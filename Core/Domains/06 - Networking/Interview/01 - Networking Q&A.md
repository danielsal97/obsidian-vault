# Interview — Networking

Systems programming questions: sockets, epoll, TCP framing, byte ordering, UDP vs TCP.

---

## I/O Multiplexing — epoll vs select vs poll

**Q: What is I/O multiplexing? Why do you need it?**

Watch multiple file descriptors simultaneously and act only when one is ready. Without it you'd need one thread per fd, or busy-poll each one.

| Mechanism | Scale | Complexity | OS |
|---|---|---|---|
| `select` | O(n) per call, max 1024 fds | Simple | POSIX |
| `poll` | O(n) per call, no fd limit | Slightly better | POSIX |
| `epoll` | O(1) per event, no fd limit | More setup | Linux only |

**Q: How does epoll work?**

1. `epoll_create1(0)` — creates an epoll instance (returns a fd)
2. `epoll_ctl(epfd, EPOLL_CTL_ADD, fd, &event)` — register an fd
3. `epoll_wait(epfd, events, max, timeout)` — block until an fd is ready; returns only the ready ones

```cpp
int epfd = epoll_create1(0);
struct epoll_event ev;
ev.events = EPOLLIN;
ev.data.fd = target_fd;
epoll_ctl(epfd, EPOLL_CTL_ADD, target_fd, &ev);

struct epoll_event events[16];
int n = epoll_wait(epfd, events, 16, -1);   // -1 = block forever
for (int i = 0; i < n; ++i) {
    handle(events[i].data.fd);
}
```

`EPOLLET` — edge-triggered mode. Only fires once when state changes (data arrives), not on every `epoll_wait` while data is available. Requires non-blocking fds and draining the fd completely each time.

**Where is this in LDS?**  
`Reactor` is the epoll wrapper. Currently watches the NBD fd and the signalfd. Phase 2A adds TCP client fds to the same epoll instance.

---

## TCP Sockets — the API

**Q: Walk me through a TCP server setup.**

```c
// 1. Create socket
int sfd = socket(AF_INET, SOCK_STREAM, 0);

// 2. Allow port reuse after restart
int opt = 1;
setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

// 3. Bind to address + port
struct sockaddr_in addr = {0};
addr.sin_family = AF_INET;
addr.sin_addr.s_addr = INADDR_ANY;
addr.sin_port = htons(7800);
bind(sfd, (struct sockaddr*)&addr, sizeof(addr));

// 4. Listen (backlog = pending connection queue size)
listen(sfd, 5);

// 5. Accept — blocks until a client connects
struct sockaddr_in client_addr;
socklen_t len = sizeof(client_addr);
int cfd = accept(sfd, (struct sockaddr*)&client_addr, &len);

// 6. Read/write on cfd like any fd
send(cfd, buf, n, 0);
recv(cfd, buf, n, 0);
```

**Q: Walk me through a TCP client setup.**

```c
int cfd = socket(AF_INET, SOCK_STREAM, 0);
struct sockaddr_in server = {0};
server.sin_family = AF_INET;
server.sin_port = htons(7800);
inet_pton(AF_INET, "192.168.1.100", &server.sin_addr);
connect(cfd, (struct sockaddr*)&server, sizeof(server));
// connected — now send/recv
```

**Where is this in LDS?**  
Phase 2A: `TCPServer` wraps the server-side setup; `BlockClient` wraps the client-side. The listening fd is added to Reactor's epoll; `OnAccept` calls `accept()` and adds the client fd to epoll dynamically.

---

## TCP Framing — the partial-read problem

**Q: Why can't you just call `recv()` once and trust you got the full message?**

TCP is a byte stream, not a message protocol. A single `send(buf, 13)` may arrive as three `recv()` calls returning 5 + 5 + 3 bytes. You must loop until you have all the bytes you expect.

```cpp
bool RecvAll(int fd, char* buf, size_t n) {
    size_t received = 0;
    while (received < n) {
        ssize_t r = recv(fd, buf + received, n - received, 0);
        if (r <= 0) return false;   // disconnect or error
        received += r;
    }
    return true;
}
```

**LDS wire protocol header (13 bytes):**

```
[type: 1B][offset: 8B big-endian][length: 4B big-endian]
```

Receiver always calls `RecvAll(fd, header, 13)` first, then `RecvAll(fd, data, length)` for a write payload.

---

## Byte Ordering

**Q: What is network byte order? What functions convert it?**

Network byte order is big-endian. Intel x86/x64 is little-endian. When sending multi-byte integers over a socket, convert them so both sides agree.

| Function | Direction | Size |
|---|---|---|
| `htons` / `ntohs` | host ↔ network | 16-bit |
| `htonl` / `ntohl` | host ↔ network | 32-bit |
| `htobe64` / `be64toh` | host ↔ big-endian | 64-bit |

```cpp
uint64_t offset_net = htobe64(offset);    // before sending
uint64_t offset_host = be64toh(offset_net); // after receiving
```

**macOS note:** `htobe64` may require `<machine/endian.h>` or use `OSSwapHostToBigInt64(x)` as an alternative.

**Where is this in LDS?**  
`BlockClient` converts offset and length before `send()`. `TCPServer` converts back with `be64toh` / `ntohl` after `RecvAll`.

---

## UDP vs TCP

**Q: When do you use UDP instead of TCP?**

| Property | TCP | UDP |
|---|---|---|
| Reliability | Guaranteed delivery + ordering | Best-effort, no guarantees |
| Overhead | Connection setup, ACKs, flow control | Minimal |
| Use case | File transfer, HTTP, LDS client link | DNS, video stream, LDS master↔minion |

LDS uses TCP for the Mac client link (reliability matters — you can't lose a write request). LDS uses UDP for master↔minion (bounded latency matters; loss is handled by the retry scheduler).

---

## Related

→ [[../../04 - Linux/Interview/01 - Linux Q&A]]
→ [[../Mental Models/04 - epoll — The Machine]]
→ [[../Mental Models/02 - TCP Sockets — The Machine]]
→ [[../Mental Models/03 - UDP Sockets — The Machine]]
→ [[../Tradeoffs/01 - Why epoll over select and poll]]
→ [[../Tradeoffs/02 - Why UDP vs TCP]]
