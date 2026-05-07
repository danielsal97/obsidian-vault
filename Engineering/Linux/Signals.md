# Signals

A signal is an asynchronous notification sent to a process. The kernel interrupts the process's normal execution to deliver it.

---

## Common Signals

| Signal | Value | Default | When sent |
|---|---|---|---|
| SIGINT | 2 | Terminate | Ctrl+C |
| SIGTERM | 15 | Terminate | `kill PID` |
| SIGKILL | 9 | Terminate | `kill -9 PID` — cannot be caught or ignored |
| SIGSEGV | 11 | Core dump | Null/invalid pointer dereference |
| SIGABRT | 6 | Core dump | `abort()` called |
| SIGUSR1 | 10 | Terminate | User-defined |
| SIGUSR2 | 12 | Terminate | User-defined |
| SIGCHLD | 17 | Ignore | Child process changed state |
| SIGALRM | 14 | Terminate | Timer expired (`alarm()`) |
| SIGHUP | 1 | Terminate | Terminal closed / "reload config" convention |
| SIGPIPE | 13 | Terminate | Write to broken pipe/socket |

---

## Sending Signals

```c
kill(pid, SIGTERM);    // send SIGTERM to process pid
kill(0, SIGTERM);      // send to all processes in process group
kill(-1, SIGTERM);     // send to all processes (dangerous)
raise(SIGUSR1);        // send to yourself
```

---

## Handling Signals — sigaction

```c
#include <signal.h>

void handler(int sig) {
    // runs asynchronously — very limited what you can do here
    write(STDOUT_FILENO, "got signal\n", 11);  // write() is async-signal-safe
}

struct sigaction sa;
sa.sa_handler = handler;
sigemptyset(&sa.sa_mask);      // don't block other signals during handler
sa.sa_flags = SA_RESTART;      // restart interrupted syscalls automatically

sigaction(SIGINT, &sa, NULL);   // register handler for SIGINT
```

**`signal()` vs `sigaction()`:**
- `signal()` — simple but behavior is implementation-defined. On some systems the handler resets to default after first delivery.
- `sigaction()` — reliable, portable, the correct way.

---

## Async-Signal Safety

A signal can interrupt ANY instruction — including `malloc`, `printf`, `mutex_lock`. If your handler calls a non-async-signal-safe function while the main code is inside that same function, you get a deadlock or heap corruption.

**Async-signal-safe functions** (can call from handler):
- `write()`, `read()`, `close()`
- `_exit()`
- `sem_post()`
- `signal()`
- Most system calls

**NOT async-signal-safe:**
- `printf`, `fprintf` (uses `malloc` internally)
- `malloc`, `free`
- `pthread_mutex_lock`
- `std::cout`
- Almost all C++ standard library

**Safe pattern — set a flag, check in main loop:**
```c
volatile sig_atomic_t g_shutdown = 0;

void handler(int sig) {
    g_shutdown = 1;   // atomic store — safe
}

// Main loop:
while (!g_shutdown) {
    // do work
}
```

`volatile sig_atomic_t` — guarantees the store/load is atomic on the target platform.

---

## Blocking Signals — sigprocmask

Block signals from being delivered while processing something critical:

```c
sigset_t mask, old_mask;
sigemptyset(&mask);
sigaddset(&mask, SIGINT);
sigaddset(&mask, SIGTERM);

// Block SIGINT and SIGTERM:
sigprocmask(SIG_BLOCK, &mask, &old_mask);
// ... critical section — signals are pending, not delivered ...
sigprocmask(SIG_SETMASK, &old_mask, NULL);  // restore
```

Blocked signals are queued (pending). When unblocked, they're delivered.

**In threads:** `pthread_sigmask` does the same thing per-thread. Common pattern: block signals in all threads, then create one dedicated signal-handling thread.

---

## signalfd — Signals as File Descriptors

Linux-specific. Converts signals into readable file descriptor events. Works with `epoll` — no async handler needed.

```c
sigset_t mask;
sigemptyset(&mask);
sigaddset(&mask, SIGINT);
sigaddset(&mask, SIGTERM);

// Block these signals from async delivery:
sigprocmask(SIG_BLOCK, &mask, NULL);

// Create a fd that becomes readable when a signal arrives:
int sfd = signalfd(-1, &mask, SFD_NONBLOCK | SFD_CLOEXEC);

// Add to epoll:
struct epoll_event ev = { .events = EPOLLIN, .data.fd = sfd };
epoll_ctl(epfd, EPOLL_CTL_ADD, sfd, &ev);

// When epoll_wait fires on sfd:
struct signalfd_siginfo info;
read(sfd, &info, sizeof(info));
// info.ssi_signo tells you which signal arrived
```

**Why signalfd is better than async handlers:**
- No async-signal-safety constraints
- Integrates with epoll — one event loop handles everything
- Signals are handled at a predictable point in the code

**LDS:** Reactor uses signalfd for SIGINT/SIGTERM. The same epoll loop that watches the NBD fd also watches the signalfd. Ctrl+C → epoll fires → Reactor sets `m_stop = true` and exits cleanly.

---

## SIGUSR1/SIGUSR2 — LDS Watchdog

The C Watchdog uses SIGUSR1 and SIGUSR2 as a ping-pong heartbeat between the guardian process and the main process.

```
Main process       Guardian process
    │                    │
    ├── SIGUSR1 ────────▶│  "I'm alive"
    │                    │
    │◀──── SIGUSR1 ──────┤  "I got it"
    │                    │
    │  (15s no signal)   │
    │                    ├── fork+exec  ← main process died, restart it
```

`sem_timedwait` blocks the guardian waiting for the next ping with a timeout. If the timeout expires without a signal, the guardian assumes the main process is dead.

---

## SIGPIPE — Broken Pipe

When you write to a socket or pipe whose other end is closed, the OS sends SIGPIPE to your process. Default action: terminate. This kills your server if a client disconnects mid-write.

**Fix: ignore SIGPIPE and check write() return value:**
```c
signal(SIGPIPE, SIG_IGN);   // ignore SIGPIPE globally
// or per-send:
send(fd, buf, n, MSG_NOSIGNAL);  // don't send SIGPIPE for this call
```

Always check `send()`/`write()` return value — if the client disconnected, it returns -1 with `errno == EPIPE`.
