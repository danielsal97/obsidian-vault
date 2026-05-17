# LDS ThreadPool + WPQ — The Machine

## The Model
A factory floor with N permanent workers and one priority conveyor belt. The belt has three lanes: Admin (WRITE), High (READ), Medium (FLUSH). Workers sleep at the belt's end. When a box arrives, the worker who's awake picks up the highest-priority box, opens it, executes whatever is inside, then returns to the belt. The main thread drops boxes on the belt and immediately walks away — it never waits.

## Why This Exists

**Without ThreadPool (inline execution in Reactor):**
- Reactor thread executes storage I/O and UDP sends directly
- A slow minion reply (100ms timeout) blocks the Reactor for 100ms
- During that 100ms: ALL other file descriptors are unmonitored
- One slow operation starves all other clients
- No priority control: a low-priority flush blocks a high-priority write

**ThreadPool + WPQ solves:**
- Reactor thread NEVER blocks: enqueues work in O(1), returns to epoll_wait()
- Worker threads absorb all blocking operations (storage, UDP, timeouts)
- WPQ priority lanes: Admin (WRITE) > High (READ) > Med (FLUSH)
  → a WRITE request always executes before a pending FLUSH
- N workers = N concurrent operations without spawning new threads per request

**Runtime effect:** A minion times out on a UDP ACK (Scheduler waits 100ms, retries with backoff). During all 100ms, the Reactor is free, handling other clients' reads and writes without any delay. The ThreadPool absorbs the blocking wait completely. Without this design, one slow minion would freeze the entire server.

## How It Moves

```
Main thread (Reactor):
  cmd = make_shared<WriteCommand>(data)
  thread_pool.AddCommand(cmd)   ← Push to WPQ (non-blocking)
  return to epoll               ← IMMEDIATELY — never waits

Inside WPQ::Push():
  lock(m_mutex)
  m_pq.push(cmd)     ← heap insert, O(log n)
  m_cv.notify_one()  ← wake one sleeping worker
  unlock

Worker thread (sleeping in Pop()):
  WPQ::Pop():
    lock(m_mutex)
    m_cv.wait(lock, [this]{ return !m_pq.empty(); })   ← spurious-wakeup safe
    cmd = m_pq.top(); m_pq.pop()
    unlock
  cmd->Execute()   ← storage read/write, network send — all happens here
```

**Priority ordering:**
The WPQ comparator orders by `ICommand::operator<`. WRITE commands have priority `Admin` (highest), READ has `High`, FLUSH has `Med`. A WRITE arriving while 10 READs are queued goes to the front — it will be executed before any READ.

**Shutdown via `StopCommand`:**
```
thread_pool.Stop():
  for each worker thread:
    wpq.Push(StopCommand{})   ← StopCommand::Execute() throws a special exception
                               ← worker catches it and exits its loop
  join all threads
```

## The Blueprint

```cpp
// thread_pool.hpp key parts:
class ThreadPool {
    WPQ<shared_ptr<ICommand>, vector<...>, Comparator> m_command;
    vector<thread> m_threads;
    static mutex m_mutex;
    static condition_variable m_cv;
    bool m_suspend_flag;
    
    void ThreadFunc() {
        while (true) {
            auto cmd = m_command.Pop();   // blocks until work arrives
            cmd->Execute();               // does the actual work
        }
    }
};

// WPQ::Pop() — blocking:
T Pop() {
    unique_lock lock(m_mutex);
    m_cv.wait(lock, [this]{ return !m_pq.empty(); });
    T ret = m_pq.top(); m_pq.pop();
    return ret;
}
```

**`Suspend()` / `Resume()`:**
Sends a `SuspendCommand` to each worker. `SuspendCommand::Execute()` waits on `m_cv` checking `m_suspend_flag`. `Resume()` sets flag to false and `notify_all()` — workers unblock and return to processing.

## Where It Breaks

- **Slow Execute()**: worker holds no lock while executing — other workers run freely. Slowness only affects that one worker's throughput.
- **WPQ full**: no capacity limit — if producers outpace consumers, the WPQ grows unbounded until OOM. Add backpressure if needed.
- **Destructor races**: `~ThreadPool` must push N `StopCommands` and `join` all threads. If `Stop()` is not called before destruction, threads may still be running when the WPQ is destroyed — UB.
- **Static mutex**: `m_mutex` and `m_cv` are `static` in the current implementation — shared across all ThreadPool instances. Creating two ThreadPools would have them sharing the same lock.

## Validate

1. 100 READ commands and 1 WRITE command are pushed to the WPQ simultaneously. In what order will workers execute them?
2. A worker is mid-`Execute()` (holding no lock) when `Stop()` is called. Does `Stop()` wait for that worker to finish? Trace the exact sequence.
3. The WPQ has 0 items. 4 workers are sleeping in `Pop()`. A WRITE command arrives. How many workers wake up? Which one gets the command?

---

## Core Vault Cross-Links

→ [[01 - Multithreading Patterns — The Machine]] — the general ThreadPool + WPQ pattern
→ [[Concurrency Runtime — The Machine]] — clone() → futex → wake cycle behind workers
→ [[10 - Context Switch — The Machine]] — what happens when scheduler picks a worker thread
