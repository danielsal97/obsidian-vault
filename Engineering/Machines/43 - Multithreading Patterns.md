# Multithreading Patterns — The Machine

## The Model
Three factory floor blueprints for coordinating multiple workers. Thread Pool: N permanent workers pulling from a shared task queue — no thread creation overhead. Producer-Consumer: one conveyor belt, producers add work to one end, consumers take from the other. Active Object: a worker with its own private queue — you send it messages, it processes them sequentially.

## How It Moves

**Thread Pool:**
```
Main thread            Task Queue (WPQ)         Worker threads (N=4)
──────────────         ────────────────         ────────────────────
submit(readTask)  ──→  [WRITE][READ][READ]  ←──  worker1: pops WRITE, executes
submit(writeTask) ──→  [WRITE][READ][READ]  ←──  worker2: pops WRITE, executes
submit(flushTask) ──→  [READ][READ][FLUSH]  ←──  worker3: pops READ, executes
                                             ←──  worker4: blocks (queue empty)
```
Workers never die. Tasks come and go. Thread creation cost (>100μs) paid only at startup.

**Producer-Consumer:**
```
Producers                  Buffer (bounded)           Consumers
─────────                  ───────────────            ─────────
produce(item) ──→  if full: wait  →  push(item)  ←──  pop(item): if empty: wait
                   post(not_empty)                     post(not_full)
```

## The Blueprint

**LDS ThreadPool pattern:**
```cpp
// Worker loop (inside thread_pool.cpp):
while (true) {
    std::unique_lock<std::mutex> lock(m_mtx);
    m_cv.wait(lock, [this]{
        return !m_wpq.empty() || !m_is_running;
    });
    if (!m_is_running && m_wpq.empty()) break;
    
    auto task = m_wpq.top();
    m_wpq.pop();
    lock.unlock();      // release lock BEFORE executing — don't hold lock during work
    task();
}
```

**Key rules:**
1. Release the mutex before executing the task — holding the lock during execution blocks all other workers
2. The `while` loop in `wait` (or predicate lambda) handles spurious wakeups
3. Check shutdown condition (`!m_is_running`) inside the predicate — avoids deadlock on shutdown
4. Use `notify_all` when shutting down — all workers must see the signal

## Where It Breaks

- **Lock held during task execution**: one worker executes, others block — defeats parallelism
- **Missed notification**: task submitted before worker enters `wait` — without the predicate condition, notification is lost and worker sleeps forever
- **Thread pool too small**: tasks block waiting for I/O, all N workers are blocked — no workers left for CPU-bound tasks. Solution: separate I/O and CPU thread pools.

## In LDS

`utilities/threading/thread_pool/include/thread_pool.hpp` + `src/thread_pool.cpp`

The LDS ThreadPool is the central execution engine. The WPQ feeds it with prioritized tasks (WRITE=2, READ=1, FLUSH=0). The Reactor receives events and submits tasks to the pool — it never executes work itself, keeping the event loop fast. Workers execute `LocalStorage::Read/Write` and `IDriverComm::SendReply` concurrently, protected by `LocalStorage`'s `shared_mutex`.

## Validate

1. A LDS WRITE task is submitted while all 4 workers are executing READ tasks. What happens in the WPQ, and when does the WRITE task execute?
2. The ThreadPool is being destroyed. `m_is_running = false` is set and `m_cv.notify_all()` is called. One worker is mid-task (has already popped its task and released the lock). Does it finish its task or terminate immediately?
3. You increase the ThreadPool to 16 workers on a 4-core machine. Does performance improve? What is the limit, and what type of tasks benefit from more workers than cores?
