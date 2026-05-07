# Decision: Why signalfd (not sigaction) for Signal Handling

## Decision

Use **`signalfd`** to handle `SIGINT`/`SIGTERM` in the Reactor, not `sigaction` or `signal()`.

---

## The Problem with sigaction

Traditional signal handlers are **asynchronous** — they interrupt your program at any instruction:

```cpp
// sigaction callback: runs at arbitrary point during execution
void handler(int sig) {
    // Only async-signal-safe functions allowed here:
    // write(), _exit(), sem_post() — that's about it
    // NO: malloc, printf, mutex, std::string, any C++ containers
}
```

Problems:
- Cannot safely call most functions from a signal handler
- Cannot use `std::mutex` (could deadlock if signal arrives while mutex held)
- Cannot integrate with `epoll` — separate code path from normal I/O
- Race conditions: signal can arrive at any point

---

## signalfd — Signals as File Descriptors

```cpp
// Block the signal from traditional delivery:
sigset_t mask;
sigemptyset(&mask);
sigaddset(&mask, SIGINT);
sigaddset(&mask, SIGTERM);
pthread_sigmask(SIG_BLOCK, &mask, nullptr);

// Create a readable FD that delivers the signal:
int sig_fd = signalfd(-1, &mask, SFD_NONBLOCK | SFD_CLOEXEC);

// Add to epoll — signals now appear as I/O events:
epoll_ctl(epoll_fd, EPOLL_CTL_ADD, sig_fd, &event);
```

Now `SIGINT`/`SIGTERM` appear in `epoll_wait()` as a readable event on `sig_fd`. The signal handler runs **synchronously** in the main event loop — no async interruption, no restrictions.

---

## Comparison

| | sigaction | signalfd |
|---|---|---|
| Async interrupt | ✅ yes | ❌ no — synchronous only |
| Async-signal-safe only | ✅ required | ❌ no restriction |
| epoll integration | ❌ no | ✅ yes |
| Can use mutex, malloc | ❌ no | ✅ yes |
| Complexity | Low | Medium |
| Works across threads | ⚠️ tricky | ✅ clean |

---

## In the Reactor

```cpp
// Reactor adds sig_fd to epoll alongside NBD fd
// On SIGINT: epoll_wait returns sig_fd as readable
// Reactor reads the signal info:
struct signalfd_siginfo info;
read(sig_fd, &info, sizeof(info));

if (info.ssi_signo == SIGINT || info.ssi_signo == SIGTERM) {
    reactor.Stop();
}
```

This is the same code path as handling an I/O event — clean, synchronous, no special rules.

---

## Related Notes
- [[Reactor]]
- [[NBDDriverComm]]
- [[Known Bugs]] (conflicting signal handling bug)
