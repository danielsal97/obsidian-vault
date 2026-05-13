# Why epoll over select and poll

## Context
You need to watch many file descriptors for I/O readiness in a single thread.

## Options

| | select | poll | epoll |
|---|---|---|---|
| Time per call | O(n) — kernel scans all fds | O(n) — kernel scans all fds | O(1) — kernel returns only ready fds |
| Max fds | 1024 (FD_SETSIZE) | Unlimited | Unlimited |
| Registration | Rebuild set every call | Rebuild array every call | One-time epoll_ctl per fd |
| OS | POSIX | POSIX | Linux only |

## The Concrete Reason

With 10,000 monitored fds and 10 active: `select`/`poll` scan all 10,000 every call.
`epoll` maintains a kernel-side ready list and returns exactly the 10 active fds — O(1) regardless of total count.

## When you'd pick differently

- **select/poll**: portability to non-Linux (macOS/BSD → use `kqueue`)
- **io_uring**: completion-based, zero per-operation syscalls — better for high-throughput storage I/O

## See also
→ [[../../06 - Networking/Theory/04 - epoll]] — full API reference
→ [[../../06 - Networking/Mental Models/04 - epoll — The Machine]] — runtime intuition
→ [[../../07 - Design Patterns/Mental Models/01 - Reactor Pattern — The Machine]] — how epoll becomes an event loop
