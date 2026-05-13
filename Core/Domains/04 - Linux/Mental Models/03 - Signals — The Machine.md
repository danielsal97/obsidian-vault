# Signals — The Machine

## The Model
An electrical interrupt delivered to a process. The kernel reaches into the process mid-execution, taps it on the shoulder, and the process jumps to a pre-registered handler function. After the handler returns, execution resumes exactly where it was interrupted — unless the signal killed the process.

## How It Moves

```
Process running:
  ... → instruction 5000 → instruction 5001 → ...

Kernel delivers SIGTERM:
  1. Process interrupted after instruction 5000
  2. Current register state saved
  3. PC jumps to signal handler
  4. Handler runs: sets g_running = false
  5. Handler returns
  6. Register state restored
  7. Execution resumes at instruction 5001
  (unless handler called exit() or the default action is termination)
```

**Default actions:**
- `SIGTERM` → terminate (catchable, allows graceful shutdown)
- `SIGKILL` → terminate immediately (cannot be caught — hard power cut)
- `SIGSEGV` → terminate + core dump (invalid memory access)
- `SIGINT`  → terminate (Ctrl+C — catchable)
- `SIGPIPE` → terminate (write to broken pipe — often ignored in servers)

## The Blueprint

```c
#include <signal.h>

// Register a handler:
struct sigaction sa = {};
sa.sa_handler = my_handler;
sa.sa_flags = SA_RESTART;   // restart interrupted syscalls automatically
sigaction(SIGTERM, &sa, NULL);

void my_handler(int sig) {
    // CONSTRAINTS: only async-signal-safe functions here
    // NO: malloc, printf, mutex lock, new, STL containers
    // YES: write(), exit(), g_flag = 1 (if volatile sig_atomic_t)
    g_running = 0;
}
```

**`volatile sig_atomic_t`**: the flag your handler sets must be declared `volatile sig_atomic_t`. `volatile` prevents the compiler from caching the value in a register. `sig_atomic_t` guarantees atomic read/write on the platform.

**`SA_RESTART`**: without this, a signal interrupts a blocking `read()`/`recv()` and returns `EINTR`. With `SA_RESTART`, the kernel automatically restarts the syscall.

## Where It Breaks

- **Calling malloc in a handler**: malloc uses a mutex internally. If the signal interrupted malloc, the mutex is already locked — your handler deadlocks.
- **Not `volatile`**: compiler sees `while (g_running)` as an infinite loop (g_running never changes in the loop's visible code) and optimizes the check away.
- **Race condition**: two signals delivered simultaneously — `sig_atomic_t` prevents tearing, but complex state changes still need care.

## In LDS

`design_patterns/reactor/src/reactor.cpp`

The LDS Reactor loop runs `while (m_running)`. To stop LDS gracefully (Ctrl+C), a SIGINT/SIGTERM handler sets `m_running = false`. The Reactor's `epoll_wait` returns with `EINTR`, the loop checks `m_running`, and exits cleanly — allowing the ThreadPool to drain its queue before shutdown.

## Validate

1. LDS's Reactor loop is `while (m_running) { epoll_wait(...); }`. The signal handler sets `m_running = false`. Without `volatile`, what might the compiler legally do to this loop?
2. You write `printf("got signal %d\n", sig)` inside your signal handler. Why is this dangerous? What should you use instead?
3. `SIGKILL` is sent to the LDS process. The ThreadPool has 50 pending tasks. What happens to them?

## Connections

**Theory:** [[Core/Domains/04 - Linux/Theory/03 - Signals]]  
**Mental Models:** [[Processes — The Machine]], [[File Descriptors — The Machine]], [[Memory Ordering — The Machine]], [[Reactor Pattern — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Reactor]] — signalfd integration; [[LDS/Decisions/Why signalfd not sigaction]]  
**Runtime Machines:** [[LDS/Runtime Machines/Reactor — The Machine]]
