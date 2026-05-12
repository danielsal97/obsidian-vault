---
name: epoll
type: linux-api
---

# epoll

**[man page →](https://man7.org/linux/man-pages/man7/epoll.7.html)** | **[Wikipedia →](https://en.wikipedia.org/wiki/Epoll)**

A Linux kernel facility for monitoring many file descriptors simultaneously with near-zero CPU cost when idle. Returns only when at least one fd is ready for I/O.

## The Problem It Solves

```
Option 1: Blocking read per fd
  read(fd1)  ← blocks here until fd1 has data
  read(fd2)  ← never reached while fd1 is busy
  → Need one thread per fd. Doesn't scale.

Option 2: Polling (busy-wait)
  while(true) { check fd1; check fd2; ... }
  → Wastes CPU even when nothing is happening.

Option 3: epoll
  epoll_wait(...)  ← sleeps with 0% CPU
  → Wakes exactly when an fd is ready. Scales to thousands of fds.
```

## Core API

```c
// Create epoll instance
int epfd = epoll_create1(0);

// Register fd to watch
struct epoll_event ev = { .events = EPOLLIN, .data.fd = nbd_fd };
epoll_ctl(epfd, EPOLL_CTL_ADD, nbd_fd, &ev);

// Wait for events (blocks until at least one fd is ready)
int n = epoll_wait(epfd, events, MAX_EVENTS, -1 /*timeout: forever*/);
for (int i = 0; i < n; i++) {
    handle(events[i].data.fd);
}
```

## In LDS

The [[Reactor]] wraps epoll. The master process runs one epoll loop on the main thread, watching:
- The NBD socketpair fd (for kernel read/write requests)
- The signalfd (for SIGINT/SIGTERM shutdown)

When the NBD fd becomes readable, epoll wakes the main thread and dispatches to `InputMediator::HandleEvent`.

## Related
- [[Reactor]] — the design pattern wrapping epoll
- [[Why signalfd not sigaction]] — how signals are integrated into epoll
- [[Concurrency Model]] — how the main thread and workers divide responsibilities
