# LDS TCPDriverComm — The Machine

## The Model
A customer service desk that replaced the internal factory intercom. Instead of the kernel connecting directly through `NBD_DO_IT`, any TCP client connects over the network and speaks the same language as the kernel NBD format — only now it's a real TCP socket. The desk has a waiting room (`m_listen_fd`) that accepts one customer at a time (`m_client_fd`). The same `ReceiveRequest()` / `SendReply()` interface exists — the `InputMediator` behind the desk doesn't know or care that this is TCP instead of a kernel socketpair.

## How It Moves

```
Construction — TCPDriverComm(port_):
  m_listen_fd = socket(AF_INET, SOCK_STREAM, 0)
  setsockopt(m_listen_fd, SO_REUSEADDR)   ← don't fail on restart with TIME_WAIT
  bind(m_listen_fd, port_)
  listen(m_listen_fd, backlog)
  m_client_fd = accept(m_listen_fd, ...)  ← BLOCKS until first client connects
                                          ← construction doesn't return until connected!

GetFD():
  return m_client_fd   ← Reactor monitors the CONNECTED client socket
                       ← m_client_fd is already set (constructor blocked on accept())
                       ← m_listen_fd only fires on NEW connections — never again after the first

ReceiveRequest():
  ReadAll(m_client_fd, &header, sizeof(RequestHeader))
  parse: type | handle | offset | len
  if WRITE: ReadAll(m_client_fd, buffer.data(), len)
  return make_shared<DriverData>(type, handle, offset, buffer)

SendReplay(data_):     ← Note: "Replay" not "Reply" — interface quirk
  WriteAll(m_client_fd, &reply_header, sizeof(ReplyHeader))
  if READ: WriteAll(m_client_fd, buffer.data(), len)

m_allocations map:
  UpdateAllocation(offset, data)  ← tracks what was written at each offset
  GetAllocation(offset)           ← retrieves stored data for READ
  used only by TCPDriverComm for GET_SIZE protocol support
```

**No dedicated listener thread (unlike NBD):**
NBDDriverComm needs a background thread to run the blocking `ioctl(NBD_DO_IT)` kernel loop. TCPDriverComm is pure userspace — `read()` and `write()` on a socket are non-blocking-compatible. No `NBD_DO_IT` equivalent. The only potential block is the `accept()` call in the constructor.

**Custom binary protocol:**
TCPDriverComm's wire protocol mirrors the NBD wire format but runs over a normal TCP connection. The `m_allocations` map (`map<size_t, vector<char>>`) tracks writes by offset — this lets `GET_SIZE` reply correctly (telling the client how many bytes are stored at a given offset), since TCP clients may issue `GET_SIZE` queries that the kernel NBD driver normally handles internally.

**`m_alloc_lock` mutex:**
`m_allocations` is protected by `m_alloc_lock` — `UpdateAllocation` and `GetAllocation` both lock it. This matters when multiple worker threads may call `GetAllocation` while the main thread's handler is calling `UpdateAllocation`. In practice, the current implementation has a single `m_client_fd` and the Reactor is single-threaded, but the map is still protected defensively.

## The Blueprint

```cpp
// tcp/include/TCPDriverComm.hpp:
class TCPDriverComm : public IDriverComm {
    int m_listen_fd;    // bound+listening socket — used only in constructor for accept()
    int m_client_fd;    // accepted connection — Reactor watches this; data flows here

    std::map<size_t, std::vector<char>> m_allocations;  // TCP-only
    mutable std::mutex m_alloc_lock;

    void ReadAll(int fd, void* buf, size_t count);
    void WriteAll(int fd, const void* buf, size_t count);
    void UpdateAllocation(size_t offset, const std::vector<char>& data);
    std::vector<char> GetAllocation(size_t offset) const;
public:
    explicit TCPDriverComm(int port_);
    std::shared_ptr<DriverData> ReceiveRequest() override;
    void SendReplay(std::shared_ptr<DriverData> data_) override;   // not SendReply!
    int GetFD() override;
    ~TCPDriverComm() override;
};
```

**`SendReplay` vs `SendReply`:**
The `IDriverComm` interface has `SendReplay` (a typo that became the API). `NBDDriverComm` implements `SendReply` (correct spelling) and `TCPDriverComm` implements `SendReplay`. This asymmetry is a real design inconsistency in LDS's current codebase — `InputMediator::SetupHandlers()` calls `m_driver->SendReplay(request)` for GET_SIZE and `m_driver->SendReply(request)` for READ/WRITE. Both methods exist on `IDriverComm`.

## Where It Breaks

- **`accept()` blocks in constructor**: If no client connects, `TCPDriverComm` construction never returns. Main thread stalls. Fix: make `accept()` non-blocking or move it out of the constructor.
- **Single client only**: `accept()` is called once, storing one `m_client_fd`. If that client disconnects, `ReadAll` returns 0 (EOF) → exception. There's no reconnect logic — a new `TCPDriverComm` would need to be created.
- **No TLS**: Data (including writes) flows in plaintext over TCP. If LDS is used over a real network (Phase 2), all storage content is visible on the wire.
- **`m_allocations` grows unbounded**: every offset written by a TCP client is stored in the map forever. For a large storage space with writes scattered across offsets, this becomes a memory leak analogue.

## In LDS

`services/communication_protocols/tcp/include/TCPDriverComm.hpp`

Phase 1 alternative driver for testing without the kernel NBD device. Use when `/dev/nbd0` isn't available (CI, non-root testing, macOS):

```cpp
// Instead of:
NBDDriverComm driver("/dev/nbd0", storageSize);
// Use:
TCPDriverComm driver(7800);   // listens on port 7800

// Rest of main() is identical:
InputMediator mediator(&driver, &storage);
reactor.Add(driver.GetFD());
reactor.SetHandler([&mediator](int fd){ mediator.Notify(fd); });
reactor.Run();
```

The TCP client (Mac-side bridge in Phase 2A) connects to port 7800 and sends the same binary protocol that the kernel NBD driver would send over the socketpair. `InputMediator` sees no difference.

## Validate

1. A TCP client connects and sends a WRITE of 512 bytes at offset 1024. Trace: which bytes hit `m_listen_fd`, which hit `m_client_fd`, and what goes into `m_allocations`.
2. `GetFD()` returns `m_client_fd`. The Reactor adds this to epoll. When does `m_client_fd` become readable — on a new connection arriving, or on data arriving from the existing connection? What would break if `m_listen_fd` were returned instead?
3. `NBDDriverComm::SendReply()` and `TCPDriverComm::SendReplay()` have different spellings. If `InputMediator` calls `m_driver->SendReply(request)` for a WRITE, and `m_driver` is `TCPDriverComm*`, what happens at runtime? Check the virtual table lookup path.
