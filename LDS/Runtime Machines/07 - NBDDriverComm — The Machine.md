# LDS NBDDriverComm — The Machine

## The Model
A translator booth between the Linux kernel's block device language and LDS's internal language. The kernel speaks NBD wire protocol: fixed 28-byte request headers over a socket. LDS speaks `DriverData` structs. The booth (`NBDDriverComm`) sits in the middle: one socket end goes into the kernel (`m_nbdFd` with `ioctl(NBD_DO_IT)`), the other end is a pipe into LDS (`m_serverFd`/`m_clientFd` socketpair). A dedicated background thread runs the kernel's NBD loop. The main thread reads parsed requests from the LDS side.

## How It Moves

```
Construction — NBDDriverComm(deviceName, storageSize):
  socketpair(AF_UNIX, SOCK_STREAM, 0, [m_serverFd, m_clientFd])
    ← creates bidirectional pipe between kernel NBD and LDS
  
  m_nbdFd = open(deviceName, O_RDWR)   ← "/dev/nbd0"
  ioctl(m_nbdFd, NBD_SET_SIZE, storageSize)
  ioctl(m_nbdFd, NBD_SET_SOCK, m_serverFd)  ← give kernel the server end
  
  m_listener = thread([this]{ ListenerThread(); })
    ← background thread runs NBD kernel loop

ListenerThread():
  ioctl(m_nbdFd, NBD_DO_IT)   ← BLOCKS HERE — kernel owns this thread
                               ← kernel reads/writes on m_serverFd socket
                               ← returns only when disconnected or error

GetFD():
  return m_clientFd   ← THIS is what the Reactor monitors with epoll
                      ← when kernel sends a request, m_clientFd becomes readable

ReceiveRequest():
  ReadAll(m_clientFd, &header, 28)   ← NBD wire format: magic+type+handle+offset+len
  parse header → DriverData{type, handle, offset, buffer}
  if WRITE: ReadAll(m_clientFd, buffer.data(), len)  ← read the payload too
  return make_shared<DriverData>(...)

SendReply(data_):
  WriteAll(m_clientFd, &reply_header, 16)  ← NBD reply: magic+error+handle
  if READ: WriteAll(m_clientFd, buffer.data(), len)  ← send data back

ReadAll(fd, buf, count):
  bytes_read = 0
  while bytes_read < count:
    n = read(fd, buf + bytes_read, count - bytes_read)
    if n <= 0: throw NBDDriverError(...)
    bytes_read += n
  ← guarantees exactly count bytes — handles partial reads from the socket
```

**The socketpair trick:**
`socketpair()` creates two connected file descriptors sharing a bidirectional byte stream. The kernel NBD driver is given `m_serverFd` via `ioctl(NBD_SET_SOCK)` — it writes requests there and reads replies. LDS reads requests from `m_clientFd` and writes replies back. The Reactor monitors `m_clientFd` with epoll — it becomes readable when the kernel places a new request on the wire.

**Why a dedicated listener thread:**
`ioctl(NBD_DO_IT)` never returns while the device is active — it blocks the calling thread, running the kernel's NBD event loop. If called on the main thread, the Reactor could never run. The listener thread sacrifices itself to this blocking ioctl, freeing the main thread for epoll.

**NBD wire format (28-byte request header):**
```
[4 bytes] magic     = 0x25609513
[4 bytes] type      = 0 (READ), 1 (WRITE), 2 (DISCONNECT), 3 (FLUSH), 4 (TRIM)
[8 bytes] handle    = opaque cookie, echo'd back in reply
[8 bytes] offset    = byte offset into the block device
[4 bytes] length    = number of bytes
```

## The Blueprint

```cpp
// nbd/include/NBDDriverComm.hpp:
class NBDDriverComm : public IDriverComm {
    int m_nbdFd;      // /dev/nbd0 — ioctl target
    int m_serverFd;   // kernel NBD side of socketpair
    int m_clientFd;   // LDS side of socketpair — Reactor monitors this

    std::thread m_listener;   // runs ioctl(NBD_DO_IT)
    
    void ListenerThread();
    void ReadAll(int fd, void* buf, size_t count);
    void WriteAll(int fd, const void* buf, size_t count);
public:
    explicit NBDDriverComm(const std::string& deviceName_, size_t storage_size);
    std::shared_ptr<DriverData> ReceiveRequest() override;
    void SendReply(std::shared_ptr<DriverData> data_) override;
    int GetFD() override;   // returns m_clientFd
    ~NBDDriverComm() override;
};
```

**`ReadAll`/`WriteAll` loop — why not just `read()`:**
TCP and Unix domain sockets can return short reads — `read()` may return fewer bytes than requested if the kernel buffer is partially full. A single `read()` for a 4KB block might return 1KB, 2KB, then 1KB in three calls. `ReadAll` loops until exactly `count` bytes are read, making the protocol framing reliable.

## Where It Breaks

- **`NBD_DO_IT` race**: if `~NBDDriverComm` is called before `ListenerThread` is joined, the thread accesses `m_nbdFd` after it's been closed → crash. Destructor must `ioctl(m_nbdFd, NBD_DISCONNECT)` first to unblock `NBD_DO_IT`, then `join()` the listener.
- **`ReadAll` partial read then connection drop**: if the socket closes mid-read (client disconnect), `read()` returns 0 (EOF). `ReadAll` throws `NBDDriverError`. This propagates through `ReceiveRequest()` → `Notify()` → Reactor. Reactor dies unless caught.
- **Only one fd exposed**: `GetFD()` returns `m_clientFd`. The Reactor adds exactly this fd to epoll. When the kernel sends a request, only `m_clientFd` becomes readable — there is no second fd to monitor.
- **No concurrent `ReceiveRequest()`**: `ReceiveRequest()` is not thread-safe — it reads sequentially from `m_clientFd`. Only one caller (the main thread via Reactor) should call it. If two threads called it simultaneously, the header bytes would be split between them.

## In LDS

`services/communication_protocols/nbd/include/NBDDriverComm.hpp`

Phase 1 production driver. Wired in `main()`:
```cpp
NBDDriverComm driver("/dev/nbd0", storageSize);
reactor.Add(driver.GetFD());   // m_clientFd → epoll
reactor.SetHandler([&mediator](int fd){ mediator.Notify(fd); });
```

When the kernel does `write("/dev/nbd0", buf, 512)`, the bytes travel: kernel → NBD kernel driver → `m_serverFd` → `m_clientFd`. Epoll fires on `m_clientFd`. Reactor calls `Notify()`. Mediator calls `ReceiveRequest()` to pull the 28-byte header and payload off the socket.

In testing/Phase 1 development, `TCPDriverComm` can replace `NBDDriverComm` without changing `InputMediator` or the `Reactor` — they only see `IDriverComm*`.

## Validate

1. The kernel issues a WRITE of 4096 bytes to offset 0. Walk through the exact bytes that appear on `m_serverFd` (header + payload). What does `ReadAll` in `ReceiveRequest()` do with them?
2. `ReadAll` is called with `count=28`. `read()` returns 10 bytes on the first call. What happens next? What would happen if `ReadAll` wasn't there and you called `read()` once?
3. `~NBDDriverComm` is called while `ListenerThread` is inside `ioctl(NBD_DO_IT)`. Without any shutdown protocol, what happens to `m_listener.join()`? What must happen before `join()` to make this safe?

---

## Core Vault Cross-Links

→ [[02 - File Descriptors — The Machine]] — what an fd is at the kernel level
→ [[Linux Runtime — The Machine]] — how the kernel's VFS layer handles this socketpair
