---
name: pthreads — POSIX Threads
type: linux-api
---

# pthreads — POSIX Threads

**[man page →](https://man7.org/linux/man-pages/man7/pthreads.7.html)** | **[Wikipedia →](https://en.wikipedia.org/wiki/Pthreads)**

The standard C/POSIX threading API on Linux. Provides thread creation, mutexes, condition variables, and synchronization primitives. The foundation that all higher-level concurrency in LDS is built on.

## Core Primitives Used in LDS

| Primitive | API | Used For |
|-----------|-----|----------|
| Thread | `pthread_create` / `pthread_join` | ThreadPool workers, ResponseManager receiver |
| Mutex | `pthread_mutex_lock/unlock` | Protecting shared data (callback maps, minion registry) |
| Condition variable | `pthread_cond_wait/signal` | WPQ blocking workers until work arrives |
| Atomic | `std::atomic<T>` (C++11, wraps hardware atomics) | Singleton double-checked locking |

## In LDS — Thread Count

```
Main thread       — epoll loop (Reactor), never blocks on I/O
Worker threads    — N threads in ThreadPool, execute Commands
Recv thread       — 1 thread in ResponseManager, blocks on recvfrom(UDP)
Watchdog thread   — 1 background thread, pings minions every 5s
Discovery thread  — 1 background thread, listens for minion broadcasts
─────────────────────────��───────────────────────────
Total:   N + 4 threads (N = hardware_concurrency)
```

## C++11 Wrappers

LDS uses the C++ standard library wrappers (`std::thread`, `std::mutex`, `std::condition_variable`) rather than raw pthreads, but they compile to the same pthreads calls on Linux.

## Connections

**Theory:** [[04 - Threads - pthreads]]  
**Mental Models:** [[Threads and pthreads — The Machine]], [[Multithreading Patterns — The Machine]], [[Memory Ordering — The Machine]]  
**LDS Implementation:** [[Utilities Framework]] — ThreadPool + WPQ; [[Threading Deep Dive]]; [[LDS/Architecture/Concurrency Model]]  
**Runtime Machines:** [[ThreadPool and WPQ — The Machine]]  
**Related Glossary:** [[WPQ]]
