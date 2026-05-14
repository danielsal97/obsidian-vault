# False Sharing

False sharing is a performance problem, not a correctness problem. Two threads write to logically independent variables, but those variables happen to reside on the same cache line. The CPU cache coherence protocol treats the entire cache line as the unit of ownership — so every write by one thread forces the other thread to re-acquire the line, even though they never touch the same memory address.

---

## Cache Lines: The Unit of Coherence

CPUs do not transfer individual bytes between caches. They transfer **cache lines** — 64 bytes on x86 and most ARM cores. Every load and store operates on a whole cache line. If a variable is 4 bytes, it shares its cache line with the 60 surrounding bytes.

This is why two counters adjacent in memory fight over the same resource even though they have nothing to do with each other.

---

## MESI Protocol

Each cache line in each CPU's cache is in one of four states:

- **Modified**: this CPU has the only copy; it has been written (dirty)
- **Exclusive**: this CPU has the only copy; it is clean
- **Shared**: multiple CPUs have clean copies
- **Invalid**: this CPU's copy is stale

A write requires **Modified** state. To acquire it, the CPU broadcasts an **invalidate** message to all other CPUs that hold the line. They mark their copies **Invalid**. The writing CPU then has exclusive ownership and proceeds.

**With false sharing:**
1. Thread A (CPU 0) writes `counter_a` → invalidates the line on CPU 1
2. Thread B (CPU 1) writes `counter_b` (same line) → must fetch the line back from CPU 0 → invalidates it on CPU 0
3. Repeat on every iteration — the line bounces between CPUs at ~30–300 ns per transfer

Neither thread is doing anything logically wrong. The MESI protocol is doing its job correctly. The problem is layout.

---

## Canonical Example

```cpp
// BAD: a and b share a 64-byte cache line
struct Counters {
    std::atomic<int> a;   // bytes 0-3
    std::atomic<int> b;   // bytes 4-7
};

Counters c;
// Thread 0: while (true) c.a.fetch_add(1, relaxed);
// Thread 1: while (true) c.b.fetch_add(1, relaxed);
// Result: ~10x slower than sequential, not ~2x faster
```

```cpp
// GOOD: a and b are on separate cache lines
struct alignas(64) Counter {
    std::atomic<int> value;
    // implicit padding to 64 bytes
};

Counter a, b;
// Thread 0: a.value++   Thread 1: b.value++
// Result: ~2x throughput vs sequential
```

---

## The Fix

**`alignas(64)`** on a struct forces the struct to start at a 64-byte-aligned address. If the struct is also 64 bytes or smaller, it cannot share a cache line with any adjacent object.

```cpp
// C++17 portable form:
#include <new>  // for hardware_destructive_interference_size

struct alignas(std::hardware_destructive_interference_size) PaddedCounter {
    std::atomic<int> value;
};
```

`hardware_destructive_interference_size` is 64 on x86 and typically 128 on ARM (due to adjacent-line prefetching). Using the constant is more portable than hardcoding 64.

**Thread-local accumulation** is often better than padding. If each thread accumulates into a private variable and only writes to the shared counter periodically, you eliminate coherence traffic entirely on the hot path:

```cpp
thread_local int local_count = 0;
// ... in hot loop:
local_count++;
// ... periodically:
shared_counter.fetch_add(local_count, relaxed);
local_count = 0;
```

---

## Where False Sharing Hides

**Thread pool stats arrays**: if each worker thread has its own metrics field in a contiguous array, adjacent fields share cache lines. Pad each entry or use thread-local storage.

**Ring buffer head and tail**: producer updates `head`, consumer updates `tail`. If they are in the same struct without padding, every push/pop bounces the cache line between producer and consumer.

**Mutex internals**: even when two protected variables use separate mutexes, if the mutex objects themselves are adjacent in memory, the `lock`/`unlock` writes bounce the line containing both mutexes.

---

## Detection

```bash
# High cache miss rate under parallelism:
perf stat -e cache-misses,cache-references ./program

# Cache line bouncing between CPUs (Linux 4.1+):
perf c2c record ./program && perf c2c report

# Symptom without tools:
# - Parallel version is same speed or slower than sequential
# - Adding more threads makes throughput worse
# - Removing std::atomic "fixes" performance (breaks coherence tracking but reveals layout)
```

---

## What Not to Do

Do not pad everything. Padding every struct member to 64 bytes wastes memory, increases working-set size, and defeats the hardware prefetcher (which fetches adjacent cache lines speculatively). Only pad the variables that are written frequently by multiple threads.

---

## Cost

| Scenario | Write latency |
|---|---|
| L1 hit (owned line) | ~0.5–1 ns |
| False sharing (same socket) | 30–100 ns per write |
| False sharing (cross-NUMA) | 100–300 ns per write |
| Tight loop throughput loss | From 1B ops/s down to 3–10M ops/s |

---

## Related

- [[03 - False Sharing — The Machine]] — MESI state machine trace
- [[02 - Memory Ordering]] — memory ordering and the C++ atomics model
- [[03 - Atomics]] — atomic operations and why adjacent atomics still suffer this problem
- [[../01 - Memory/Mental Models/09 - Cache Hierarchy — The Machine (deep)]] — cache hierarchy and prefetching
