# epoll — I/O Multiplexing

epoll lets a single thread watch many file descriptors simultaneously and act only when one is ready. The foundation of the Reactor pattern.

---

## The Problem epoll Solves

Without I/O multiplexing, you either:
1. Block on a single fd — can't watch others simultaneously
2. Use one thread per fd — doesn't scale (10k clients = 10k threads)
3. Non-blocking poll in a loop — burns CPU constantly checking

epoll solves this: sleep until at least one fd is ready, then return only the ready ones. Zero CPU when idle.

---

## select vs poll vs epoll

| | select | poll | epoll |
|---|---|---|---|
| Max fds | 1024 (FD_SETSIZE) | Unlimited | Unlimited |
| Time per call | O(n) scan of all fds | O(n) scan | O(1) — only ready fds returned |
| Fd registration | Rebuild set every call | Rebuild array every call | Register once with epoll_ctl |
| OS | POSIX | POSIX | Linux only |

With 10,000 fds and 10 active, `select`/`poll` scan all 10,000 each call. `epoll` returns only the 10 active ones — the kernel maintains a ready list.

---

## The Three Calls

### 1. epoll_create1 — create epoll instance

```c
int epfd = epoll_create1(0);              // returns epoll fd
int epfd = epoll_create1(EPOLL_CLOEXEC);  // close on exec (good practice)
```

`epfd` is a file descriptor. Close it with `close(epfd)` when done.

---

### 2. epoll_ctl — register / modify / remove fds

```c
struct epoll_event ev;
ev.events = EPOLLIN;    // watch for readability
ev.data.fd = target_fd; // or ev.data.ptr for custom pointer

// Add:
epoll_ctl(epfd, EPOLL_CTL_ADD, target_fd, &ev);

// Modify:
ev.events = EPOLLIN | EPOLLOUT;
epoll_ctl(epfd, EPOLL_CTL_MOD, target_fd, &ev);

// Remove:
epoll_ctl(epfd, EPOLL_CTL_DEL, target_fd, NULL);
```

---

### 3. epoll_wait — block until ready

```c
struct epoll_event events[MAX_EVENTS];
int n = epoll_wait(epfd, events, MAX_EVENTS, timeout_ms);
// timeout_ms: -1 = block forever, 0 = return immediately, >0 = ms timeout

for (int i = 0; i < n; i++) {
    int fd = events[i].data.fd;
    if (events[i].events & EPOLLIN) {
        handle_read(fd);
    }
    if (events[i].events & EPOLLOUT) {
        handle_write(fd);
    }
    if (events[i].events & (EPOLLERR | EPOLLHUP)) {
        handle_error(fd);
    }
}
```

Returns the number of ready fds. Only the ready fds are in `events[]`.

---

## Event Types

| Event | Meaning |
|---|---|
| `EPOLLIN` | Data available to read, or new connection on listen fd |
| `EPOLLOUT` | Buffer has space — can write without blocking |
| `EPOLLRDHUP` | Peer closed connection (remote half-close) |
| `EPOLLERR` | Error on fd (always monitored even if not requested) |
| `EPOLLHUP` | Hang up — always monitored |
| `EPOLLET` | Edge-triggered mode |
| `EPOLLONESHOT` | Fire once then disable |

---

## Level-Triggered vs Edge-Triggered

**Level-triggered (default):** epoll_wait fires as long as the condition is true. If you read only 10 bytes from a 100-byte buffer, epoll_wait fires again immediately.

**Edge-triggered (`EPOLLET`):** epoll_wait fires only when state transitions — data arrives (empty → has data). If you don't read everything, epoll_wait doesn't fire again until more data arrives.

Edge-triggered requires:
1. Non-blocking fds
2. Read in a loop until `EAGAIN`/`EWOULDBLOCK`

```c
// Edge-triggered read loop:
while (1) {
    ssize_t n = recv(fd, buf, sizeof(buf), 0);
    if (n < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) break;  // done
        // real error
        break;
    }
    if (n == 0) { close_connection(fd); break; }
    process(buf, n);
}
```

**LDS uses level-triggered** — simpler and correct for the request pattern.

---

## Complete Server Example

```c
int epfd = epoll_create1(EPOLL_CLOEXEC);

// Add listen fd:
struct epoll_event ev = { .events = EPOLLIN, .data.fd = listen_fd };
epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev);

while (running) {
    struct epoll_event events[64];
    int n = epoll_wait(epfd, events, 64, -1);
    
    for (int i = 0; i < n; i++) {
        int fd = events[i].data.fd;
        
        if (fd == listen_fd) {
            // New connection
            int client = accept(listen_fd, NULL, NULL);
            struct epoll_event cev = { .events = EPOLLIN, .data.fd = client };
            epoll_ctl(epfd, EPOLL_CTL_ADD, client, &cev);
            
        } else if (events[i].events & EPOLLIN) {
            // Data from existing client
            handle_client(fd);
            
        } else if (events[i].events & (EPOLLERR | EPOLLHUP)) {
            // Client disconnected
            epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
            close(fd);
        }
    }
}
```

---

## The Reactor Pattern

epoll is the mechanism. Reactor is the design pattern that wraps it:

```
Reactor:
- Owns the epoll fd
- Add(fd, handler) — registers fd + stores handler
- Remove(fd) — deregisters
- Run() — loops on epoll_wait, dispatches to registered handlers

epoll_wait fires on fd X
    → look up handler for fd X
    → call handler(fd X)
```

The handler knows what to do with that specific fd — the Reactor doesn't. This is the per-fd handler map upgrade needed for Phase 2A.

---

## LDS Context

`Reactor` wraps epoll. In Phase 1 it watches:
- NBD socketpair fd → fires `mediator.Notify(fd)`
- signalfd → fires shutdown handler

In Phase 2A it adds:
- TCPServer listen fd → fires `tcp_server.OnAccept(fd)`
- Each client fd (added dynamically by OnAccept) → fires `tcp_server.OnClientData(fd)`

All handled by the same `epoll_wait` loop.

---

## Understanding Check

> [!question]- Why does edge-triggered mode require reading until EAGAIN, and what happens in LDS if you forget this and use EPOLLET?
> Edge-triggered epoll fires only on state transitions — when data newly arrives on an fd that had no data. If you read only part of the available data and return from the handler, epoll will not fire again until more data arrives. Any bytes left in the kernel buffer are stranded indefinitely. In LDS, this would mean a partially-received NBD request sits in the buffer forever: the Reactor loop never re-dispatches that fd until the NBD driver sends additional bytes, which may never happen since the driver is waiting for the response to the request it already sent. The connection deadlocks. LDS uses level-triggered precisely to avoid this complexity.

> [!question]- Why is epoll O(1) per event while select and poll are O(n) in the number of registered file descriptors?
> select and poll require the application to pass the entire set of watched fds on every call, and the kernel must scan the whole set to find which ones are ready. With 10,000 fds and only 10 active, the kernel does 10,000 checks per call. epoll maintains an internal ready list in the kernel — when an fd becomes ready, the kernel appends it to the list. epoll_wait only copies out the ready entries, so with 10,000 fds and 10 active you get back exactly 10 entries regardless of total fd count. Registration is a one-time O(1) epoll_ctl call per fd.

> [!question]- What goes wrong if a handler called from the epoll_wait loop blocks for 200ms waiting for a response from a slow minion?
> The entire Reactor loop is blocked for those 200ms. During that time, no other fd in the epoll set is serviced: new TCP clients cannot be accepted, other NBD requests pile up in the kernel buffer, and the signalfd for SIGTERM is not processed — preventing clean shutdown. The single-threaded Reactor model requires handlers to be non-blocking and fast. The correct design is for the handler to submit work to the ThreadPool/WPQ and return immediately, letting the worker thread wait for the minion response asynchronously while the Reactor loop stays responsive.

> [!question]- Why must you close a client fd with close() AND remove it from epoll with EPOLL_CTL_DEL before closing, or does close() handle the epoll cleanup automatically?
> In most cases, close() on a file descriptor automatically removes it from all epoll interest lists — the kernel cleans up the epoll registration when the fd is destroyed. However, if the fd was duplicated (via dup() or fork()), close() only decrements the reference count; the underlying file description survives and remains in epoll until all copies are closed. In that case, epoll keeps firing on an fd you think you've closed, and m_handlers[fd] may now point to a different connection reusing the same fd number. Best practice is to explicitly call EPOLL_CTL_DEL before close() to avoid subtle bugs with dup'd fds.

> [!question]- In the LDS Phase 2A design, why is it correct to add the per-client fd to the same epoll instance that watches the NBD socketpair, rather than creating a separate epoll fd for TCP clients?
> epoll can multiplex heterogeneous fd types — regular files, sockets, pipes, signalfd — in a single instance. Using one epoll fd for all of LDS's I/O sources means one thread, one blocking point, and one dispatch loop handles all events. Adding a separate epoll fd for TCP clients would require either a second thread (adding synchronization complexity) or polling both epoll instances in sequence (creating latency for whichever is checked second). The Reactor's handler map scales cleanly: each fd has its own handler pointer, so the NBD handler and the TCP client handlers coexist without interfering.
