# TCPServer

**Phase:** 2A | **Status:** ❌ Not built  
**Location:** `services/network/include/TCPServer.hpp` + `src/TCPServer.cpp`

---

## What It Does

TCPServer is the Linux-side network endpoint for the client-server link. It:

1. Binds a TCP socket and listens for incoming connections
2. When a client connects, adds the client socket to the existing Reactor (not a new thread)
3. When data arrives from a client, parses the `NetworkProtocol` request
4. Calls `IStorage::Read` or `IStorage::Write` on the existing `LocalStorage`
5. Sends a `NetworkProtocol` response back over the same socket

It is entirely event-driven — no blocking I/O, no dedicated TCP thread. The Reactor's epoll loop handles everything.

---

## Interface

```cpp
class TCPServer {
public:
    TCPServer(int port, Reactor& reactor, IStorage& storage);
    ~TCPServer();                    // closes listen socket + all client sockets

    int GetListenFD() const;         // register this with Reactor in LDS.cpp

    TCPServer(const TCPServer&) = delete;
    TCPServer& operator=(const TCPServer&) = delete;

private:
    void OnAccept(int listen_fd);    // called by Reactor when client connects
    void OnClientData(int fd);       // called by Reactor when client sends data
    void CloseClient(int fd);        // Remove from reactor + close + erase from map

    bool RecvAll(int fd, void* buf, size_t n);
    bool SendAll(int fd, const void* buf, size_t n);

    int m_listen_fd;
    Reactor& m_reactor;
    IStorage& m_storage;
    std::unordered_map<int, bool> m_clients;  // active client fds
};
```

---

## How It Plugs Into LDS.cpp

```cpp
// In app/LDS.cpp, after the Reactor upgrade:
LocalStorage storage(size);
NBDDriverComm driver(device, size);
TCPServer tcp_server(7800, reactor, storage);
InputMediator mediator(&driver, &storage);
Reactor reactor;

reactor.Add(driver.GetFD(),             [&](int fd){ mediator.Notify(fd); });
reactor.Add(tcp_server.GetListenFD(),   [&](int fd){ tcp_server.OnAccept(fd); });
reactor.Run();
```

The single Reactor loop now handles NBD events and TCP client events from the same `epoll_wait()` call.

---

## Key Implementation Notes

**`RecvAll` is mandatory.**
TCP is a stream. A single `send()` of 100 bytes may arrive as two `recv()` calls of 60 and 40 bytes. `RecvAll` loops until all N bytes are received:

```cpp
bool TCPServer::RecvAll(int fd, void* buf, size_t n) {
    size_t received = 0;
    while (received < n) {
        ssize_t r = recv(fd, (char*)buf + received, n - received, 0);
        if (r <= 0) return false;  // connection closed or error
        received += r;
    }
    return true;
}
```

**Client disconnect handling.**
If `RecvAll` returns false (client disconnected or error), call `CloseClient(fd)`:
```cpp
reactor.Remove(fd);
close(fd);
m_clients.erase(fd);
```
Without this, the fd leaks and the epoll set grows unboundedly.

**`OnAccept` adds each client dynamically.**
```cpp
void TCPServer::OnAccept(int listen_fd) {
    int client_fd = accept(listen_fd, nullptr, nullptr);
    m_clients[client_fd] = true;
    m_reactor.Add(client_fd, [this, client_fd](int fd){ OnClientData(fd); });
}
```

**Byte order on receive.**
All multi-byte integers arrive in big-endian. Convert immediately after `RecvAll`:
```cpp
ClientRequest req;
RecvAll(fd, &req, sizeof(req));
uint64_t offset = be64toh(req.offset);
uint32_t length = ntohl(req.length);
```

---

## Design Pattern: Reactor + TCPServer

```
epoll_wait() fires on listen_fd
    → OnAccept()
        → accept() → client_fd
        → reactor.Add(client_fd, handler)   ← dynamic registration

epoll_wait() fires on client_fd
    → OnClientData(client_fd)
        → RecvAll(header) → RecvAll(data)
        → storage.Read/Write(...)
        → SendAll(response)
```

This is the Reactor pattern: events drive dispatch, no thread blocks waiting for a single fd.

---

## Port

Default: **7800**. Configurable as a constructor argument.

Port 7800 is above 1024 (no root required). Does not conflict with the minion UDP ports (7700, 7701, 7702) defined in the Wire Protocol Spec.

---

## Learning Resources

To implement this yourself:

- **Beej's Guide to Network Programming** — free online, covers everything: socket/bind/listen/accept/recv loop/byte ordering
- `man 2 accept` / `man 2 recv` / `man 7 tcp` — Linux man pages
- Search terms: `socket bind listen accept C++`, `TCP partial read recv loop`, `htons htonl htobe64`, `epoll_ctl EPOLLIN non-blocking accept`

## Similarity to NBDDriverComm

| | NBDDriverComm | TCPServer |
|---|---|---|
| Setup | `socketpair` + `ioctl` | `socket/bind/listen` |
| FD registered with Reactor | one fixed fd | listen fd + dynamic client fds |
| Reactor fires | read nbd_request | `accept()` → add client_fd |
| Data | already connected | `RecvAll(header)` → `RecvAll(data)` |
| Reply | `SendReply(DriverData)` | `send(response)` |
| Cleanup | close socketpair | `close(client_fd)` + remove from Reactor |

Key difference: NBDDriverComm has one fixed fd. TCPServer spawns a new fd per client, each registered dynamically into the Reactor.

---

## Related Notes

- [[Architecture/Client-Server Architecture]]
- [[Phase 2A - Mac Client TCP Bridge]]
- [[Reactor]]
- [[LocalStorage]]
- [[Components/BlockClient]] — the Mac-side counterpart
