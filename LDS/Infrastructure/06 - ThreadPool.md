# ThreadPool + WPQ

**Location:** `utilities/threading/thread_pool/` + `utilities/thread_safe_data_structures/priority_queue/`  
**Status:** ✅ Implemented  
**Layer:** Tier 2 — Framework

---

## What It Does

Manages N worker threads that execute `ICommand` objects in priority order. Commands pushed from the main thread are picked up by workers concurrently. Higher priority commands execute first.

---

## Interface

```cpp
class ThreadPool {
public:
    explicit ThreadPool(size_t threads = hardware_concurrency);

    void AddCommand(std::shared_ptr<ICommand> cmd);  // push to WPQ
    void Stop();                                      // drain + shutdown
    void Suspend();                                   // pause all workers
    void Resume();                                    // unpause
    void SetSize(size_t n);                           // resize pool
    size_t GetSize() const;
};
```

---

## Priority Levels

| Priority | Value | Used For |
|---|---|---|
| `Admin` | 3 | Suspend, Flush — highest urgency |
| `High` | 2 | Write commands |
| `Med` | 1 | Read commands |
| `Low` | 0 | Stop — drains all work first |

Worker threads always pop the highest priority available command.

---

## WPQ — Waitable Priority Queue

```cpp
template <typename T, typename Container, typename Compare>
class WPQ {
    std::priority_queue<T, Container, Compare> m_pq;
    std::mutex              m_mutex;    // instance member ✅
    std::condition_variable m_cv;       // instance member ✅

    void Push(T& item);   // lock, push, notify_one
    T    Pop();           // lock, wait until non-empty, pop
};
```

`Pop()` **blocks** until an item is available — workers sleep with 0% CPU when queue is empty.

---

## Shutdown Sequence

```cpp
void ThreadPool::Stop() {
    Resume();                              // wake any suspended threads first
    for (size_t i = 0; i < N; ++i) {
        AddCommand(make_shared<StopCommand>());  // priority = Low
    }
    for (auto& t : m_threads) t.join();   // wait for all workers to exit
}
```

One `StopCommand` per worker. They drain all higher-priority user commands first, then each worker picks up a `StopCommand` and exits.

---

## Known Bug #10 — Static mutex/cv

```cpp
// CURRENT (wrong):
static std::mutex              m_mutex;  // shared across ALL instances
static std::condition_variable m_cv;

// PROBLEM: tp2.Resume() wakes ALL workers from ALL pools
// FIX: remove 'static' — make them instance members
```

**Must fix before Phase 2** — if multiple `ThreadPool` instances are used, they will interfere with each other.

---

## Related Notes
- [[Engineering/Threading Deep Dive]] — full internals with code
- [[Design Patterns/Command]] — what workers execute
- [[Engineering/Known Bugs]] — Bug #10
- [[04 - Concurrency Model]]
