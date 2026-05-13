# Linux Runtime — The Machine

## The Model

A Linux process is the kernel's unit of isolation: its own virtual address space, its own file descriptor table, its own signal mask. Threads share the address space but each has its own stack. The kernel is not "alongside" your process — it IS running when any syscall happens. Your process alternates between user mode and kernel mode on every I/O call.

## How It Moves

```
Shell types: ./LDS
      │
      ▼
bash calls fork()
  → kernel: duplicate parent's memory map (copy-on-write)
  → child gets same fd table, same open files
      │
      ▼
child calls exec("./LDS")
  → kernel: replace address space with LDS binary
  → load .text, .data, .bss from ELF
  → set up initial stack (argc, argv, envp, aux vector)
  → dynamic linker runs: resolves shared library symbols
  → calls C++ global constructors (via .init_array)
      │
      ▼
main() starts running (user mode)
      │
      ▼
process calls socket() / epoll_create() / read()
  → CPU switches to kernel mode via syscall instruction
  → kernel executes, may block process (sleep in wait queue)
  → when data ready: kernel wakes process, returns to user mode
      │
      ▼
process runs until: exit() / SIGKILL / crash (SIGSEGV)
  → kernel: close all fds, free virtual memory, send SIGCHLD to parent
  → zombie state until parent calls wait()
```

## What the Kernel Does Behind the Scenes

Every time your process runs, the kernel is scheduling it. The scheduler runs on every timer interrupt (typically 1000Hz). Your process gets a time slice (~1-10ms). When the slice expires, or when you block on I/O, the kernel preempts you and runs another task.

Context switch cost: ~1-5μs. That's why blocking on I/O is fine (the kernel efficiently switches away) but spinning wastes CPU.

## Where Processes Block

- `read()` on an empty socket → process sleeps in socket's wait queue
- `epoll_wait()` with no ready fds → sleeps in epoll's wait queue
- `pthread_mutex_lock()` when mutex is held → futex sleep (kernel park)
- `sleep()` / `nanosleep()` → timer-based wakeup

Wakeup is always kernel-initiated: interrupt fires, kernel finds the waiting process, marks it TASK_RUNNING, scheduler eventually puts it on a CPU.

## Links

→ [[../Domains/04 - Linux/Theory/01 - Processes]] — full process API
→ [[../Domains/04 - Linux/Theory/02 - File Descriptors]] — fd table, kernel structures
→ [[../Domains/04 - Linux/Theory/08 - Kernel]] — kernel modes, scheduler, syscall path
→ [[../Domains/04 - Linux/Mental Models/01 - Processes — The Machine]] — process lifecycle in detail
→ [[Program Startup — The Machine]] — what exec() triggers step by step
