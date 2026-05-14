# Atomics

An atomic operation is one the CPU guarantees completes without interruption. No other CPU can observe an intermediate state. `std::atomic<T>` provides two things: (1) indivisible read-modify-write for type T, and (2) control over the memory ordering of surrounding loads and stores.

---

## What Atomicity Means

A plain `int` increment is three instructions on x86: load, add, store. Between the load and the store, another thread can write the variable. The result is a **torn write** or a **lost update**. An atomic increment uses a single locked bus transaction — the read and write are fused and exclusive.

Atomics prevent torn reads and lost updates on a single variable. They do not protect invariants that span multiple variables — that still requires a mutex.

---

## `std::atomic<T>` Operations

```cpp
std::atomic<int> x{0};

x.store(1, order);                   // write
int v = x.load(order);               // read
int old = x.exchange(5, order);      // swap: returns old value

// Compare-and-swap:
int expected = 0;
bool ok = x.compare_exchange_weak(expected, 1, order);
// If x == expected: stores 1, returns true
// If x != expected: loads x into expected, returns false
// _weak may fail spuriously on LL/SC architectures (ARM) — use in a loop
// _strong never fails spuriously — use when you cannot loop

int prev = x.fetch_add(1, order);    // atomic increment; returns old value
int prev = x.fetch_sub(1, order);    // atomic decrement
```

---

## Memory Orders

The memory order argument controls visibility of surrounding non-atomic memory operations. Full treatment is in [[02 - Memory Ordering]]. Brief definitions:

| Order | What it guarantees |
|---|---|
| `relaxed` | Atomicity only. No ordering constraints on other loads/stores. |
| `acquire` | (on load) Nothing after this load can be reordered before it. Pairs with a `release` store. |
| `release` | (on store) Nothing before this store can be reordered after it. Pairs with an `acquire` load. |
| `acq_rel` | Both acquire and release. Use on read-modify-write (CAS, fetch_add). |
| `seq_cst` | All seq_cst operations appear in a single global order visible to all threads. Default. |

Use `seq_cst` until profiling shows it is a bottleneck. Then consider acquire/release for flag-based producer/consumer patterns.

---

## Hardware Implementation

**x86:** The `LOCK` prefix asserts exclusive ownership of the cache line, performs the read-modify-write atomically, then releases ownership. No other CPU can touch the cache line between the read and write.

```asm
lock xadd [counter], 1    ; fetch_add on x86
lock cmpxchg [ptr], rax   ; CAS on x86
```

**ARM / RISC-V:** No `LOCK` prefix. Uses **LL/SC** (Load-Linked / Store-Conditional):
```
ldrex r0, [ptr]    ; load-exclusive: marks the cache line for monitoring
; ... compute new value ...
strex r1, r2, [ptr] ; store-conditional: fails if any other CPU wrote the line
```
If `strex` fails, the thread retries. This is why `compare_exchange_weak` can fail spuriously on ARM even when values match — the cache line was touched between `ldrex` and `strex`.

---

## CAS and the ABA Problem

CAS is the primitive underlying all lock-free algorithms. The pattern:

```cpp
// Lock-free stack push:
node->next = head.load(relaxed);
while (!head.compare_exchange_weak(node->next, node, release, relaxed));
```

**ABA problem:** Thread 1 reads head = A. Thread 2 pops A, pushes B, then pushes A back. Thread 1's CAS sees head == A and succeeds — but the list structure has changed. The CAS cannot distinguish "A unchanged" from "A removed and re-added". Fix: attach a version counter to the pointer (tagged pointer), or use hazard pointers or epoch-based reclamation.

---

## When to Use Atomics

| Use case | Pattern |
|---|---|
| Counter (statistics, reference count) | `fetch_add(1, relaxed)` |
| Single flag (shutdown signal) | `store(true, release)` / `load(acquire)` |
| Lock-free queue or stack | CAS loop with `acq_rel` |
| Spinlock | CAS on a bool with `acquire` on lock, `release` on unlock |

## When NOT to Use Atomics

When multiple variables must change together consistently. Two separate atomic stores are not atomic relative to each other — another thread can observe any combination of old and new values.

```cpp
// BROKEN: not atomic together
std::atomic<int> size{0}, capacity{0};
size.store(new_size);       // thread can observe size updated but capacity not yet
capacity.store(new_cap);
```

If the invariant is `size <= capacity`, another thread reading both atomics between these two stores sees the invariant violated. Use a mutex for multi-variable invariants.

---

## Cost

| Operation | Uncontended | Contended (cross-core) |
|---|---|---|
| `load` / `store` (relaxed) | ~1 ns | — |
| `store` (seq_cst, x86) | ~10–50 ns (MFENCE) | — |
| `fetch_add` (relaxed) | ~5 ns | 30–200 ns |
| CAS success | ~5 ns | 30–200 ns |

Contention cost is cache-coherence traffic: acquiring exclusive ownership of the cache line from another CPU. See [[04 - False Sharing]] for the related problem of false sharing.

---

## Related

- [[04 - Atomics — The Machine]] — hardware-level execution trace
- [[02 - Memory Ordering]] — full acquire/release/seq_cst semantics
- [[04 - False Sharing]] — adjacent atomics can still cause coherence traffic
