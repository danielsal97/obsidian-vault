# Multithreading Patterns

Common patterns for structuring concurrent work safely and efficiently.

---

## Thread Pool

A fixed set of worker threads process tasks from a shared queue. Avoids the overhead of creating/destroying threads for each task.

```cpp
class ThreadPool {
    std::vector<std::thread> m_workers;
    std::queue<std::function<void()>> m_tasks;
    std::mutex m_mutex;
    std::condition_variable m_cv;
    bool m_stop = false;

public:
    explicit ThreadPool(size_t n) {
        for (size_t i = 0; i < n; ++i) {
            m_workers.emplace_back([this] {
                while (true) {
                    std::function<void()> task;
                    {
                        std::unique_lock<std::mutex> lk(m_mutex);
                        m_cv.wait(lk, [this] { return m_stop || !m_tasks.empty(); });
                        if (m_stop && m_tasks.empty()) return;
                        task = std::move(m_tasks.front());
                        m_tasks.pop();
                    }
                    task();   // execute outside the lock
                }
            });
        }
    }

    void submit(std::function<void()> task) {
        {
            std::lock_guard<std::mutex> lk(m_mutex);
            m_tasks.push(std::move(task));
        }
        m_cv.notify_one();
    }

    ~ThreadPool() {
        { std::lock_guard<std::mutex> lk(m_mutex); m_stop = true; }
        m_cv.notify_all();
        for (auto& t : m_workers) t.join();
    }
};
```

LDS uses `ThreadPool` + `WPQ` for this. See [[../Design Patterns/Command]] — work items are command objects (or lambdas).

---

## Producer / Consumer

One or more producers create work; one or more consumers process it. A bounded queue between them prevents producers from outrunning consumers.

```cpp
// Using semaphores (see Linux/Semaphores):
sem_t empty;  // tracks empty slots
sem_t filled; // tracks filled slots
std::mutex m;
Item buffer[N];
int in = 0, out = 0;

// Producer:
sem_wait(&empty);          // wait for space
{ std::lock_guard lk(m); buffer[in] = item; in = (in+1) % N; }
sem_post(&filled);         // signal item available

// Consumer:
sem_wait(&filled);         // wait for item
{ std::lock_guard lk(m); item = buffer[out]; out = (out+1) % N; }
sem_post(&empty);          // signal slot freed
```

---

## Lock Hierarchy — Preventing Deadlock

Always acquire locks in the same order, everywhere.

```cpp
// Two mutexes: always lock A before B:
void transfer(Account& a, Account& b, int amount) {
    std::lock(a.m_mutex, b.m_mutex);   // acquires both atomically — no deadlock
    std::lock_guard<std::mutex> lk_a(a.m_mutex, std::adopt_lock);
    std::lock_guard<std::mutex> lk_b(b.m_mutex, std::adopt_lock);
    a.balance -= amount;
    b.balance += amount;
}
```

`std::lock(m1, m2)` uses a deadlock-avoidance algorithm. Alternatively, always sort mutexes by address before locking.

---

## Double-Checked Locking — Safe Version

Lazy initialization of a shared object:

```cpp
std::mutex m;
std::atomic<Config*> g_config{nullptr};

Config* get_config() {
    Config* cfg = g_config.load(std::memory_order_acquire);
    if (!cfg) {
        std::lock_guard<std::mutex> lk(m);
        cfg = g_config.load(std::memory_order_relaxed);
        if (!cfg) {
            cfg = new Config();
            g_config.store(cfg, std::memory_order_release);
        }
    }
    return cfg;
}
```

The `acquire`/`release` ordering ensures that the Config object is fully written before any thread reads it through the pointer. See [[Memory Ordering]] for why this matters.

The simple version (`static Config inst;`) in C++11 is also thread-safe and preferred.

---

## Reader-Writer Lock

Many readers, one writer:

```cpp
std::shared_mutex rw;

// Readers (many can run simultaneously):
{
    std::shared_lock<std::shared_mutex> lk(rw);
    // ... read shared data ...
}

// Writer (exclusive):
{
    std::unique_lock<std::shared_mutex> lk(rw);
    // ... modify shared data ...
}
```

`std::shared_mutex` is in C++17. For C++14, use `pthread_rwlock_t`.

---

## Active Object

Wraps a worker thread inside an object. The object's public methods enqueue work; the private thread processes it. Caller is never blocked.

```cpp
class AsyncLogger {
    std::thread m_thread;
    std::queue<std::string> m_queue;
    std::mutex m_mutex;
    std::condition_variable m_cv;
    bool m_stop = false;

public:
    AsyncLogger() : m_thread([this] { run(); }) {}

    void log(const std::string& msg) {
        { std::lock_guard lk(m_mutex); m_queue.push(msg); }
        m_cv.notify_one();
    }

private:
    void run() {
        while (true) {
            std::string msg;
            {
                std::unique_lock lk(m_mutex);
                m_cv.wait(lk, [this] { return m_stop || !m_queue.empty(); });
                if (m_stop && m_queue.empty()) return;
                msg = std::move(m_queue.front());
                m_queue.pop();
            }
            std::cout << msg << "\n";
        }
    }
};
```

---

## Futures and Promises

Decouple the result of a computation from when it finishes:

```cpp
std::promise<int> p;
std::future<int> f = p.get_future();

std::thread t([&p] {
    int result = expensive_compute();
    p.set_value(result);
});

// Later, block until result is ready:
int val = f.get();   // blocks if not ready yet
t.join();
```

`std::async` wraps this pattern:
```cpp
auto f = std::async(std::launch::async, expensive_compute);
int val = f.get();   // get result when needed
```

---

## Common Pitfalls

| Bug | Cause | Fix |
|---|---|---|
| Race condition | Unsynchronized access to shared state | Mutex or atomic |
| Deadlock | Two threads each wait for a lock the other holds | Lock ordering, `std::lock` |
| Livelock | Threads keep backing off and retrying forever | Randomized backoff |
| Spurious wakeup | `cond_wait` returns without a signal | Always use `while (!cond)` |
| Lock granularity | Holding lock too long | Do work outside lock, lock only the data |

---

## Related Notes

- [[Memory Ordering]] — atomics and happens-before
- [[../Linux/Threads - pthreads]] — pthread API
- [[../Linux/Semaphores]] — producer/consumer with semaphores
- [[../Design Patterns/Reactor]] — single-threaded event loop alternative
- [[../Design Patterns/Command]] — work items in thread pool

---

## Understanding Check

> [!question]- Why does the ThreadPool execute tasks outside the mutex lock, and what would go wrong if the lock were held during task()?
> The mutex protects the shared queue — it should be held only long enough to dequeue the next task. If the lock were held during task() execution, only one worker thread could run at a time regardless of pool size, defeating the entire purpose of having multiple workers. Worse, if the task itself tries to submit new work to the pool (a common pattern), it would attempt to acquire the same mutex on the same thread — a self-deadlock. Releasing the lock before calling task() allows all worker threads to execute their tasks concurrently while the mutex is only contended during brief queue operations.

> [!question]- What is a spurious wakeup in condition variables, and what goes wrong in the LDS ThreadPool if the wait loop uses if (!cond) instead of while (!cond)?
> A spurious wakeup is when a thread wakes from condition_variable::wait() without notify_one() or notify_all() having been called — the OS is permitted to do this for implementation reasons on some platforms. If the worker uses if (m_stop || !m_tasks.empty()) { ... process ... } instead of while (...) { ... wait ... }, a spurious wakeup would fall through with an empty queue, and the worker would call m_tasks.front() on an empty queue — undefined behavior (dequeue from empty container, likely a crash). The while loop re-checks the condition and goes back to sleep if it's still false, correctly handling spurious wakeups.

> [!question]- In the double-checked locking pattern, why is the first load (outside the lock) memory_order_acquire and not memory_order_relaxed?
> If the outer load used relaxed ordering, a thread could observe the pointer as non-null (set by the initializing thread) but the Config object it points to might not yet be fully visible — the CPU is free to reorder the store to the pointer before the stores to Config's members. The thread would dereference a valid-looking non-null pointer but read uninitialized or partially written fields. acquire ordering on the load creates a happens-before relationship with the release store: all writes the initializing thread made to Config before the release-store of the pointer are guaranteed to be visible to any thread that sees the pointer as non-null via an acquire-load.

> [!question]- What is false sharing and how could it affect LDS's ThreadPool worker threads if each thread tracks its own "tasks processed" counter in a shared array?
> False sharing occurs when two threads write to different variables that happen to occupy the same CPU cache line (typically 64 bytes). Each write forces the cache line to be invalidated on the other core, which must fetch the updated line before its next access — even though the two threads are modifying completely different memory locations. If LDS had struct { int count; } worker_stats[N] where N workers each increment worker_stats[i].count, all counts fit in one or two cache lines. Every increment by any worker invalidates the line for all other workers, serializing what should be independent operations. The fix is alignas(64) struct { int count; } worker_stats[N] — padding each counter to its own cache line.

> [!question]- Why does the Reader-Writer Lock pattern benefit LDS's configuration or routing-table scenarios, and when would it be wrong to use it?
> A shared_mutex allows many readers simultaneously as long as no writer holds the lock. For LDS scenarios like a routing table mapping minion IDs to addresses (read on every block operation, updated rarely when a minion joins/leaves), a reader-writer lock gives far higher throughput than a plain mutex — hundreds of concurrent reads proceed without blocking each other. Using it is wrong when writes are frequent or when the critical section is so short that the overhead of shared_mutex (heavier than mutex) exceeds the benefit of concurrency. It's also wrong when readers perform writes on the protected data (e.g., lazy initialization inside a "read" path) — that requires exclusive access and using shared_lock would be a data race.
