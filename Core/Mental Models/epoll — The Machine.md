# epoll — The Machine

## The Model
A notification board. You pin file descriptors to the board (register). You stand at the board and watch (epoll_wait). The moment any pinned fd has data ready, epoll_wait hands you a list of exactly which fds are ready — only the ready ones, instantly, with one call. No scanning. O(1) per event regardless of how many fds are pinned.

## How It Moves

```
Setup:
  epfd = epoll_create1(0)              ← create the board

  epoll_ctl(epfd, EPOLL_CTL_ADD, server_fd, &event)   ← pin server fd
  epoll_ctl(epfd, EPOLL_CTL_ADD, client_fd, &event)   ← pin client fd
  epoll_ctl(epfd, EPOLL_CTL_ADD, nbd_fd, &event)      ← pin NBD device fd

Event loop:
  while (running) {
    n = epoll_wait(epfd, events, 64, -1)   ← stand at board, wait
    // n = number of ready fds (1 to 64)
    for (i = 0; i < n; i++) {
      fd = events[i].data.fd
      handler = m_handlers[fd]              ← O(1) lookup
      handler(fd)                           ← dispatch
    }
  }
```

**vs select/poll:**
```
select/poll:  you give it ALL your fds every call → O(n) scan
              kernel returns a bitmask → you scan it to find ready ones
              limit: ~1024 fds (select), works but slow

epoll:        kernel maintains internal list → only returns READY fds
              O(1) per event regardless of total fd count
              limit: millions of fds
```

**Level-triggered vs edge-triggered:**
- **Level-triggered (default)**: epoll_wait keeps returning an fd as long as data is available. Safe — you can't miss data.
- **Edge-triggered (EPOLLET)**: epoll_wait returns an fd ONCE when new data arrives. You must read until `EAGAIN` or data is lost. Faster but requires non-blocking I/O and careful loops.

## The Blueprint

```cpp
// Non-blocking fd (required for edge-triggered, recommended always):
int flags = fcntl(fd, F_GETFL, 0);
fcntl(fd, F_SETFL, flags | O_NONBLOCK);

// Register fd:
epoll_event ev;
ev.events = EPOLLIN | EPOLLERR | EPOLLHUP;
ev.data.fd = fd;
epoll_ctl(epfd, EPOLL_CTL_ADD, fd, &ev);

// Remove fd (e.g., on connection close):
epoll_ctl(epfd, EPOLL_CTL_DEL, fd, nullptr);

// Wait and dispatch:
epoll_event events[64];
int n = epoll_wait(epfd, events, 64, timeout_ms);
for (int i = 0; i < n; i++) {
    if (events[i].events & EPOLLIN)  handleRead(events[i].data.fd);
    if (events[i].events & EPOLLERR) handleError(events[i].data.fd);
}
```

## Where It Breaks

- **Long handler**: if a handler takes 100ms, the entire event loop is blocked for 100ms — all other fds starve. Push work to the ThreadPool; keep handlers fast.
- **Not removing closed fds**: if you `close(fd)` without `epoll_ctl(DEL)`, the fd slot may be reused — epoll reports events on the wrong handler.
- **EPOLLHUP not handled**: remote closed the connection → EPOLLHUP fires → if you only handle EPOLLIN, the fd stays registered, keeps firing EPOLLHUP forever.

## In LDS

`design_patterns/reactor/src/reactor.cpp`

The LDS Reactor is a direct implementation of the epoll pattern. It maintains `m_epfd` (the board) and `m_handlers` (`unordered_map<int, Handler>`). `AddHandler(fd, handler)` calls `epoll_ctl(ADD)`. The event loop calls `epoll_wait`, iterates the ready events, and looks up + calls the handler for each fd. The Reactor never does the work itself — it dispatches to the ThreadPool.

## Validate

1. LDS has 500 registered fds (multiple clients + NBD device). 3 fds have data ready. `epoll_wait` returns. How many fds does LDS scan to find the 3 ready ones?
2. A client closes the TCP connection. `EPOLLHUP` fires. The Reactor's handler reads 0 bytes from `recv` (EOF). What must the handler do next to prevent the epoll loop from firing EPOLLHUP on every iteration forever?
3. A handler calls `LocalStorage::Read(offset, 512MB)` — a slow operation. What happens to other fds with pending data while this runs?

## Connections

**Theory:** [[Core/Theory/Networking/epoll]]  
**Mental Models:** [[Reactor Pattern — The Machine]], [[File Descriptors — The Machine]], [[TCP Sockets — The Machine]], [[Kernel — The Machine]]  
**Tradeoffs:** [[Why epoll over select and poll]]  
**LDS Implementation:** [[LDS/Infrastructure/Reactor]] — epoll is the core; [[LDS/Architecture/Concurrency Model]]  
**Runtime Machines:** [[LDS/Runtime Machines/Reactor — The Machine]]  
**Glossary:** [[epoll]], [[File Descriptors]]
