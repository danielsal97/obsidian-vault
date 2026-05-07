---
name: WPQ — Waitable Priority Queue
type: data-structure
---

# WPQ — Waitable Priority Queue

An internal thread-safe data structure that combines a priority queue with a condition variable. Worker threads block on it (zero CPU) until a command is available, then wake and pop the highest-priority item.

## "Waitable" — The Blocking Mechanism

```cpp
// Worker thread loop:
while (running) {
    std::unique_lock<std::mutex> lock(mutex_);
    cond_.wait(lock, [this]{ return !queue_.empty() || !running_; });
    // ↑ Releases lock and sleeps until notified.
    // Wakes when push() calls cond_.notify_one()

    auto cmd = queue_.top();
    queue_.pop();
    lock.unlock();

    cmd->Execute();
}
```

## "Priority" — The Ordering

Commands have a `CMDPriority` enum that determines execution order:

| Priority | Level | Used For |
|----------|-------|----------|
| `Admin` | 3 (highest) | System-critical (flush, shutdown) |
| `High` | 2 | WRITE operations — data integrity |
| `Med` | 1 | READ operations |
| `Low` | 0 | Background tasks |

A WRITE always executes before a READ if both are waiting, ensuring data is persisted before reads might observe stale state.

## Why Priority Matters

In a busy system, the queue may accumulate many mixed READ and WRITE commands. Without priority, a long burst of READs could delay a WRITE indefinitely. Priority ordering guarantees writes drain first.

## Interface

```cpp
class WPQ {
public:
    void Push(std::shared_ptr<ICommand> cmd);  // wakes one worker
    std::shared_ptr<ICommand> Pop();           // blocks until available
    void Shutdown();                           // wake all workers to exit
};
```

## Related
- [[Utilities Framework]] — ThreadPool + WPQ implementation details
- [[Command]] — what gets queued
- [[Threading Deep Dive]] — mutex/condvar internals
- [[Concurrency Model]] — how the full thread model is arranged
