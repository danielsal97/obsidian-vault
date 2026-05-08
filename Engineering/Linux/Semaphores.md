# Semaphores

A semaphore is a non-negative integer counter with two atomic operations: **wait** (decrement) and **post** (increment). Threads/processes block on wait when the count is 0.

---

## POSIX Unnamed Semaphores (between threads)

```c
#include <semaphore.h>

sem_t sem;
sem_init(&sem, 0, 1);   // pshared=0 (threads only), initial value=1

// Wait (P / down / acquire):
sem_wait(&sem);         // blocks if value == 0; decrements when > 0
// ... critical section ...
sem_post(&sem);         // increment; unblocks a waiter if any

sem_destroy(&sem);
```

With initial value `1`, this behaves like a mutex (binary semaphore).  
With initial value `N`, this is a counting semaphore that allows N concurrent accessors.

---

## POSIX Named Semaphores (between processes)

```c
// Process A:
sem_t* sem = sem_open("/my_sem", O_CREAT, 0666, 1);  // create with value 1
sem_wait(sem);
// ... critical section ...
sem_post(sem);
sem_close(sem);

// Process B:
sem_t* sem = sem_open("/my_sem", 0);  // open existing
sem_wait(sem);
sem_post(sem);
sem_close(sem);

// Cleanup (one process removes the name):
sem_unlink("/my_sem");
```

Visible in `/dev/shm/` as `sem.my_sem`.

---

## Counting Semaphore — Producer/Consumer

```c
sem_t empty_slots;
sem_t filled_slots;
pthread_mutex_t lock;

// Init:
sem_init(&empty_slots, 0, BUFFER_SIZE);  // N empty slots available
sem_init(&filled_slots, 0, 0);           // 0 items available

// Producer:
sem_wait(&empty_slots);    // wait for an empty slot
pthread_mutex_lock(&lock);
// ... add item to buffer ...
pthread_mutex_unlock(&lock);
sem_post(&filled_slots);   // signal that one more item is ready

// Consumer:
sem_wait(&filled_slots);   // wait for an item
pthread_mutex_lock(&lock);
// ... remove item from buffer ...
pthread_mutex_unlock(&lock);
sem_post(&empty_slots);    // signal that one slot is freed
```

This is the classic bounded-buffer problem. Two semaphores track slot counts; a mutex protects the actual buffer access.

---

## Non-blocking Try

```c
int ret = sem_trywait(&sem);  // returns -1 (EAGAIN) instead of blocking
if (ret == -1 && errno == EAGAIN) {
    // semaphore was 0 — did not acquire
}
```

Timed wait:
```c
struct timespec ts;
clock_gettime(CLOCK_REALTIME, &ts);
ts.tv_sec += 2;   // timeout in 2 seconds
int ret = sem_timedwait(&sem, &ts);
```

---

## Semaphore vs Mutex

| | Mutex | Binary Semaphore |
|---|---|---|
| Ownership | Yes — only the locker can unlock | No ownership — anyone can post |
| Use case | Protect a critical section | Signal between threads |
| Recursive | Optional (`PTHREAD_MUTEX_RECURSIVE`) | No |
| Priority inheritance | Yes (some implementations) | No |

**Key difference:** a mutex must be unlocked by the same thread that locked it. A semaphore can be posted by a *different* thread than the one that waited. This makes semaphores the right tool for producer/consumer signaling.

---

## System V Semaphores (Legacy)

Older, more complex API. Prefer POSIX.

```c
int semid = semget(IPC_PRIVATE, 1, IPC_CREAT | 0666);
struct sembuf op = {0, -1, 0};   // wait
semop(semid, &op, 1);
op.sem_op = 1;                   // post
semop(semid, &op, 1);
semctl(semid, 0, IPC_RMID);     // remove
```

---

## Common Pitfalls

**Forgetting to post on error paths:**
```c
sem_wait(&sem);
if (error) return;      // BAD — semaphore stays at 0, future waiters block forever
sem_post(&sem);
```

**Double post:** initializing with 1 then posting again without waiting — count becomes 2, allows two concurrent accessors.

**Named semaphore leak:** if process crashes after `sem_open` but before `sem_unlink`, the semaphore persists in `/dev/shm` until manually removed.

---

## C++ Wrappers

C++11 does not have a `std::semaphore`. C++20 adds `<semaphore>`:

```cpp
#include <semaphore>
std::counting_semaphore<10> sem(0);  // max value 10, initial 0
sem.release();    // post
sem.acquire();    // wait (blocks)
```

Before C++20, use `std::mutex` + `std::condition_variable` for the same effect.

---

## Related Notes

- [[Threads - pthreads]] — mutex and condition variables
- [[Shared Memory]] — shared memory that needs semaphore coordination
- [[IPC Overview]] — where semaphores fit among IPC mechanisms

---

## Understanding Check

> [!question]- Why is a semaphore the right synchronization primitive for producer/consumer, while a mutex alone is not sufficient?
> A mutex protects a critical section by ensuring mutual exclusion — it answers "who has access right now." But a producer/consumer also needs to answer "is there work available / is there space?" A mutex cannot express that: if the consumer locks the mutex and finds the buffer empty, it must unlock and busy-wait or sleep externally. A counting semaphore directly encodes the count of available items or slots as its value, and sem_wait blocks the consumer efficiently until the count is nonzero. You still need a mutex to protect the actual buffer manipulation, but the semaphore handles the signaling.

> [!question]- What goes wrong if you forget to call sem_post on an error path inside a sem_wait critical section?
> The semaphore value stays decremented and is never restored. Any other thread or process waiting on sem_wait will block forever — a permanent deadlock. This is a common bug because the error path is often an early return added after the fact, and the developer forgets the cleanup. The pattern mirrors mutex unlock on error: use a goto cleanup label in C, or RAII wrappers in C++ to guarantee the post always runs. Named semaphores are especially dangerous here because if the process crashes after sem_wait without sem_post, the semaphore value persists in /dev/shm until manually fixed.

> [!question]- What is the key behavioral difference between a mutex and a binary semaphore that makes semaphores dangerous for mutual exclusion?
> A mutex has ownership: only the thread that locked it can unlock it. This enables priority inheritance (the kernel can temporarily boost a low-priority locker's priority to prevent priority inversion) and prevents a bug where one thread inadvertently releases another thread's lock. A binary semaphore has no ownership — any thread can call sem_post regardless of which thread called sem_wait. This makes it easy to accidentally release the "lock" from an unrelated code path, allowing two threads into the critical section simultaneously. For mutual exclusion, always use a mutex; use semaphores only for signaling.

> [!question]- In the LDS watchdog, sem_timedwait is used rather than sem_wait — why does an infinite wait break the watchdog logic?
> The guardian must detect when the main process has died and stopped sending SIGUSR1 heartbeats. If it called sem_wait with no timeout, it would block indefinitely waiting for a signal that will never come (because the main process is dead). sem_timedwait adds a deadline: if no signal arrives within ~15 seconds, the call returns ETIMEDOUT and the guardian concludes the main process is dead, triggering a fork+exec restart. An infinite wait would make the watchdog useless — a dead main process would never be restarted.

> [!question]- What happens to a named semaphore in /dev/shm if a process crashes after sem_open but before sem_unlink?
> The semaphore object persists in /dev/shm indefinitely — the kernel does not automatically clean it up on process exit the way it cleans up anonymous memory. The next time the program runs and calls sem_open with O_CREAT, it will open the existing stale semaphore with whatever value it had at crash time (possibly 0 if the crash happened inside a critical section). This can immediately deadlock the new process. The fix is to either always call sem_unlink before sem_open with O_CREAT, or handle EEXIST explicitly and decide whether to unlink and recreate or reuse the existing semaphore.
