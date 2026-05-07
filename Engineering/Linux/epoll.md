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
