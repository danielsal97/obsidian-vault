# LDS Reactor — The Machine

## The Model
A traffic controller at a single intersection who never moves. Two roads feed into the intersection: the driver fd (NBD requests or TCP data) and the signal fd (SIGINT/SIGTERM). The controller watches both with `epoll_wait`. When a vehicle arrives on either road, the controller calls the registered handler and immediately returns to watching. The controller never handles traffic itself.

## Why This Exists

**Without Reactor (thread-per-connection):**
- 1000 concurrent NBD/TCP clients → 1000 threads
- 1000 kernel stacks × 8MB = 8GB memory for stacks alone
- Scheduler context-switches between idle threads every quantum → cache pollution
- Each I/O completion wakes one blocked thread → one syscall per event

**Reactor solves:**
- One thread monitors ALL file descriptors simultaneously via epoll
- epoll_wait() returns only ready fds — zero wasted work on idle connections
- No context switch per event: same thread calls all handlers in the event loop
- O(1) fd readiness notification regardless of how many fds are registered

**Runtime effect:** LDS registers the NBD socketpair fd, the TCP server fd, the signalfd, and each connected client fd — all watched by one epoll instance. When a write request arrives on the NBD fd AND a new TCP client connects simultaneously, the Reactor handles both in the same `epoll_wait()` call, no synchronization needed, no race conditions. One thread, zero locks in the hot path.

## How It Moves

```
Reactor::Reactor()
  m_epoll_fd = epoll_create1(0)   ← create the board
  SetupSignals():
    sigprocmask(SIG_BLOCK, {SIGINT, SIGTERM})   ← block signals from normal delivery
    m_signal_fd = signalfd(...)                  ← route signals through fd instead
    epoll_ctl(ADD, m_signal_fd)                  ← pin signal fd to board

Reactor::Add(fd)
  epoll_ctl(EPOLL_CTL_ADD, fd, EPOLLIN)         ← pin driver fd to board

Reactor::Run()
  while (true):
    n = epoll_wait(m_epoll_fd, events, MAX_EVENTS=10, timeout=-1)
    
    for each event:
      if fd == m_signal_fd:
        return              ← SIGINT/SIGTERM received → exit loop, clean shutdown
      else:
        m_io_handler(fd)   ← call the single registered handler
```

**Why `signalfd` instead of `signal()`:**
Traditional signal handlers interrupt code mid-execution (async). `signalfd` converts SIGINT/SIGTERM into readable events on a file descriptor — they arrive in the `epoll_wait` loop like any other event, in order, safely. No async-signal-safe restrictions. No `volatile sig_atomic_t`.

**ONE handler for ALL fds:**
Unlike a map-based Reactor, LDS's Reactor has a single `m_io_handler`. The handler (`InputMediator::Notify`) is responsible for identifying what the fd is and what to do. This keeps the Reactor simple — it knows nothing about protocols.

## The Blueprint

```cpp
// reactor.hpp (hrd41 namespace):
class Reactor {
    int m_epoll_fd;
    int m_signal_fd;
    std::function<void(int)> m_io_handler;
    static constexpr int MAX_EVENTS = 10;
    void SetupSignals();
public:
    Reactor();
    ~Reactor();   // closes m_epoll_fd and m_signal_fd
    void Add(int fd);
    void Remove(int fd);
    void SetHandler(std::function<void(int)> handler);
    void Run();   // blocks until SIGINT/SIGTERM
};
```

**Wiring in main:**
```cpp
NBDDriverComm driver("/dev/nbd0", storage_size);
InputMediator mediator(&driver, &storage);
Reactor reactor;

reactor.Add(driver.GetFD());   // pin the NBD socketpair fd
reactor.SetHandler([&mediator](int fd) {
    mediator.Notify(fd);       // mediator handles everything
});
reactor.Run();   // hands control to epoll — blocks here
```

## Where It Breaks

- **No handler set**: `Run()` throws `ReactorError("No handler set")` — must call `SetHandler` before `Run`
- **Handler throws**: exception escapes `m_io_handler(fd)` — propagates out of `Run()` → Reactor dies, no more events served. Catch in the handler.
- **Slow handler**: `mediator.Notify(fd)` blocks for 100ms → all other fds starve during that time. The Reactor is designed to pair with the ThreadPool — Notify must be fast.
- **`epoll_wait` returns -1 with `EINTR`**: handled explicitly (`continue` the loop) — a non-blocked signal interrupted the syscall.

## Validate

1. SIGINT is sent to LDS. What happens to it before it reaches the Reactor? Why doesn't the signal handler fire?
2. The driver fd has a new request AND a SIGTERM arrives in the same `epoll_wait` batch. The loop processes the driver event first. What happens when it reaches the signal fd event?
3. `MAX_EVENTS = 10`. 15 fds become ready simultaneously. What happens to the remaining 5?

---

## Core Vault Cross-Links

→ [[01 - Reactor Pattern — The Machine]] — the general pattern this implements
→ [[04 - epoll — The Machine]] — what epoll_wait() actually does in the kernel
→ [[Networking Stack — The Machine]] — the full path from NIC to this Reactor
