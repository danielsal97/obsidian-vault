# Reactor Pattern

Handles multiple I/O sources in a single thread by waiting for events and dispatching them to registered handlers. Avoids a thread-per-connection model.

---

## Core Idea

```
while (true) {
    fds_ready = epoll_wait(...)      // block until any fd has an event
    for each ready fd:
        handler = dispatch_table[fd]
        handler->handle_event()
}
```

The reactor loop never blocks in a handler — handlers do non-blocking I/O and return immediately. The next `epoll_wait` picks up the next event.

---

## Implementation

```cpp
class IHandler {
public:
    virtual void handle_event(int fd, uint32_t events) = 0;
    virtual ~IHandler() = default;
};

class Reactor {
    int m_epfd;
    std::unordered_map<int, IHandler*> m_handlers;

public:
    Reactor() : m_epfd(epoll_create1(0)) {}

    void register_fd(int fd, uint32_t events, IHandler* handler) {
        epoll_event ev{ .events = events, .data.fd = fd };
        epoll_ctl(m_epfd, EPOLL_CTL_ADD, fd, &ev);
        m_handlers[fd] = handler;
    }

    void unregister_fd(int fd) {
        epoll_ctl(m_epfd, EPOLL_CTL_DEL, fd, nullptr);
        m_handlers.erase(fd);
    }

    void run() {
        epoll_event events[64];
        while (true) {
            int n = epoll_wait(m_epfd, events, 64, -1);
            for (int i = 0; i < n; ++i) {
                int fd = events[i].data.fd;
                m_handlers[fd]->handle_event(fd, events[i].events);
            }
        }
    }
};
```

---

## Concrete Handlers

```cpp
class NBDHandler : public IHandler {
    void handle_event(int fd, uint32_t) override {
        // read request from NBD socket, non-blocking
        DriverData data;
        read_nbd_request(fd, &data);
        m_mediator->handle(&data);
    }
};

class SignalHandler : public IHandler {
    void handle_event(int fd, uint32_t) override {
        signalfd_siginfo sig;
        read(fd, &sig, sizeof(sig));
        if (sig.ssi_signo == SIGTERM) reactor->stop();
    }
};
```

---

## LDS Reactor

```
epoll fd watches:
  ├── nbd_fd (socketpair[0]) — kernel sends NBD requests here
  ├── signal_fd              — SIGTERM, SIGINT for graceful shutdown
  └── [future: tcp_fd]       — TCP client connections
```

Each fd maps to a handler class. The main loop is a single thread — no synchronization needed for the dispatch table.

---

## Level vs Edge Triggered

| | Level-triggered (LT) | Edge-triggered (ET) |
|---|---|---|
| When does epoll fire? | As long as data is available | Only when new data arrives |
| Must drain buffer? | No — can read partial | Yes — must read until EAGAIN |
| Default | Yes | No — set `EPOLLET` flag |

```c
// Edge-triggered registration:
ev.events = EPOLLIN | EPOLLET;
epoll_ctl(epfd, EPOLL_CTL_ADD, fd, &ev);

// With ET, must read all available data:
while (true) {
    ssize_t n = read(fd, buf, sizeof(buf));
    if (n == -1 && errno == EAGAIN) break;   // no more data
    // process n bytes
}
```

See [[../Networking/epoll]] for full detail.

---

## Single-Threaded vs Multi-Threaded Reactor

**Single-threaded Reactor** (LDS model):
- One thread does all dispatch
- Handlers must not block
- Simpler — no races in dispatch table

**Multi-threaded Reactor**:
- Reactor dispatches to a thread pool
- Handlers can block
- Handlers need their own locking

LDS hands off blocking work to the `ThreadPool` via `WPQ`, keeping the Reactor loop fast.

---

## Stopping the Reactor

Clean shutdown via `signalfd` (converts SIGTERM to a readable fd event):

```cpp
// Register signal fd with reactor:
int sfd = signalfd(-1, &mask, SFD_NONBLOCK | SFD_CLOEXEC);
reactor.register_fd(sfd, EPOLLIN, &signal_handler);

// In signal_handler:
void handle_event(int fd, uint32_t) override {
    // read signal, set m_running = false
    m_reactor.stop();
}
```

See [[Signals]] — `signalfd` makes signal handling safe to mix with `epoll`.

---

## Comparison to Other I/O Models

| Model | How |
|---|---|
| Thread per connection | `accept()` → `pthread_create()` → blocking I/O in thread |
| select/poll | Older multiplexing — O(n) scan, lower fd limit |
| **epoll Reactor** | O(1) event delivery, scales to thousands of fds |
| io_uring (Linux 5.1+) | Async I/O via submission/completion ring buffers |

---

## Related Notes

- [[../Networking/epoll]] — the underlying Linux mechanism
- [[Signals]] — signalfd for signal handling in Reactor
- [[../Linux/File Descriptors]] — fd lifecycle and non-blocking mode
- [[Command]] — handlers often create Command objects and push to a queue

---

## Understanding Check

> [!question]- Why must Reactor handlers be non-blocking, and what is the exact failure mode if NBDHandler::handle_event() calls a blocking recv() that waits 500ms?
> The Reactor loop is single-threaded. epoll_wait returns a batch of ready fds, and the loop dispatches them sequentially. If handle_event() on one fd blocks for 500ms, all other ready fds in the current batch wait. Worse, new events accumulate in the kernel's epoll ready list but are never dequeued until the current handler returns. In LDS, this would mean the signalfd SIGTERM event is not processed (no clean shutdown), new NBD requests pile up in the socketpair buffer, and the kernel may throttle further NBD I/O. The correct design is for handlers to read available data (non-blocking), create a Command, push it to WPQ, and return immediately.

> [!question]- How does LDS use signalfd to make SIGTERM handling safe in a Reactor loop, and what would go wrong with a traditional signal handler?
> A traditional signal handler runs asynchronously and can interrupt any instruction — including a malloc, a container operation, or an epoll_wait call. Writing to a mutex or calling non-async-signal-safe functions inside a signal handler is undefined behavior. signalfd converts SIGTERM into a file descriptor event: the OS blocks actual delivery of the signal and instead makes the signalfd readable. The Reactor registers the signalfd with epoll, and when SIGTERM arrives, epoll_wait returns the signalfd as a ready fd. The SignalHandler::handle_event() runs in the normal event loop, safely calling m_reactor.stop() — no async interruption, no race conditions.

> [!question]- What goes wrong if the Reactor's m_handlers map is modified (fd added or removed) from a worker thread while the Reactor loop is iterating it on the main thread?
> The Reactor's dispatch table (m_handlers) is an unordered_map modified by register_fd() and unregister_fd(). The Reactor loop reads from it on every epoll_wait iteration. Concurrent read-modify from two threads without synchronization is a data race — undefined behavior. The map's internal structure could be partially modified mid-traversal: iterator invalidation, use-after-free on nodes, or a lookup returning a garbage handler pointer, leading to a crash or wrong handler being called. The LDS design avoids this by keeping all fd registration and deregistration on the Reactor thread itself (done inside event handlers), so the map is only ever modified and read by the same thread.

> [!question]- In Phase 2A, when a TCP client connects and the TCPServer handler calls register_fd() for the new client fd, how does this fit into the single-threaded Reactor model without creating a race?
> The TCPServer's handle_event() is called from within the Reactor's event loop iteration — it runs on the Reactor thread. Calling reactor.register_fd() from inside a handler is safe because the Reactor loop has already fetched the current batch of events from epoll_wait; the new fd won't appear until the next epoll_wait call. By the time register_fd() returns and the handler returns to the loop, the next iteration of epoll_wait will include the newly registered client fd. There is no race because the handler and the loop iteration are sequential — the loop can't be in epoll_wait while the handler is running.

> [!question]- Why is the io_uring model fundamentally different from the epoll Reactor, and for what LDS workload would io_uring be a meaningful improvement?
> epoll is readiness-based: it tells you when an fd is ready so you can issue a syscall (recv, send, read, write) without blocking. You still make syscalls, each of which crosses the user/kernel boundary. io_uring is completion-based: you submit I/O operations to a ring buffer in shared memory, and the kernel processes them asynchronously, placing results in a completion ring — zero per-operation syscalls after the initial setup. For LDS's storage layer (reading/writing blocks to a local file via LocalStorage), io_uring would reduce syscall overhead for high-throughput sequential block operations, where the epoll model adds a round-trip per operation (epoll_wait to know the fd is ready, then a separate pread/pwrite syscall).
