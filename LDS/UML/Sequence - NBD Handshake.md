# Sequence Diagram — NBD Handshake & Request Handling

This diagram covers the full lifecycle: constructor setup, first request, and shutdown. Understanding this sequence is required for debugging NBD issues.

---

## Part 1: Constructor — Device Setup

```mermaid
sequenceDiagram
    participant App as app/LDS.cpp
    participant NBDC as NBDDriverComm
    participant K as Linux Kernel (NBD Driver)
    participant LT as Listener Thread
    participant ST as Signal Thread

    App->>NBDC: NBDDriverComm("/dev/nbd0", size)

    Note over NBDC: open("/dev/nbd0", O_RDWR) → m_nbdFd
    Note over NBDC: socketpair(AF_UNIX) → [m_serverFd, m_clientFd]

    NBDC->>K: ioctl(m_nbdFd, NBD_SET_SOCK, m_clientFd)
    Note over K: NBD driver now owns m_clientFd

    NBDC->>K: ioctl(m_nbdFd, NBD_SET_BLKSIZE, 1024)
    NBDC->>K: ioctl(m_nbdFd, NBD_SET_SIZE_BLOCKS, size/1024)
    NBDC->>K: ioctl(m_nbdFd, NBD_SET_FLAGS, SEND_FLUSH|SEND_TRIM)

    NBDC->>LT: spawn m_listener thread
    LT->>LT: sigfillset() - block ALL signals
    LT->>K: ioctl(m_nbdFd, NBD_DO_IT)
    Note over K,LT: BLOCKS HERE — kernel I/O relay is running

    NBDC->>ST: spawn m_signal_thread
    ST->>ST: sigwait({SIGINT, SIGTERM}) — sleeping

    NBDC-->>App: constructor returns
    Note over App: GetFD() returns m_serverFd for Reactor
```

---

## Part 2: Normal Request (Write)

```mermaid
sequenceDiagram
    participant User as User Process
    participant K as Kernel (NBD + VFS)
    participant LT as Listener Thread
    participant CS as m_clientFd (socket)
    participant SS as m_serverFd (socket)
    participant Reactor
    participant Handler as io_handler (LDS.cpp)
    participant LS as LocalStorage

    User->>K: write(fd, buf, 512) to /dev/nbd0
    Note over K: Encodes nbd_request struct
    K->>LT: (relay via NBD_DO_IT)
    LT->>CS: write nbd_request header (28 bytes)
    LT->>CS: write data (512 bytes for WRITE)
    Note over CS,SS: data flows through socketpair

    SS-->>Reactor: EPOLLIN fires on m_serverFd
    Reactor->>Handler: io_handler(serverFd)

    Handler->>Handler: ReceiveRequest()
    Handler->>SS: ReadAll(28 bytes) — nbd_request header
    Handler->>SS: ReadAll(512 bytes) — write data
    Handler->>Handler: decode → DriverData{WRITE, handle, offset, buffer}

    Handler->>LS: storage.Write(data)
    Note over LS: memcpy to m_storage[offset..offset+512]

    Handler->>Handler: SendReply()
    Handler->>SS: WriteAll(nbd_reply{magic, error=0, handle})

    SS-->>LT: (relay via socketpair)
    LT-->>K: reply received by kernel
    K-->>User: write() returns 512
```

---

## Part 3: Read Request

```mermaid
sequenceDiagram
    participant User
    participant K as Kernel
    participant SS as m_serverFd
    participant Handler as io_handler
    participant LS as LocalStorage

    User->>K: read(fd, buf, 512)
    K->>SS: nbd_request{type=READ, handle=H, from=4096, len=512}

    SS-->>Handler: EPOLLIN
    Handler->>SS: ReadAll(header 28 bytes)
    Note over Handler: No data to read for READ requests
    Handler->>Handler: DriverData{READ, H, offset=4096, length=512}

    Handler->>LS: storage.Read(data)
    Note over LS: copies m_storage[4096..4607] into data.m_buffer

    Handler->>SS: WriteAll(nbd_reply header 16 bytes)
    Handler->>SS: WriteAll(data.m_buffer 512 bytes)

    SS-->>K: reply with data
    K-->>User: read() returns 512, buf filled
```

---

## Part 4: Shutdown

```mermaid
sequenceDiagram
    participant User as User/Ctrl+C
    participant Reactor
    participant NBDC as NBDDriverComm
    participant K as Kernel
    participant LT as Listener Thread
    participant ST as Signal Thread

    User->>Reactor: SIGINT (via signalfd)
    Note over Reactor: signal_fd fires in epoll_wait
    Reactor->>Reactor: running = false

    Reactor->>NBDC: Disconnect()
    NBDC->>K: ioctl(m_nbdFd, NBD_DISCONNECT)
    Note over K: Sends disconnect to NBD relay

    K->>LT: NBD_DO_IT ioctl returns (unblocked)
    LT-->>LT: thread function returns

    NBDC->>LT: m_listener.join()  ← waits for thread exit

    Note over NBDC: ~NBDDriverComm destructor
    NBDC->>NBDC: close(m_serverFd)
    NBDC->>NBDC: close(m_clientFd)
    NBDC->>NBDC: close(m_nbdFd)
```

---

## Part 5: Signal Thread Conflict (Bug #7)

```mermaid
sequenceDiagram
    participant K as Kernel (signal)
    participant Reactor as Reactor (signalfd)
    participant ST as NBD Signal Thread (sigwait)

    Note over K: SIGINT raised
    K-->>Reactor: signal_fd readable (via signalfd + epoll)
    K-->>ST: sigwait() returns SIGINT

    Note over Reactor,ST: Race — who handles it first?

    alt Reactor wins
        Reactor->>Reactor: running = false
        Reactor->>Reactor: Disconnect()
        Note over ST: ST also calls Disconnect() → double-close Bug #4
    else Signal Thread wins
        ST->>ST: Disconnect()
        Note over Reactor: signal_fd may not fire if signal already consumed
    end
```

**Root cause:** Both `Reactor` (via `signalfd`) and `NBDDriverComm`'s signal thread (`sigwait`) are listening for the same signals. Linux will deliver each signal to only ONE of the two. This is a design conflict.

**Fix:** Remove `m_signal_thread` from `NBDDriverComm`. Reactor handles all signals. `Disconnect()` is called only from Reactor's `SIGINT` path. This is tracked as Bug #7.

---

## nbd_request / nbd_reply Structs (Wire Format)

```
nbd_request (kernel → userspace, 28 bytes):
  [4]  magic  = 0x25609513
  [4]  type   = 0=READ, 1=WRITE, 2=DISC, 3=FLUSH, 4=TRIM
  [8]  handle = opaque correlation ID (big-endian)
  [8]  from   = byte offset (big-endian)
  [4]  len    = data length (big-endian)
  --- followed by [len] bytes of data if type==WRITE ---

nbd_reply (userspace → kernel, 16 bytes):
  [4]  magic  = 0x67446698
  [4]  error  = 0 on success, errno on failure
  [8]  handle = copied unchanged from request
  --- followed by [len] bytes of data if replying to READ ---
```

All fields big-endian. `ReadAll`/`WriteAll` loops ensure full struct transfer despite partial socket reads.

---

## Related Notes
- [[NBD Protocol Deep Dive]]
- [[Request Lifecycle]]
- [[NBDDriverComm]]
- [[Known Bugs]]
- [[Reactor]]
