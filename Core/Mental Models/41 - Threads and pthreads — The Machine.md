# Threads and pthreads — The Machine

## The Model
Multiple workers on the same factory floor. They share the same memory, the same tools, the same file descriptors — but each has their own task list (stack) and their own position in the instructions (program counter). A mutex is a physical key hanging on a hook — only one worker can hold it at a time. A condition variable is a waiting room — workers sleep there until someone rings the bell.

## How It Moves

```
Thread A                          Thread B
──────────────────────────────    ──────────────────────────────
lock(mutex)   ← takes key          lock(mutex)   ← waits, key is gone
  read m_data                        (blocked)
unlock(mutex) → hangs key back               ↓
                                   lock(mutex)   ← takes key
                                     read m_data
                                   unlock(mutex) → hangs key back

CONDITION VARIABLE pattern:
Consumer thread:                  Producer thread:
  lock(mutex)                       lock(mutex)
  while (queue.empty())               queue.push(item)
    cond.wait(mutex)  ← sleep         cond.notify_one() ← ring bell
  item = queue.front()              unlock(mutex)
  unlock(mutex)
```

**WHY `while` not `if`:** Spurious wakeups — the OS can wake a thread from `wait()` even when `notify` wasn't called. The `while` loop re-checks the condition and goes back to sleep if it's still false.

## The Blueprint

```cpp
// C++ std::thread:
std::thread t([]() { worker_function(); });
t.join();   // wait for thread to finish

// std::jthread (C++20) — auto-joins on destruction:
std::jthread t([](std::stop_token st) {
    while (!st.stop_requested()) { doWork(); }
});

// Mutex + condition variable:
std::mutex mtx;
std::condition_variable cv;
bool ready = false;

// Producer:
{ std::lock_guard<std::mutex> lock(mtx); ready = true; }
cv.notify_one();

// Consumer:
std::unique_lock<std::mutex> lock(mtx);
cv.wait(lock, []{ return ready; });   // lambda re-checks on spurious wakeup
```

**Deadlock:** Thread A holds mutex1, waits for mutex2. Thread B holds mutex2, waits for mutex1. Both wait forever. Prevention: always acquire mutexes in the same global order. Use `std::lock(m1, m2)` to acquire both atomically.

## Where It Breaks

- **Data race**: two threads access shared data, at least one writes, no synchronization → UB
- **Deadlock**: circular lock dependency
- **Spurious wakeup without `while`**: thread wakes, condition is false, proceeds with invalid state
- **`lock_guard` vs `unique_lock`**: `lock_guard` is simpler and cannot be unlocked early; `unique_lock` can be unlocked early (required for `condition_variable::wait`)

## In LDS

`utilities/threading/thread_pool/include/thread_pool.hpp`

The LDS ThreadPool creates N worker threads at startup. Each worker runs a loop:
```cpp
while (m_is_running) {
    std::unique_lock<std::mutex> lock(m_mtx);
    m_cv.wait(lock, [this]{ return !m_wpq.empty() || !m_is_running; });
    if (!m_is_running) break;
    auto task = m_wpq.top(); m_wpq.pop();
    lock.unlock();
    task();
}
```
`while (!m_wpq.empty() || ...)` is the spurious-wakeup guard. The lambda condition is the `while` loop equivalent.

`services/local_storage/src/LocalStorage.cpp` — `std::shared_mutex m_mutex` allows multiple concurrent readers (`shared_lock`) but exclusive writers (`unique_lock`). Multiple ThreadPool workers can read simultaneously; only one can write.

## Validate

1. LDS uses `shared_mutex` for `LocalStorage`. Two threads call `Read` simultaneously. Do they block each other? What about one `Read` and one `Write`?
2. A worker calls `m_wpq.pop()` after releasing the mutex. Another worker sneaks in between `top()` and `pop()` and takes the same task. How does LDS prevent this?
3. You want to stop all ThreadPool workers. You set `m_is_running = false` and call `m_cv.notify_all()`. Why is `notify_all` (not `notify_one`) required here?

## Connections

**Theory:** [[Core/Theory/Linux/04 - Threads - pthreads]]  
**Mental Models:** [[Multithreading Patterns — The Machine]], [[Memory Ordering — The Machine]], [[Semaphores — The Machine]], [[RAII — The Machine]], [[Reactor Pattern — The Machine]]  
**Tradeoffs:** [[Why ThreadPool over inline execution]]  
**LDS Implementation:** [[LDS/Infrastructure/ThreadPool]], [[LDS/Infrastructure/Threading Deep Dive]]  
**Runtime Machines:** [[LDS/Runtime Machines/ThreadPool and WPQ — The Machine]]  
**Glossary:** [[pthreads]], [[WPQ]]
