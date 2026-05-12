# LDS Request Lifecycle — The Machine

## The Model
One WRITE request's journey from userspace through the kernel and back. Follow a single package: an application calls `write("/dev/nbd0", buf, 512)`. The package enters the kernel, crosses into LDS, gets decoded, prioritized, executed in a worker thread, stored in memory, and an acknowledgment travels back to the kernel, unblocking the application. Every component in LDS is touched. The Reactor never waits. The main thread never stores data. The worker thread never reads from a socket.

## How It Moves

```
① Application:
  write(fd, buf, 512)   ← userspace write to /dev/nbd0 block device
  [BLOCKS HERE — application is suspended until NBD replies]

② Kernel NBD driver:
  Receives write() → formats 28-byte NBD request header:
    magic=0x25609513, type=WRITE(1), handle=<cookie>, offset=0, len=512
  Followed by 512 bytes of data payload
  Writes all 540 bytes to m_serverFd (socketpair kernel end)
  m_clientFd becomes readable → epoll_wait returns in LDS main thread

③ Reactor (main thread):
  n = epoll_wait(m_epoll_fd, events, 10, -1)   ← was sleeping, now wakes
  event.fd == m_clientFd (driver fd, not signal fd)
  calls m_io_handler(m_clientFd)
    → mediator.Notify(m_clientFd)

④ InputMediator::Notify(fd):
  (void)fd   ← fd ignored, single driver
  request = m_driver->ReceiveRequest()
    → NBDDriverComm::ReceiveRequest():
        ReadAll(m_clientFd, &header, 28)   ← reads 28-byte header from socket
        parse: type=WRITE, handle=cookie, offset=0, len=512
        ReadAll(m_clientFd, buffer.data(), 512)   ← reads 512-byte payload
        return make_shared<DriverData>(WRITE, handle=cookie, offset=0, buffer=[512 bytes])
  
  m_handlers.at(DriverData::WRITE)(request)
    → executes the WRITE lambda immediately (Phase 1 — synchronous):
        m_storage->Write(request)     ← stores data
        m_driver->SendReply(request)  ← sends ACK
  
  returns to Reactor event loop   ← main thread ready for next event

⑤ LocalStorage::Write(request):
  lock_guard lock(m_lock)   ← acquires mutex
  bounds check: 0 + 512 <= storage_size   ← OK
  copy(buffer.begin(), buffer.end(), m_storage.begin() + 0)
    ← 512 bytes copied into m_storage vector at offset 0
  m_offset_sizes[0] = 512   ← ledger entry
  lock released (scope exit)

⑥ NBDDriverComm::SendReply(request):
  WriteAll(m_clientFd, &reply_header, 16)
    ← reply header: magic=0x67446698, error=0, handle=<same cookie>
  ← no payload for WRITE reply (data goes only from kernel TO LDS, not back)
  
  kernel NBD driver reads reply from m_serverFd
  matches handle=cookie to the pending write() call
  unblocks the application

⑦ Application:
  write() returns 512   ← control returns to userspace
  [was blocked since step ①, now free]
```

**Timeline — who waits for what:**
```
Application:  [=== write() blocked =============================] → returns
Kernel NBD:   [send request] [==== waiting for reply ============]
Reactor:      [sleep] [wake] [Notify] [back to epoll sleep]
LocalStorage: [=== Write() mutex + memcpy ===]
NBDDriverComm:               [ReadAll header][ReadAll payload]   [WriteAll reply]
```

**Phase 2 difference — the ThreadPool path:**
In Phase 2, `InputMediator`'s WRITE handler doesn't execute synchronously. Instead:
```
m_handlers[WRITE] = [this, pool](data) {
    pool->AddCommand(make_shared<WriteCommand>(data, m_storage, m_driver));
    ← returns immediately — main thread goes back to epoll
};

Worker thread later:
    WriteCommand::Execute():
        m_storage->Write(data)   ← RAID01Manager: sendto() × 2 minions, wait ACKs
        m_driver->SendReply(data)
```
The Reactor handles many more events while the worker waits for minion ACKs.

## The Full Cast

| Component | File | Role in WRITE |
|---|---|---|
| `NBDDriverComm` | `nbd/NBDDriverComm.hpp` | Decode 28+512 bytes from socket into DriverData |
| `Reactor` | `reactor/reactor.hpp` | Detect readable fd, dispatch to Notify |
| `InputMediator` | `mediator/InputMediator.hpp` | Look up WRITE handler, call it |
| `LocalStorage` | `local_storage/LocalStorage.hpp` | Lock, bounds-check, memcpy, unlock |
| `NBDDriverComm` | (same) | Encode 16-byte reply, write to socket |
| `Kernel NBD` | (kernel) | Match handle, unblock application |

## Where It Breaks (End-to-End)

- **Reactor slow path**: if `m_storage->Write()` takes 50ms (Phase 2 + minion network), the Reactor is stuck in `Notify()` for 50ms. A second WRITE arriving during that window sits unread in `m_clientFd`'s kernel buffer. The kernel application `write()` call is also still blocked. Backpressure builds until the kernel buffer fills → application `write()` blocks at the kernel socket level.
- **Handle mismatch**: `SendReply` must echo back the exact `handle` from `ReceiveRequest()`. If the handle is wrong, the kernel NBD driver won't match it to the pending `write()` call → the application hangs forever.
- **Out-of-order replies**: NBD protocol supports multiple in-flight requests if each has a unique handle. LDS's current Phase 1 processes one request at a time (single-threaded Notify). Phase 2 with ThreadPool can process multiple requests concurrently — replies must carry the correct handle or the kernel will deliver data to the wrong application call.

## Validate

1. The application calls `write("/dev/nbd0", buf, 4096)`. Walk through every `ReadAll` call in `ReceiveRequest()` — how many bytes does each read, and what do they contain?
2. Between step ③ (Reactor wakes) and step ⑦ (application unblocks), can the Reactor process a second request? In Phase 1, when does the main thread become free to handle a second epoll event?
3. `ReceiveRequest()` reads the 28-byte header and sees `type=DISCONNECT`. Trace what happens through `InputMediator::Notify()` and the DISCONNECT handler lambda. Does `SendReply()` get called? Does the Reactor keep running?
