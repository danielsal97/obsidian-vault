# Reactor Pattern — The Machine

## The Model
A single traffic controller at a busy intersection. One thread sits at the intersection (epoll_wait). When a vehicle arrives (fd event), the controller looks up the registered handler for that road (fd) and waves it through (dispatches the handler). The controller never leaves the intersection. It never handles traffic itself. It only dispatches.

## How It Moves

```
          ┌─────────────────────────────────────────┐
          │              REACTOR                     │
          │                                         │
fd events │  epoll_wait() ──→ [event0, event1, ...]  │
──────────→  │                                      │
NBD fd    │  for each event:                        │──→ ThreadPool task
TCP fd    │    m_handlers[fd](event) ──────────────→│     (real work here)
client fd │                                         │
          └─────────────────────────────────────────┘
          Register:   AddHandler(fd, callback)
          Unregister: RemoveHandler(fd)
```

**The invariant:** the Reactor thread never blocks, never does slow work. Every handler must return immediately. Slow work (storage read, network send) is handed to the ThreadPool. If a handler blocks, ALL other fds wait — the intersection is jammed.

**Why single-threaded for dispatch:**
- No locking needed on the handler map — only one thread reads it
- Event ordering is deterministic — events for the same fd are processed in order
- Thread-per-connection alternative: each connection gets a thread → 10,000 connections = 10,000 threads → memory exhausted, context-switch overhead

## The Blueprint

```cpp
class Reactor {
    int m_epfd;
    std::unordered_map<int, Handler> m_handlers;
    std::atomic<bool> m_running;
    
public:
    void AddHandler(int fd, Handler h) {
        m_handlers[fd] = h;
        epoll_event ev = {EPOLLIN | EPOLLERR | EPOLLHUP, {.fd = fd}};
        epoll_ctl(m_epfd, EPOLL_CTL_ADD, fd, &ev);
    }
    
    void Run() {
        epoll_event events[64];
        while (m_running) {
            int n = epoll_wait(m_epfd, events, 64, 100);   // 100ms timeout
            for (int i = 0; i < n; i++) {
                m_handlers[events[i].data.fd](events[i]);
            }
        }
    }
};
```

## Where It Breaks

- **Slow handler**: `LocalStorage::Read` takes 10ms in the Reactor thread → all other fds blocked for 10ms. Always push to ThreadPool.
- **Handler modifies `m_handlers` during dispatch**: invalidates iterators in the dispatch loop. Defer handler changes to the start of the next iteration.
- **Handler throws**: exception escapes the event loop → all fds stop being served. Catch exceptions in the dispatch loop.

## In LDS

`design_patterns/reactor/src/reactor.cpp` + `include/reactor.hpp`

The LDS Reactor is the central nervous system. It registers:
1. The NBD device fd (`/dev/nbd0`) — fires when the kernel has a block request
2. The TCP server fd — fires when a new client connects
3. Each TCP client fd — fires when a client sends a request

When an event fires, the handler creates a task (Command object) and submits it to the ThreadPool. The Reactor itself touches no storage and sends no data — it only routes.

## Validate

1. 500 clients are connected. 3 send requests simultaneously. `epoll_wait` returns 3 events. How many threads handle these 3 requests, and what thread does the dispatching?
2. A handler calls `LocalStorage::Read(0, 512)` directly (not via ThreadPool). Client 2 sends a request while Read is running. What happens to client 2's request?
3. LDS is shutting down. `m_running = false`. The Reactor is in `epoll_wait` with no events. How long does it take to notice the shutdown?
