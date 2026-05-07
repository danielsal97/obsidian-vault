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
