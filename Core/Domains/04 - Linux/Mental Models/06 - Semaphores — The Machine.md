# Semaphores — The Machine

## The Model
A parking lot with a counter above the entrance. The counter shows available spaces. `wait()` decrements it — if it reaches zero, you stop at the entrance until a space opens. `post()` increments it — if someone was waiting, one car enters. A binary semaphore (counter = 1) is a key on a hook: either available or not.

## How It Moves

```
Counting semaphore (N=3 — allow 3 simultaneous readers):

sem_init(&sem, 0, 3)    counter = 3

Thread A: sem_wait()    counter = 2  ← enters
Thread B: sem_wait()    counter = 1  ← enters
Thread C: sem_wait()    counter = 0  ← enters
Thread D: sem_wait()    counter = 0  ← BLOCKS (no space)
Thread A: sem_post()    counter = 1  ← Thread D unblocks, enters

Binary semaphore (N=1) = mutex equivalent:
sem_wait() → enter critical section
sem_post() → leave critical section
```

**Semaphore vs Mutex:**
- Mutex: owned by a thread — only the locking thread can unlock it
- Semaphore: not owned — any thread (or process) can post it
- Semaphore works ACROSS PROCESSES; `std::mutex` does not
- Semaphore can be used to signal (producer posts, consumer waits — no shared ownership)

## The Blueprint

```c
#include <semaphore.h>

// Unnamed (same process / shared memory):
sem_t sem;
sem_init(&sem, 0, 1);     // 2nd arg: 0=threads, 1=processes; 3rd: initial value
sem_wait(&sem);           // decrement; blocks if 0
sem_post(&sem);           // increment; wakes one waiter
sem_destroy(&sem);

// Named (across unrelated processes):
sem_t* s = sem_open("/lds_sem", O_CREAT, 0600, 1);
sem_wait(s);
sem_post(s);
sem_close(s);
sem_unlink("/lds_sem");   // remove name
```

**Producer-Consumer with semaphore:**
```c
sem_t empty, full;
sem_init(&empty, 0, BUFFER_SIZE);   // N empty slots
sem_init(&full,  0, 0);             // 0 full slots

// Producer:           Consumer:
sem_wait(&empty);      sem_wait(&full);
put(item);             get(item);
sem_post(&full);       sem_post(&empty);
```

## Where It Breaks

- **Forgetting `sem_post`**: threads pile up at `sem_wait` indefinitely — semaphore deadlock
- **`sem_post` without matching `sem_wait`**: counter grows unbounded — eventually another process gets access it shouldn't
- **Named semaphore not unlinked**: persists in `/dev/shm` after process exit

## In LDS

LDS uses `std::mutex` + `std::condition_variable` for the ThreadPool (same-process coordination). If LDS were extended to coordinate with minion processes via shared memory, `sem_t` with `pshared=1` (initialized in the shared memory region itself) would be the synchronization mechanism. The `sem_post` after writing a block to shared memory is the signal to the minion that data is ready to process.

## Validate

1. A semaphore is initialized to 0. Thread A calls `sem_wait`. What happens? Thread B then calls `sem_post`. Now what happens?
2. You use a binary semaphore as a mutex. Thread A calls `sem_wait` to enter a critical section, then crashes. Thread B calls `sem_wait` and blocks forever. Why does a real mutex not have this problem?
3. LDS has a shared memory buffer shared between manager and minion. Manager writes a 512-byte block, then calls `sem_post`. Minion calls `sem_wait`, then reads. Is there a race condition? What CPU guarantee do you need?

## Connections

**Theory:** [[06 - Semaphores]]  
**Mental Models:** [[Threads and pthreads — The Machine]], [[Shared Memory — The Machine]], [[Memory Ordering — The Machine]]  
**LDS Implementation:** [[LDS/Architecture/Concurrency Model]] — future shared-memory extension  
**Glossary:** [[pthreads]]
