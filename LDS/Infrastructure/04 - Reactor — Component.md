# Reactor

**Location:** `design_patterns/reactor/`  
**Status:** ✅ Implemented  
**Layer:** Tier 2 — Framework

---

## What It Does

The Reactor is the **event loop** of the LDS master. It sits on the main thread and uses `epoll` to monitor file descriptors. When one becomes ready, it dispatches to the registered handler.

One thread. No blocking. Handles everything.

---

## Interface

```cpp
class Reactor {
public:
    explicit Reactor();

    void Add(int fd);                            // watch this fd
    void Remove(int fd);                         // stop watching
    void SetHandler(std::function<void(int)>);   // callback for all fds
    void Run();                                  // blocking event loop
    void Stop();                                 // stop the loop

private:
    int m_epoll_fd;
    int m_signal_fd;                             // signalfd for SIGINT/SIGTERM
    std::atomic<bool> running;
    std::function<void(int)> m_io_handler;
};
```

---

## How It's Used in `app/LDS.cpp`

```cpp
NBDDriverComm driver("/dev/nbd0", size);
Reactor reactor;

reactor.Add(driver.GetFD());
reactor.SetHandler([&](int fd) {
    auto req = driver.ReceiveRequest();
    if (req->m_type == DriverData::DISCONNECT) { reactor.Stop(); return; }
    storage.Read/Write(req);
    driver.SendReply(req);
});

reactor.Run();  // blocks until SIGINT
```

---

## Signal Handling

Uses `signalfd` — SIGINT/SIGTERM become readable fd events in epoll. No async signal handlers. When signal fires, `running = false` and `Run()` exits cleanly.

See: [[Why signalfd not sigaction]]

---

## Key Properties

| Property | Value |
|---|---|
| Threads used | 1 (main thread) |
| Max monitored fds | `MAX_EVENTS = 10` per wait, unlimited total |
| epoll mode | Level-triggered (EPOLLIN, default) |
| Timeout | `-1` (blocks indefinitely) |

---

## Related Notes
- [[Design Patterns/Reactor]] — deep dive with diagrams
- [[04 - Concurrency Model]] — how Reactor fits with other threads
- [[08 - Request Lifecycle]] — what happens inside the handler
- [[Engineering/NBD Protocol Deep Dive]]
