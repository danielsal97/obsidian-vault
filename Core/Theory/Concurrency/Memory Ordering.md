# Memory Ordering

Modern CPUs and compilers reorder instructions for performance. Memory ordering rules control which reorderings are allowed, ensuring that concurrent code behaves correctly.

---

## The Problem

Without synchronization, compilers and CPUs can reorder reads and writes:

```cpp
// Thread 1:
data = 42;      // (1)
ready = true;   // (2)

// Thread 2:
while (!ready); // (3)
use(data);      // (4)
```

The CPU may execute (2) before (1). Thread 2 sees `ready == true` but `data` still uninitialized. This is a **data race** — undefined behavior in C++.

---

## C++ Memory Model (C++11)

C++11 defines a memory model with three layers:

1. **Sequential consistency** — the default intuition (all threads see the same order)
2. **Happens-before** — formal rule: if A happens-before B, A's effects are visible when B runs
3. **Atomic operations** — the tool for expressing ordering between threads

---

## std::atomic

```cpp
#include <atomic>

std::atomic<bool> ready{false};
std::atomic<int>  data{0};

// Thread 1:
data.store(42, std::memory_order_release);      // release: no reorder before this
ready.store(true, std::memory_order_release);

// Thread 2:
while (!ready.load(std::memory_order_acquire)); // acquire: no reorder after this
int val = data.load(std::memory_order_relaxed); // safe — acquire on ready happened first
```

The `release` on Thread 1 and `acquire` on Thread 2 establish a **synchronizes-with** relationship: everything written in Thread 1 before the release is visible to Thread 2 after the acquire.

---

## Memory Order Options

| Order | What it means | Use case |
|---|---|---|
| `memory_order_relaxed` | No ordering guarantees — just atomicity | Independent counter increments |
| `memory_order_consume` | Dependency ordering (complex, deprecated in practice) | — |
| `memory_order_acquire` | No loads/stores after this can move before it | Load of a flag |
| `memory_order_release` | No loads/stores before this can move after it | Store to a flag |
| `memory_order_acq_rel` | Both acquire and release | Read-modify-write (CAS) |
| `memory_order_seq_cst` | Full sequential consistency — strongest | Default for `std::atomic` ops |

---

## Sequential Consistency (Default)

```cpp
std::atomic<int> x{0};
x++;                          // seq_cst by default
x.fetch_add(1);               // seq_cst by default
x.store(1);                   // seq_cst by default
```

`memory_order_seq_cst` is the safest and most expensive. Use it until you have profiling evidence that a weaker order would help.

---

## Atomic Read-Modify-Write — CAS

Compare-And-Swap: atomically: "if the value is expected, set it to desired; otherwise, load the current value into expected".

```cpp
std::atomic<int> val{0};

int expected = 0;
bool swapped = val.compare_exchange_strong(expected, 1);
// If val == 0: sets val = 1, returns true
// If val != 0: loads val into expected, returns false
```

Used to implement lock-free data structures:

```cpp
// Lock-free push to a stack:
void push(Node* node) {
    node->next = head.load(std::memory_order_relaxed);
    while (!head.compare_exchange_weak(node->next, node,
        std::memory_order_release, std::memory_order_relaxed));
}
```

`compare_exchange_weak` may fail spuriously (allowed to fail even when values match) — always use in a loop.  
`compare_exchange_strong` will not fail spuriously — use when you can't loop.

---

## Volatile — Not What You Think

```cpp
volatile int x = 0;   // does NOT mean thread-safe
```

`volatile` prevents the compiler from caching the variable in a register — useful for memory-mapped hardware registers. It does NOT prevent CPU reordering and does NOT make operations atomic.

For shared data between threads, always use `std::atomic` or a mutex.

---

## Happens-Before Summary

```
Thread 1         Thread 2
  A                 B

A happens-before B means: all of A's side effects are visible when B runs.

Established by:
  - Sequenced-before: A then B in the same thread
  - Synchronizes-with: release-store + acquire-load on same atomic
  - Thread creation: thread A creates thread B → all of A's writes happen-before B starts
  - Thread join: all of B's writes happen-before A returns from join()
```

---

## Fence / Barrier

Explicit memory barrier — weaker than per-operation ordering, used for performance:

```cpp
std::atomic_thread_fence(std::memory_order_acquire);  // acquire fence
std::atomic_thread_fence(std::memory_order_release);  // release fence
std::atomic_thread_fence(std::memory_order_seq_cst);  // full fence
```

Rarely needed — per-operation ordering on atomics is usually clearer.

---

## False Sharing

Two threads write to different variables that happen to be on the same cache line (64 bytes). The CPU must invalidate the other core's cache on every write — massive performance hit.

```cpp
// Bad — counter[0] and counter[1] share a cache line:
struct { int val; } counters[2];

// Fixed — each in its own cache line:
struct alignas(64) { int val; } counters[2];
```

---

## Practical Advice

1. Default to mutex + condition variable — correct and easy to reason about
2. Use `std::atomic` with `seq_cst` for simple flags and counters
3. Only use relaxed/acquire-release ordering when `seq_cst` shows up in profiling
4. Lock-free code is hard — measure before writing it

---

## Related Notes

- [[Multithreading Patterns]] — thread pool, producer/consumer
- [[../Linux/Threads - pthreads]] — pthreads mutex/condvar
- [[../C++/C++11/Overview]] — `std::atomic`, `std::thread`, `std::mutex` added in C++11
- [[../Memory/Process Memory Layout]] — how variables map to memory regions

---

## Understanding Check

> [!question]- Why does volatile not make a flag variable thread-safe, even though it prevents the compiler from caching it in a register?
> volatile tells the compiler to always read/write the variable from/to memory rather than keeping it in a register. This prevents compiler-level caching but does nothing about CPU-level reordering. A modern out-of-order processor can still execute stores and loads in an order different from program order, and without a memory barrier, a second thread on another core may see the volatile write to a flag before seeing the writes to the data it guards. volatile also provides no atomicity — a 64-bit write on a 32-bit bus is two separate bus transactions, and another thread can observe a torn value halfway through. std::atomic provides both atomicity and the necessary memory barriers.

> [!question]- In the ready/data pattern, why is acquire on the ready flag sufficient to also guarantee visibility of the data variable, without putting acquire on data's own load?
> The release-acquire pair on ready creates a synchronizes-with relationship that covers all writes in Thread 1 before the release store, not just the write to ready itself. Thread 1 writes data = 42 and then does ready.store(true, release). The release prevents any earlier store (including data = 42) from being reordered past it. Thread 2 does ready.load(acquire) and sees true. The acquire prevents any subsequent load (including the data load) from being reordered before it. Together, data = 42 is guaranteed to happen-before the data load in Thread 2. No separate acquire on data is needed because the ordering fence covers all preceding writes.

> [!question]- What goes wrong if you use compare_exchange_weak in a single-shot context (not in a retry loop) to implement a "set this flag once" operation?
> compare_exchange_weak is allowed to fail spuriously — it may return false even when the current value matches expected, with no modification having occurred. In a loop this is fine: you just retry. In a single-shot context, a spurious failure means the CAS reports failure, you conclude the flag was already set by someone else, and you skip your initialization path — but the flag is still in its original unset state. The result is a missed initialization: the resource is never set up, and all subsequent code that assumes the flag guards a valid resource proceeds with an uninitialized or null object. Use compare_exchange_strong for single-shot operations where spurious failure cannot be tolerated.

> [!question]- How does false sharing interact with std::atomic, and can two adjacent atomics on the same cache line still suffer performance degradation?
> std::atomic guarantees per-operation atomicity and ordering, but it does not control the physical placement of variables in memory. Two adjacent std::atomic<int> counters can share a cache line. Each atomic write on one core causes a cache coherence protocol message (MESI invalidation) to all other cores that have a copy of that cache line — including threads reading or writing the other atomic on the same line. The operations remain correct and atomic, but throughput degrades because threads contend for exclusive ownership of the cache line. The fix is the same as for non-atomic false sharing: alignas(64) to pad each atomic to its own cache line.

> [!question]- In LDS's shutdown sequence, a flag like m_running = false must be seen by the ThreadPool worker threads. What is the minimum correct ordering, and why would relaxed ordering be wrong?
> The worker threads loop on while (m_running) { ... wait ... process task ... }. The main thread sets m_running = false and calls notify_all() to wake sleeping workers. For workers to reliably see m_running = false and exit their loops, the store needs at least memory_order_release and the load in the worker needs at least memory_order_acquire. This ensures the store is visible after the notify_all() synchronizes-with the workers' condition variable wait (which itself provides acquire semantics on the mutex). Using relaxed on the store to m_running means no ordering guarantee — a worker might load the old true value indefinitely, spinning forever or never exiting. In practice the mutex/condvar provides the needed ordering, but if m_running were checked outside the lock (e.g., a poll before waiting), explicit acquire/release atomics would be required.
