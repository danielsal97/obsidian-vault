# Threads — pthreads

A thread is a lightweight execution unit within a process. All threads share the same address space, file descriptors, and global variables. Each thread has its own stack and registers.

---

## Creating Threads

```c
#include <pthread.h>

void* worker(void* arg) {
    int* val = (int*)arg;
    printf("thread received: %d\n", *val);
    return NULL;
}

int main() {
    pthread_t tid;
    int data = 42;

    pthread_create(&tid, NULL, worker, &data);  // create thread
    pthread_join(tid, NULL);                     // wait for it to finish
    return 0;
}
```

Compile with `-lpthread`.

---

## Mutex — Mutual Exclusion

Prevents two threads from accessing shared data simultaneously.

```c
pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

void safe_increment() {
    pthread_mutex_lock(&lock);
    counter++;                       // critical section
    pthread_mutex_unlock(&lock);
}
```

**Rules:**
- Lock before accessing shared state, unlock immediately after
- Never hold a lock while blocking (I/O, sleep) — causes starvation
- Acquire multiple locks in the same order everywhere — prevents deadlock

---

## Condition Variable

A thread waits for a condition to become true without spinning.

```c
pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t  cond = PTHREAD_COND_INITIALIZER;
int ready = 0;

// Consumer thread:
pthread_mutex_lock(&lock);
while (!ready) {                          // always loop — spurious wakeups
    pthread_cond_wait(&cond, &lock);      // atomically: unlock + sleep
}
// ready == 1 here, lock is held again
pthread_mutex_unlock(&lock);

// Producer thread:
pthread_mutex_lock(&lock);
ready = 1;
pthread_cond_signal(&cond);               // wake one waiter
// or: pthread_cond_broadcast(&cond);     // wake all waiters
pthread_mutex_unlock(&lock);
```

`pthread_cond_wait` atomically releases the mutex and blocks. When signaled, it re-acquires the mutex before returning.

---

## Thread-Local Storage

Each thread gets its own copy of the variable:

```c
__thread int errno_copy;          // C99 TLS
thread_local int counter = 0;    // C++11 TLS
```

`errno` is thread-local in POSIX — each thread has its own error code.

---

## Thread Attributes

```c
pthread_attr_t attr;
pthread_attr_init(&attr);

// Detached thread — no need to join, resources freed automatically:
pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);

// Stack size:
pthread_attr_setstacksize(&attr, 1024 * 1024);   // 1 MB stack

pthread_create(&tid, &attr, worker, NULL);
pthread_attr_destroy(&attr);
```

---

## Cancellation

```c
// In the thread: set up a cleanup handler
pthread_cleanup_push(cleanup_fn, arg);
// ... work ...
pthread_cleanup_pop(1);   // 1 = run cleanup

// From another thread:
pthread_cancel(tid);      // request cancellation
```

Cancellation is tricky — prefer signaling a shutdown flag instead.

---

## Read-Write Lock

Multiple readers can hold simultaneously; writers get exclusive access.

```c
pthread_rwlock_t rwlock = PTHREAD_RWLOCK_INITIALIZER;

// Reader:
pthread_rwlock_rdlock(&rwlock);
// ... read shared data ...
pthread_rwlock_unlock(&rwlock);

// Writer:
pthread_rwlock_wrlock(&rwlock);
// ... modify shared data ...
pthread_rwlock_unlock(&rwlock);
```

Good for data that is read often and written rarely.

---

## Common Bugs

**Race condition:**
```c
// Thread 1 and Thread 2 both run:
if (counter < MAX) counter++;   // read-check-increment is not atomic — data race
```

**Deadlock:**
```c
// Thread A: lock(m1), lock(m2)
// Thread B: lock(m2), lock(m1)   — circular wait → deadlock
```

**Spurious wakeup — missing while loop:**
```c
// Wrong:
pthread_cond_wait(&cond, &lock);
// use data immediately — but cond_wait can return without a signal

// Correct: always re-check the condition
while (!ready) pthread_cond_wait(&cond, &lock);
```

---

## C++11 Threads

C++11 wraps pthreads:

```cpp
#include <thread>
#include <mutex>
#include <condition_variable>

std::mutex m;
std::thread t([]{ 
    std::lock_guard<std::mutex> lk(m);
    // ... 
});
t.join();
```

See [[../C++/C++11/Overview]] — `std::thread`, `std::mutex`, `std::condition_variable`, `std::lock_guard`, `std::unique_lock` were all added in C++11.

---

## LDS Context

LDS uses a thread pool (`ThreadPool` + `WPQ`) where:
- One thread dispatches work items to the queue
- Worker threads pull from `WPQ` and execute read/write operations
- `LocalStorage` requires a mutex because multiple workers can hit it simultaneously (Bug #10: static mutex issue in ThreadPool)

The `LocalStorage` mutex pattern:
```cpp
std::lock_guard<std::mutex> lk(m_mutex);
// ... access m_storage ...
```

---

## Understanding Check

> [!question]- Why must pthread_cond_wait always be called inside a while loop, not an if statement?
> POSIX allows spurious wakeups — pthread_cond_wait can return even when no thread called pthread_cond_signal or pthread_cond_broadcast. This is permitted by the standard to allow efficient implementation on certain hardware. If you use an if, you proceed with the assumption the condition is true when it may not be. The while loop re-checks the predicate after every wakeup and goes back to sleep if it is still false, making the code correct regardless of spurious wakeups.

> [!question]- What goes wrong if two threads always acquire the same two mutexes in opposite orders?
> This creates a classic circular-wait deadlock. Thread A holds mutex 1 and waits for mutex 2; Thread B holds mutex 2 and waits for mutex 1. Neither can proceed. The system does not detect or resolve this — both threads are blocked forever. The fix is a strict global lock ordering: every thread must acquire mutex 1 before mutex 2, always. Alternatively, use std::scoped_lock (C++17) which acquires multiple mutexes deadlock-free using a consistent internal ordering algorithm.

> [!question]- In LDS, LocalStorage was initially implemented with a static mutex — why was that a bug?
> A static mutex is shared across all instances of a class. If the ThreadPool creates multiple LocalStorage objects (or if LocalStorage is used in multiple contexts), all of them serialize on the same lock even when accessing completely independent storage. This creates unnecessary contention and, more critically, was Bug #10: the static mutex was initialized once but could be destroyed and re-initialized across test runs, causing undefined behavior. The fix is an instance-level mutex (a member variable) so each LocalStorage object has its own lock.

> [!question]- Why does holding a mutex while performing blocking I/O cause starvation, and how would this affect LDS worker threads?
> If a thread holds a mutex and then blocks on a read() or network call, it holds the lock for the entire I/O duration — potentially milliseconds or seconds. Every other thread that needs the same lock is completely blocked during that time, even if their work is unrelated to the I/O. In LDS's thread pool, if a worker held m_mutex on LocalStorage while waiting for a slow disk read, all other workers trying to read/write storage would be serialized behind that one I/O, eliminating any concurrency benefit from the thread pool.

> [!question]- What is the difference between a detached thread and a joined thread, and what leak occurs if you neither join nor detach?
> A joined thread's resources (stack, thread-local storage, thread descriptor) are released by the joining thread when pthread_join returns. A detached thread releases its own resources when it exits. If you neither join nor detach a thread, its resources are never freed — they accumulate as a memory leak similar to zombie processes. The thread descriptor stays allocated until the process exits. In a long-running server that spawns many short-lived threads, this eventually exhausts system thread limits.
