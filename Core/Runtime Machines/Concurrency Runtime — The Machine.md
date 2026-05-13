# Concurrency Runtime — The Machine

## The Model

A thread is a kernel-scheduled execution context. It has its own stack, its own registers, its own program counter — but shares the heap and global data with all other threads in the process. The kernel switches between threads on timer interrupt, on blocking syscall, or when a thread explicitly yields. You don't control when you're preempted. That's why every shared write needs protection.

## How It Moves — Thread Pool with Work Queue

```
Producer thread (Reactor) has work to dispatch:
  post(lambda):
  → lock WPQ mutex
  → push lambda onto queue
  → unlock WPQ mutex
  → sem_post(&semaphore)   // wake one waiting worker
      │
      ▼
Worker thread was blocked on sem_wait():
  → kernel: semaphore count > 0, decrement, wake thread
  → thread runs: lock WPQ mutex, pop lambda, unlock mutex
  → execute lambda (the actual work)
  → loop back to sem_wait() — sleep until next item
```

## How It Moves — Mutex Contention

```
Thread A holds mutex M
Thread B calls pthread_mutex_lock(&M):
      │
      ▼
futex user-space fast path:
  → atomically check lock word: locked (thread A's ID)
  → fast path fails: must go to kernel
      │
      ▼
futex syscall (FUTEX_WAIT):
  → kernel: verify lock still held (atomically)
  → add thread B to futex wait queue
  → mark thread B TASK_INTERRUPTIBLE
  → context switch away — thread B is now sleeping
      │
      ▼
Thread A calls pthread_mutex_unlock(&M):
  → atomically clear lock word
  → check if any waiters (kernel fast path check)
  → if yes: futex syscall (FUTEX_WAKE) → wake one waiter
      │
      ▼
Thread B wakes:
  → kernel: mark TASK_RUNNING
  → scheduler: thread B gets CPU when available
  → thread B acquires mutex (retry atomic lock)
```

## What "Memory Visible to Another Thread" Means

Writes are NOT immediately visible to other threads. The CPU has its own write buffer; data may sit there before hitting L3 cache and being visible globally.

`pthread_mutex_unlock()` includes a release fence: all writes before the unlock are flushed and globally visible BEFORE the unlock is seen. `pthread_mutex_lock()` includes an acquire fence: all reads after the lock see writes that were flushed before the corresponding unlock.

This is why the mutex protects not just atomicity but VISIBILITY.

## Where Threads Block

| Situation | Kernel mechanism |
|---|---|
| `sem_wait()` with count=0 | futex FUTEX_WAIT |
| `pthread_mutex_lock()` contended | futex FUTEX_WAIT |
| `pthread_cond_wait()` | futex + cond var queue |
| `epoll_wait()` no events | epoll wait queue |
| `read()` empty socket | socket wait queue |
| `usleep()` / `nanosleep()` | hrtimer |

## Links

→ [[../Domains/05 - Concurrency/Theory/01 - Multithreading Patterns]] — thread pool, WPQ, producer/consumer
→ [[../Domains/05 - Concurrency/Theory/02 - Memory Ordering]] — acquire/release, happens-before
→ [[../Domains/04 - Linux/Theory/04 - Threads - pthreads]] — pthreads API
→ [[../Domains/04 - Linux/Theory/06 - Semaphores]] — counting semaphore
→ [[../Domains/05 - Concurrency/Mental Models/01 - Multithreading Patterns — The Machine]]
→ [[../Domains/05 - Concurrency/Mental Models/02 - Memory Ordering — The Machine]]
