# Atomics — The Machine

## The Model

An atomic operation is one that the CPU guarantees will complete without interruption — no other CPU can observe a "half-written" state. On x86, 64-bit aligned reads and writes of words up to 64 bits are naturally atomic. `std::atomic<T>` adds two things on top: (1) guarantees atomicity for any T up to the platform's natural size, and (2) controls the memory ordering of surrounding loads and stores.

Atomics are NOT a free alternative to mutexes. They're cheaper for simple counter operations, but they're a poor fit for multi-step operations that need to update several variables consistently.

---

## How It Moves — Atomic Increment

```cpp
std::atomic<int> counter{0};
counter.fetch_add(1, std::memory_order_relaxed);
```

On x86:
```asm
lock xadd [counter], 1
```

```
LOCK prefix:
  → CPU asserts LOCK# signal on memory bus (or uses cache locking on modern CPUs)
  → reads counter's cache line, ensures exclusive ownership (MESI: M state)
  → reads current value, adds 1, writes back
  → all in one bus transaction — no other CPU can read-modify-write between read and write
  → releases exclusive access
      │
      ▼
fetch_add returns the OLD value (before increment)
```

Cost: if the cache line is in M state (no contention): ~5ns. If another CPU holds it: ~30-300ns to acquire exclusive ownership.

---

## Memory Ordering — The Critical Part

The atomicity of the operation itself is only part of the story. The second question is: **which other memory operations are visible before/after this atomic?**

### `memory_order_relaxed`
```cpp
counter.fetch_add(1, memory_order_relaxed);
```
- Guarantees: the atomic operation itself is atomic
- Does NOT guarantee: any ordering relative to non-atomic reads/writes
- Use for: pure counters, statistics — where you care about the final value but not about synchronizing other state

### `memory_order_acquire` (on load)
```cpp
int v = flag.load(memory_order_acquire);
// ALL reads/writes after this line see everything that was written
// before the corresponding release store
```
- Creates a one-way barrier: nothing AFTER the acquire can be reordered BEFORE it
- Pairs with a `release` store on another thread
- Use for: reading a "data is ready" flag — ensures you see the data that was written before the flag was set

### `memory_order_release` (on store)
```cpp
flag.store(1, memory_order_release);
// ALL reads/writes before this line are visible to any thread
// that does an acquire-load of flag and sees value 1
```
- Creates a one-way barrier: nothing BEFORE the release can be reordered AFTER it

### The Acquire-Release Pair — Producer/Consumer

```cpp
// Shared data
int data = 0;
std::atomic<bool> ready{false};

// Thread 1 (producer):
data = 42;                               // plain write
ready.store(true, memory_order_release); // release: data write MUST be visible before this

// Thread 2 (consumer):
while (!ready.load(memory_order_acquire)) {} // acquire: must see everything before the release
use(data);  // guaranteed to see data = 42
```

Without acquire/release: the CPU or compiler could reorder `data = 42` AFTER the store to `ready`, so Thread 2 might see `ready = true` but still read `data = 0`.

### `memory_order_seq_cst` (default)
```cpp
counter.fetch_add(1);  // defaults to seq_cst
```
- Strongest guarantee: all seq_cst operations appear in a single total order visible to all threads
- Prevents ALL reordering: no load/store can move across this operation
- Cost: on x86 this adds a `MFENCE` instruction (~10-50ns): forces all pending writes to flush to the coherent cache before proceeding

---

## Compare-and-Swap (CAS) — Lock-Free Building Block

```cpp
int expected = 0;
bool success = counter.compare_exchange_weak(expected, 1);
```

```
Atomic execution:
  → read current value of counter
  → if current == expected: store 1, return true
  → if current != expected: update expected to current value, return false

One CPU reads-and-conditionally-writes in a single bus-locked operation.
No other CPU can write between the read and the write.
```

CAS is the foundation of all lock-free data structures (lock-free queue, lock-free stack, hazard pointers, etc.).

**`compare_exchange_weak` vs `compare_exchange_strong`**: `_weak` may spuriously fail (even if current == expected) on LL/SC architectures (ARM, RISC-V). Use `_weak` in a retry loop (faster on ARM). Use `_strong` when you cannot loop (e.g. in a condition that must be checked exactly once).

---

## When NOT to Use Atomics

Atomics protect individual variables. They do NOT protect invariants across multiple variables.

```cpp
// BROKEN: two separate atomic stores — another thread can see
// any combination of intermediate states
std::atomic<int> x{0}, y{0};

// Thread 1:
x.store(1);
y.store(1);

// Thread 2 (wrong assumption):
if (y.load() == 1) assert(x.load() == 1);  // NOT guaranteed
```

If you need to update two variables atomically together: use a mutex. If you're writing a lock-free structure that requires updating two locations: use a combined struct with a single CAS (or use epoch-based techniques, but that's expert territory).

---

## Hidden Costs

| Operation | Approx cost (no contention) | With contention |
|---|---|---|
| atomic load (relaxed) | 1ns (same as regular load) | - |
| atomic store (relaxed) | 1ns | - |
| atomic load (seq_cst) | 1ns on x86 | - |
| atomic store (seq_cst) | 10-50ns (MFENCE on x86) | - |
| fetch_add (relaxed) | 5ns | 30-300ns |
| CAS success | 5ns | 30-300ns |
| CAS loop (contended) | - | 100ns-10μs |

---

## Related Machines

→ [[02 - Memory Ordering — The Machine]]
→ [[03 - False Sharing — The Machine]]
→ [[01 - Multithreading Patterns — The Machine]]
→ [[02 - Memory Ordering]]
→ [[10 - Context Switch — The Machine]]
