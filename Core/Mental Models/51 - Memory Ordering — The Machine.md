# Memory Ordering — The Machine

## The Model
CPUs and compilers reorder instructions for performance. Memory ordering is a fence — a physical barrier that says "do not move instructions past this point." Different fence strengths provide different guarantees at different costs. The weakest fence is free; the strongest fence stops the CPU's reordering engine entirely.

## How It Moves

```
Without ordering — compiler/CPU may reorder freely:
Thread A:              Thread B:
  data = 42;             if (ready) {
  ready = true;              use(data);   // may see ready=true but data still 0!
                         }
  (CPU may write 'ready' before 'data' to cache)

With acquire-release:
Thread A:              Thread B:
  data = 42;
  ready.store(true, release);   ← fence: all writes before this are visible to
                                          anyone who sees this store
                                 ready.load(acquire):   ← fence: all reads after 
                                                            this see writes before 
                                                            the matching release
                                     use(data);   // guaranteed to see data=42
```

## The Blueprint

**Five memory orders:**
| Order | Cost | Guarantee |
|---|---|---|
| `memory_order_relaxed` | Free | Atomic operation, no ordering relative to others |
| `memory_order_acquire` | Cheap | No loads after this can be reordered before it |
| `memory_order_release` | Cheap | No stores before this can be reordered after it |
| `memory_order_acq_rel` | Cheap | Both acquire and release |
| `memory_order_seq_cst` | Expensive | Total global order — every thread sees same order |

**Default for `std::atomic`: `seq_cst` — always correct, sometimes unnecessarily slow.**

```cpp
// Safe default (use this unless you measure a bottleneck):
std::atomic<bool> m_running{true};
m_running.store(false);            // seq_cst by default
while (m_running.load()) { ... }   // seq_cst by default

// Optimized (only for performance-critical atomic counters):
std::atomic<uint64_t> m_read_count{0};
m_read_count.fetch_add(1, std::memory_order_relaxed);   // no ordering needed for a counter
```

## Where It Breaks

- **`relaxed` for flags**: if Thread A sets `data = 42` then `flag.store(1, relaxed)`, Thread B may see `flag=1` but still see `data=0`. Use `release`/`acquire` for flag + data patterns.
- **Assuming `volatile` gives you ordering**: `volatile` prevents compiler reordering but NOT CPU reordering. On x86 the CPU model is strong enough to get away with it; on ARM it is not. Use `std::atomic`.
- **Overusing `seq_cst`**: on x86, `seq_cst` stores require a full memory fence instruction. On a lock-free hot path called millions of times/second, this is measurable.

## In LDS

`design_patterns/reactor/src/reactor.cpp`

`m_running` is an `std::atomic<bool>`. The Reactor loop reads it; the signal handler writes it. `seq_cst` (default) ensures the signal handler's `store(false)` is immediately visible to the loop's `load()` without any CPU reordering. Using `relaxed` here would be technically incorrect — the `load` and `store` are on different threads with no other synchronization.

`utilities/threading/thread_pool/include/thread_pool.hpp` — `m_is_running` is `std::atomic<bool>` with `seq_cst`. The condition variable `wait` happens-after the store — the full acquire/release semantics are provided by the mutex, making the atomic ordering here conservative but correct.

## Validate

1. The Reactor uses `atomic<bool> m_running`. The signal handler sets it to `false`. Without `atomic` (plain `bool`), what two things could go wrong?
2. Two threads: Thread A does `x = 42; flag.store(1, relaxed)`. Thread B does `if (flag.load(relaxed)) use(x)`. Is `x = 42` guaranteed visible when Thread B reads x? What ordering fixes this?
3. LDS metrics counter `atomic<uint64_t> reads_served`. Is `seq_cst` or `relaxed` appropriate here? Why?

## Connections

**Theory:** [[Core/Theory/Concurrency/02 - Memory Ordering]]  
**Mental Models:** [[Threads and pthreads — The Machine]], [[Multithreading Patterns — The Machine]], [[Undefined Behavior — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Reactor]] — `m_running` atomic; [[LDS/Architecture/Concurrency Model]]  
**Glossary:** [[pthreads]]
