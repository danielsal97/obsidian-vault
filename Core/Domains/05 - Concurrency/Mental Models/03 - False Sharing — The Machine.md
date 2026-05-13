# False Sharing — The Machine

## The Model

The CPU's cache coherence protocol operates at cache line granularity — 64 bytes. If two threads on different CPUs are writing to different variables that happen to reside in the same cache line, they fight over ownership of that cache line on every write. Neither thread is sharing the VARIABLE, but they're sharing the CACHE LINE. This is false sharing — and it can kill parallel performance, turning a 4-core program into something slower than a single-threaded one.

---

## How It Moves — Cache Coherence (MESI Protocol)

Each cache line can be in one of four states:
- **M**odified: this CPU has the only copy, and it's been written (dirty)
- **E**xclusive: this CPU has the only copy, clean
- **S**hared: multiple CPUs have clean copies
- **I**nvalid: this CPU's copy is stale

```
Initial state: Thread A and Thread B both recently read counter_a and counter_b.
Both cache lines are in SHARED state on both CPUs.

Thread A (CPU 0) writes counter_a:
  → CPU 0 sends "invalidate" broadcast on memory bus
  → CPU 1 receives invalidate: marks its cache line INVALID
  → CPU 0's cache line transitions: SHARED → MODIFIED
  → CPU 0 writes proceed

Thread B (CPU 1) writes counter_b (same 64-byte cache line as counter_a):
  → CPU 1 sees its cache line is INVALID
  → CPU 1 must fetch the line: sends "read with intent to modify" request
  → CPU 0 receives: must flush its MODIFIED line to memory (write-back)
  → CPU 0's line transitions: MODIFIED → INVALID
  → CPU 1 fetches line from memory (or directly from CPU 0's cache)
  → CPU 1 writes counter_b
  → Cycle repeats every time either thread writes
```

Two threads doing independent work, but every write causes a cross-CPU cache line transfer. This adds ~30-300ns of latency per write (inter-core vs same-socket vs cross-socket).

---

## Real Code That Demonstrates False Sharing

```cpp
// BAD: a and b are adjacent — likely same cache line
struct Counters {
    std::atomic<int> a;   // offset 0
    std::atomic<int> b;   // offset 4
};

Counters c;
// Thread 0: while(true) c.a++;
// Thread 1: while(true) c.b++;
// Performance: ~2x SLOWER than sequential, due to constant cache line bouncing
```

```cpp
// GOOD: a and b are on separate cache lines
struct alignas(64) Counter {
    std::atomic<int> value;
    char padding[60];    // pad to fill 64 bytes
};

Counter a, b;
// Thread 0: while(true) a.value++;
// Thread 1: while(true) b.value++;
// Performance: 2x speedup vs sequential (true parallelism)
```

---

## The Fix: Cache Line Padding

```cpp
// C++17 hardware_destructive_interference_size
struct alignas(std::hardware_destructive_interference_size) AlignedCounter {
    std::atomic<int> value;
};
```

`hardware_destructive_interference_size` is typically 64 (x86) or 128 (ARM). Use `alignas` to force each variable onto its own cache line.

---

## Where False Sharing Commonly Hides

**Thread pool work queues**: if each worker thread has its own stats counter (tasks_completed, etc.) and they're in a contiguous array — false sharing.

**Ring buffer head/tail**: if the producer updates `head` and the consumer updates `tail`, and they share a cache line — every push/pop bounces the line.

**Struct members**: any frequently-written fields in a struct accessed by multiple threads. Even if protected by separate mutexes, the cache line bounces on every mutex acquire/release.

**Allocator metadata**: if the allocator stores small bookkeeping data between allocations and multiple threads allocate in parallel, those metadata bytes may share cache lines across threads.

---

## How to Diagnose

**perf stat**: `perf stat -e cache-misses,cache-references ./program` — high miss rate under parallelism suggests false sharing.

**perf c2c** (Linux): specialized tool for detecting cache line bouncing between CPUs. Shows which cache lines are hot and which CPUs are fighting over them.

**VTune Amplifier / Intel Advisor**: profiler with dedicated false sharing detection.

Symptoms without tools: parallel version of program is slower or same speed as sequential. Adding cores makes it WORSE. Removing `std::atomic` and using plain reads "magically speeds it up" (because you've broken the coherence protocol tracking).

---

## Hidden Costs

- False sharing on a frequently-written line: 100-300ns per write (vs 0.5ns L1 hit)
- Cross-NUMA-node false sharing: 300-1000ns per write
- A tight loop with false sharing: throughput drops from 1B ops/sec to 3-10M ops/sec

---

## Related Machines

→ [[02 - Memory Ordering — The Machine]]
→ [[01 - Multithreading Patterns — The Machine]]
→ [[../Domains/01 - Memory/Mental Models/08 - Cache Hierarchy — The Machine]]
→ [[../Domains/04 - Linux/Mental Models/10 - Context Switch — The Machine]]
→ [[../Domains/05 - Concurrency/Theory/02 - Memory Ordering]]
