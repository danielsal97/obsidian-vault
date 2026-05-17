# Linux — Hub

The OS interface: processes, file descriptors, signals, and kernel interaction.

## Place in Runtime

```
exec() → address space → threads → scheduler → fd table → signals
```

→ [[Linux Runtime — The Machine]] — all 6 subsystems simultaneously (start here)
→ [[00 - VAULT MAP]] — vault root
→ [[Core/00 START HERE|Core Start Here]]

## The Machine

- [[01 - Processes — The Machine]] — fork/exec lifecycle, COW pages, address space setup
- [[02 - File Descriptors — The Machine]] — kernel fd table, open file table, inode
- [[03 - Signals — The Machine]] — signal delivery, pending mask, async-signal-safety
- [[04 - Threads and pthreads — The Machine]] — clone() syscall, new kernel stack, scheduler context
- [[10 - Context Switch — The Machine]] — timer interrupt, save RIP/RSP/GPRs, pick_next_task
- [[11 - Scheduler — The Machine]] — CFS vruntime, TIF_NEED_RESCHED, nice weights
- [[05 - Shared Memory — The Machine]] — shm_open, mmap MAP_SHARED, kernel page table
- [[08 - mmap — The Machine]] — file-backed vs anonymous, page fault on first access

## Theory

- [[01 - Processes]] — fork(), exec(), wait(), zombie, daemon process
- [[02 - File Descriptors]] — everything is an fd: files, sockets, pipes, timers
- [[03 - Signals]] — sigaction, async-signal-safety, signalfd, SIGPIPE
- [[04 - Threads - pthreads]] — pthread_create, mutex, condition variable, TLS
- [[05 - Shared Memory]] — shm_open, mmap MAP_SHARED, synchronization
- [[06 - Semaphores]] — counting semaphore, sem_wait/post, producer/consumer
- [[07 - mmap]] — file-backed vs anonymous mapping, MAP_PRIVATE vs MAP_SHARED
- [[09 - Context Switch]] — timer interrupt, register save/restore, pick_next_task
- [[10 - Scheduler]] — CFS vruntime, nice weights, TIF_NEED_RESCHED

## Interview Q&A

- [[01 - Linux Q&A]] — fork/exec, signals, file descriptors, mmap, inotify

## Glossary

[[17 - pthreads]] · [[15 - VFS]]
