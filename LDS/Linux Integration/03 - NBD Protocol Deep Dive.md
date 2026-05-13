# NBD Protocol Deep Dive

This is the most Linux-specific part of the project. Understanding it deeply is what makes this project stand out in interviews.

---

## What is NBD?

NBD (Network Block Device) is a **Linux kernel subsystem** that lets userspace programs appear as block devices (`/dev/nbd0`, `/dev/nbd1`, etc.).

```
┌─────────────────────────────────────────────────┐
│               Linux Kernel                       │
│                                                  │
│  VFS → Block Layer → NBD Driver                  │
│                           │                      │
│                    socketpair (AF_UNIX)           │
│                           │                      │
└───────────────────────────┼──────────────────────┘
                            │
              ┌─────────────▼──────────┐
              │    NBDDriverComm       │
              │    (our process)       │
              │                        │
              │  ReceiveRequest()      │
              │  SendReply()           │
              └────────────────────────┘
```

From the user's perspective: `/dev/nbd0` is a real disk. `cp file /mnt/nbd` works. `mkfs.ext4 /dev/nbd0` works. The NBD driver transparently forwards all I/O to us.

---

## Setup Sequence — What `NBDDriverComm` Constructor Does

```cpp
NBDDriverComm::NBDDriverComm(const std::string& device, size_t size) {
    // 1. Open the NBD device
    m_nbdFd = open(device.c_str(), O_RDWR);  // opens /dev/nbd0

    // 2. Create a socket pair (kernel talks to us through this)
    int sv[2];
    socketpair(AF_UNIX, SOCK_STREAM, 0, sv);
    m_serverFd = sv[0];  // our end
    m_clientFd = sv[1];  // kernel's end

    // 3. Tell NBD kernel driver which socket to use
    ioctl(m_nbdFd, NBD_SET_SOCK, m_clientFd);

    // 4. Configure block device geometry
    ioctl(m_nbdFd, NBD_SET_BLKSIZE, 1024);
    ioctl(m_nbdFd, NBD_SET_SIZE_BLOCKS, size / 1024);
    ioctl(m_nbdFd, NBD_SET_FLAGS, NBD_FLAG_SEND_FLUSH | NBD_FLAG_SEND_TRIM);

    // 5. Start listener thread BEFORE NBD_DO_IT
    m_listener = std::thread([this]{ ListenerThread(); });

    // 6. Start signal thread for clean shutdown
    SetUpSignals();
}
```

---

## The Listener Thread — `ioctl(NBD_DO_IT)`

```cpp
void NBDDriverComm::ListenerThread() {
    // Block ALL signals in this thread
    // Any signal would interrupt ioctl() with EINTR, breaking the relay loop
    sigset_t mask;
    sigfillset(&mask);
    pthread_sigmask(SIG_BLOCK, &mask, nullptr);

    // THIS CALL NEVER RETURNS until NBD_DISCONNECT or Disconnect()
    // It tells the kernel: "start forwarding I/O over the socket"
    // The kernel now uses m_clientFd for all block device I/O
    ioctl(m_nbdFd, NBD_DO_IT);
    // returns here only on shutdown
}
```

**Why a dedicated thread?** `ioctl(NBD_DO_IT)` is a blocking kernel call that **never returns** until the device is disconnected. It cannot be on the main thread or any thread you want to use for other work.

**Why `sigfillset`?** Any signal arriving while `ioctl` is executing causes `EINTR` (interrupted system call). The kernel relay loop would break. All signals must be blocked in this thread.

---

## Request/Reply Binary Format

The kernel sends `nbd_request` structs and expects `nbd_reply` structs back. These are defined in `<linux/nbd.h>`:

```c
// Kernel → Userspace
struct nbd_request {
    uint32_t  magic;        // NBD_REQUEST_MAGIC = 0x25609513
    uint32_t  type;         // NBD_CMD_READ=0, NBD_CMD_WRITE=1, ...
    uint64_t  handle;       // opaque cookie — copied unchanged to reply
    uint64_t  from;         // byte offset
    uint32_t  len;          // data length in bytes
};  // followed by 'len' bytes of data if type == WRITE

// Userspace → Kernel
struct nbd_reply {
    uint32_t  magic;        // NBD_REPLY_MAGIC = 0x67446698
    uint32_t  error;        // 0 = success, errno on failure
    uint64_t  handle;       // MUST match the request's handle exactly
};  // followed by 'len' bytes of data if replying to a READ
```

**All multi-byte fields are big-endian.** Must use `ntohl()` / `htonl()` etc. when decoding.

---

## `DriverData` — Our Internal Format

After decoding the binary protocol, `ReceiveRequest()` produces a `DriverData`:

```cpp
struct DriverData {
    enum ActionType { READ, WRITE, DISCONNECT, FLUSH, TRIM };
    enum StatusType { SUCCESS, FAILURE };

    ActionType     m_type;    // decoded from nbd_request.type
    size_t         m_handle;  // opaque: nbd_request.handle (unchanged)
    size_t         m_offset;  // nbd_request.from
    size_t         m_len;     // nbd_request.len  ← Bug #2: never initialized in ctor
    StatusType     m_status;
    std::vector<char> m_buffer;  // contains data for WRITE; filled by READ
};
```

`m_handle` is the kernel's **request correlator**. The kernel sends async requests; it matches replies by `handle`. We must echo it back unchanged in `SendReply()`.

---

## `ReadAll` / `WriteAll` — Why Loops?

Sockets can deliver **partial data**. A single `read()` may return fewer bytes than requested:

```cpp
void NBDDriverComm::ReadAll(int fd, void* buf, size_t count) {
    char* ptr = static_cast<char*>(buf);
    while (count > 0) {
        ssize_t n = read(fd, ptr, count);
        if (n <= 0) throw NBDDriverError("read failed");
        ptr += n;
        count -= n;
    }
}
```

A `read()` of 512 bytes might return 256. Without the loop, the second half of the struct is left in the kernel buffer and the next `ReceiveRequest()` reads a corrupted struct. This is a classic socket programming bug.

---

## `GetFD()` — Why the Server FD?

```cpp
int NBDDriverComm::GetFD() { return m_serverFd; }
```

`m_serverFd` is our end of the socketpair. The Reactor watches it with `epoll(EPOLLIN)`. When the kernel writes an `nbd_request` to `m_clientFd`, data arrives on `m_serverFd` — epoll fires — Reactor calls the handler — we call `ReceiveRequest()` which reads from `m_serverFd`.

```
Kernel writes to m_clientFd → data appears on m_serverFd
Reactor's epoll sees EPOLLIN on m_serverFd → fires handler
Handler calls driver.ReceiveRequest() → reads nbd_request from m_serverFd
```

---

## Shutdown Sequence

```
1. User presses Ctrl+C
2. SIGINT delivered to process
3. Reactor's signalfd fires → Reactor::Run() sets running = false
4. Reactor calls driver.Disconnect()
5. Disconnect() calls ioctl(m_nbdFd, NBD_DISCONNECT)
6. Kernel receives disconnect → wakes up the ListenerThread's ioctl(NBD_DO_IT)
7. ListenerThread returns and m_listener.join() completes
8. NBDDriverComm destructor closes all fds
```

**Current Bug #4 (Disconnect race):** `Disconnect()` is called from the Reactor AND potentially from `m_signal_thread` simultaneously. Both call `close(m_nbdFd)`. A double-close is undefined behavior if the fd was reused. Fix: use `std::once_flag` to ensure Disconnect runs exactly once.

---

## NBD Command Types

| NBD Command | Value | Mapped to DriverData |
|---|---|---|
| `NBD_CMD_READ` | 0 | `ActionType::READ` |
| `NBD_CMD_WRITE` | 1 | `ActionType::WRITE` |
| `NBD_CMD_DISC` | 2 | `ActionType::DISCONNECT` |
| `NBD_CMD_FLUSH` | 3 | `ActionType::FLUSH` |
| `NBD_CMD_TRIM` | 4 | `ActionType::TRIM` |

FLUSH and TRIM are sent by the filesystem. LDS currently handles them as no-ops (returns SUCCESS without writing anything).

---

## Key Interview Questions About NBD

**Q: What is a userspace block device?**
> `/dev/nbd0` looks like a real disk to the kernel. All I/O (read, write, flush) is forwarded to our process over a socket pair. We respond with data and the kernel treats it as if the disk answered.

**Q: Why `socketpair(AF_UNIX)` not a TCP socket?**
> The `NBD_SET_SOCK` ioctl requires a socket (not a pipe). AF_UNIX is bidirectional, local (no TCP stack overhead), and zero-copy within the same machine.

**Q: What does `ioctl(NBD_DO_IT)` do?**
> Tells the kernel to begin forwarding I/O over the socket. It's a blocking call — the kernel uses this thread to run the I/O relay loop. Returns only on `NBD_DISCONNECT`.

**Q: Why block ALL signals in the listener thread?**
> Any signal (SIGINT, SIGHUP, even SIGUSR1) interrupts `ioctl(NBD_DO_IT)` with `EINTR`, breaking the relay. The kernel would stop forwarding I/O. Must block all signals so only Reactor's `signalfd` path handles shutdown.

**Q: What is `m_handle` and why copy it unchanged?**
> An opaque 64-bit token the kernel generates per-request. The kernel matches our reply to the original request by this handle. If we change it, the kernel will get confused or hang waiting for a reply that never arrives.

---

## Related Notes
- [[NBD Layer]]
- [[NBDDriverComm]]
- [[Known Bugs]]
- [[Why signalfd not sigaction]]
- [[Sequence - NBD Handshake]]
