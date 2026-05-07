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
