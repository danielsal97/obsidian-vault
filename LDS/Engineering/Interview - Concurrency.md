# Interview — Concurrency & Threading

Questions about threads, synchronization, and the bugs you fixed in LDS.

---

## Threads — the basics

**Q: What is a thread? How does it differ from a process?**

A thread is an independent execution context sharing the same address space as its siblings. A process is an independent address space. Threads are cheaper to create and share memory; processes are isolated (crash in one doesn't affect another).

```cpp
std::thread t([]{ doWork(); });
t.join();   // wait for t to finish
// t.detach() — let it run independently, no join needed (but no way to know when done)
```

**Where is this in LDS?**  
`ThreadPool` manages a fixed pool of `std::thread` workers. `NBDDriverComm` runs the kernel do_it loop in a detached thread. Watchdog (`ds/`) calls `pthread_detach` explicitly — the watchdog thread lives until the process exits.

---

## Mutex — types and when to use each

**Q: What is a mutex? What types exist in C++?**

| Type | When to use |
|---|---|
| `std::mutex` | Default — exclusive access |
| `std::shared_mutex` | Many readers, few writers — readers share, writers block all |
| `std::recursive_mutex` | Same thread needs to lock again without deadlock (usually a design smell) |
| `std::timed_mutex` | Need a try-lock with timeout |

**Q: What is the difference between `lock_guard` and `unique_lock`?**

`lock_guard` — RAII wrapper. Locks on construction, unlocks on destruction. Cannot be manually unlocked. Simple.

`unique_lock` — Flexible RAII wrapper. Can be manually unlocked and relocked. Required for `condition_variable`. Slightly heavier.

```cpp
{
    std::lock_guard<std::mutex> lock(m_mutex);    // simple case
    m_data.push_back(x);
}   // unlocked here

{
    std::unique_lock<std::mutex> lock(m_mutex);   // needed for cv
    m_cv.wait(lock, [&]{ return !m_queue.empty(); });
    auto item = m_queue.front();
    m_queue.pop();
}
```

**Where is this in LDS?**  
`LocalStorage` uses `std::shared_mutex` with `std::shared_lock` for reads and `std::unique_lock` for writes — concurrent reads are safe and fast; writes are exclusive. `ThreadPool` uses `std::mutex` + `std::unique_lock` for the wait queue.

---

## Race Conditions — what they are and examples from LDS

**Q: What is a race condition?**

Two threads access shared data with at least one write, and the outcome depends on scheduling order. Undefined behavior in C++.

**LDS Bug #8 — Dispatcher race (use-after-free on vector reallocation):**

```cpp
// Dispatcher<Msg>: m_subs is std::vector<ICallBack<Msg>*>
// Thread 1: Dispatcher::Notify() iterates m_subs
// Thread 2: Dispatcher::Register() calls m_subs.push_back()
// push_back may trigger reallocation → Thread 1 has a dangling pointer → crash
```

Fix: add `std::shared_mutex` to `Dispatcher`. `Notify` holds shared lock (read), `Register`/`UnRegister` hold exclusive lock (write).

**LDS Bug #10 — ThreadPool static mutex/cv:**

```cpp
// utilities/threading/thread_pool/include/thread_pool.hpp lines 61-62
static std::mutex m_mutex;           // BUG: shared across ALL ThreadPool instances
static std::condition_variable m_cv; // BUG: one pool's signal wakes the other

// Fix: remove 'static' — each pool instance owns its own mutex and cv
```

If you had two ThreadPools, a shutdown signal on Pool A could wake Pool B's workers, causing spurious work or corrupted state.

---

## Condition Variables

**Q: What is a condition variable? How do you use it correctly?**

A condition variable lets threads block until a condition is true, without busy-waiting.

```cpp
std::mutex m;
std::condition_variable cv;
std::queue<int> q;

// Producer
{
    std::lock_guard<std::mutex> lock(m);
    q.push(42);
}
cv.notify_one();

// Consumer
{
    std::unique_lock<std::mutex> lock(m);
    cv.wait(lock, [&]{ return !q.empty(); });  // lambda: predicate
    auto x = q.front(); q.pop();
}
```

**Q: What is a spurious wakeup?**

A condition variable can wake even when no `notify` was called (OS-level behavior). This is why you must always use a predicate — the lambda in `cv.wait(lock, pred)` re-checks the condition and goes back to sleep if it's still false.

**Where is this in LDS?**  
`ThreadPool` workers call `m_cv.wait(lock, pred)` — they sleep when the queue is empty and wake when a task is pushed. The predicate is `[&]{ return !m_queue.empty() || m_stop; }`.

---

## Deadlock

**Q: What is a deadlock? How do you prevent it?**

Deadlock: Thread A holds Lock 1 and waits for Lock 2. Thread B holds Lock 2 and waits for Lock 1. Neither proceeds.

**Prevention:**
1. **Lock ordering** — always acquire locks in the same global order
2. **`std::lock(m1, m2)`** — acquires multiple locks atomically, avoids ordering issues
3. **RAII with try-lock and backoff** — if you can't get lock 2, release lock 1 and retry
4. **Avoid holding locks while calling external code**

```cpp
// Safe: lock both atomically
std::unique_lock<std::mutex> l1(m1, std::defer_lock);
std::unique_lock<std::mutex> l2(m2, std::defer_lock);
std::lock(l1, l2);
```

---

## `std::atomic`

**Q: When do you use `atomic` instead of a mutex?**

`atomic<T>` is for a single value that needs lock-free read-modify-write. Uses CPU instructions (compare-and-swap, fetch-add) — no OS involvement, no context switch.

Use `atomic<bool>` for a stop flag. Use `atomic<int>` for a counter. Use a mutex when you need to protect a compound data structure or a sequence of operations that must be atomic together.

```cpp
std::atomic<bool> m_stop{false};

// Thread 1 (reactor loop):
while (!m_stop.load()) { epoll_wait(...); }

// Thread 2 (signal handler):
m_stop.store(true);
```

**Where is this in LDS?**  
`Reactor` uses `std::atomic<bool> m_stop` — the signal thread sets it, the epoll loop reads it. No mutex needed because it's a single boolean.

---

## Memory Ordering

**Q: What is memory ordering? What does `acquire`/`release` mean?**

The CPU and compiler can reorder instructions for performance. Memory ordering tells the hardware/compiler what reordering is safe.

| Order | Meaning |
|---|---|
| `relaxed` | No ordering guarantees. Use for statistics counters |
| `acquire` | All reads/writes after this point see everything before the matching `release` |
| `release` | All reads/writes before this point are visible to any subsequent `acquire` |
| `seq_cst` | Strongest. Full sequential consistency. Default for `atomic`. Expensive on ARM |

For a flag pattern (`store(true)` on one thread, `load()` on another), `release`/`acquire` is sufficient and cheaper than `seq_cst`.

---

## Thread Sanitizer

**Q: How do you detect race conditions?**

ThreadSanitizer (TSan) — compile with `-fsanitize=thread`. Instruments all memory accesses at runtime and reports races with a full stack trace showing both threads and the conflicting accesses.

```bash
g++ -fsanitize=thread -g test.cpp -o test
./test   # prints: WARNING: ThreadSanitizer: data race ...
```

This is how Bug #8 would be caught in practice — TSan reports the race on `m_subs` between the `Notify()` iteration and the `push_back()` in `Register()`.

---

## Producer-Consumer Pattern

**Q: Describe a thread-safe producer-consumer queue.**

Classic pattern in LDS ThreadPool:

```cpp
// Shared state
std::queue<Task> m_queue;
std::mutex m_mutex;
std::condition_variable m_cv;
bool m_stop = false;

// Producer
void Push(Task t) {
    { std::lock_guard lock(m_mutex); m_queue.push(t); }
    m_cv.notify_one();
}

// Consumer (worker thread)
void Worker() {
    while (true) {
        std::unique_lock lock(m_mutex);
        m_cv.wait(lock, [&]{ return !m_queue.empty() || m_stop; });
        if (m_stop && m_queue.empty()) return;
        auto t = m_queue.front(); m_queue.pop();
        lock.unlock();
        t.Execute();
    }
}
```

Key points: unlock before `Execute()` (don't hold the lock while doing work), check both stop flag and queue in predicate.

---

## POSIX Threads (pthreads)

**Q: Why does the C Watchdog use `pthreads` directly instead of `std::thread`?**

The Watchdog is written in C (not C++), so `std::thread` isn't available. `pthread_create`, `pthread_detach`, `sigaction`, `sem_timedwait` are the C-level building blocks. The C++ standard library wraps these under the hood.

Knowing both levels shows depth — `std::thread` is the right choice in C++ code, but understanding the POSIX primitives it wraps demonstrates you know what's happening underneath.
