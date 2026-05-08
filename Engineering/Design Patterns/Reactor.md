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
