# std::vector — The Machine

## The Model

A `vector<T>` is three pointers on the stack: `begin`, `end`, `capacity_end`. The actual data is a contiguous block on the heap. The critical behavior: when `push_back()` exceeds capacity, the vector allocates a new block (typically 2x larger), **moves every existing element** to the new block, then destroys the old block. This reallocation is O(n) — and it invalidates every pointer, reference, and iterator into the old storage.

---

## Memory Layout

```
Stack frame:
┌─────────────────┐
│  begin ptr      │ → points to heap allocation
│  end ptr        │ → points to one-past-last element
│  capacity ptr   │ → points to one-past-last allocated slot
└─────────────────┘

Heap (contiguous block):
┌────┬────┬────┬────┬────┬────┬────┬────┐
│ T0 │ T1 │ T2 │ T3 │ .. │ .. │ .. │ .. │
└────┴────┴────┴────┴────┴────┴────┴────┘
 ^                    ^                    ^
begin               end              capacity_end
(size=4, capacity=8)
```

---

## How It Moves — push_back() (no reallocation)

```
v.push_back(x)   where size < capacity
      │
      ▼
Placement new at *end:
  → calls T's copy constructor (or move constructor if x is rvalue)
    with the storage at *end as the destination
  → T is constructed in-place — no separate allocation
      │
      ▼
increment end pointer
      │
      ▼
Done. O(1) amortized.
```

---

## How It Moves — push_back() WITH reallocation

```
v.push_back(x)   where size == capacity
      │
      ▼
Calculate new capacity: typically 2x current
  (exact growth factor is implementation-defined; libstdc++: 2x, MSVC: 1.5x)
      │
      ▼
allocator.allocate(new_capacity * sizeof(T)):
  → calls ::operator new(bytes)
  → malloc(bytes) internally
  → kernel: brk() or mmap() if heap exhausted
  → returns pointer to new uninitialized block
      │
      ▼
Move existing elements to new block:
  → for each T at position i (i = 0 to size-1):
      → if T has noexcept move constructor:
          → std::move_if_noexcept: call T::T(T&&) at new location
          → no copy — O(1) per element for most types
      → else (move constructor can throw):
          → must copy instead (to preserve strong exception guarantee)
          → calls T::T(const T&) at new location
          → EXPENSIVE: deep copy for strings, containers-within-vectors
      │
      ▼
Construct new element at new end position (the push_back target)
      │
      ▼
Destroy old elements (call T::~T() for each)
  → destructor runs in reverse order: last to first
      │
      ▼
allocator.deallocate(old_ptr):
  → ::operator delete(old_ptr)
  → free() internally
      │
      ▼
Update begin, end, capacity_end to new block
      │
      ▼
All iterators, pointers, and references into old storage: INVALID
```

---

## The noexcept Rule

If `T`'s move constructor is not `noexcept`, `vector` uses copy during reallocation to preserve the strong exception guarantee. If a copy throws halfway through, vector can destroy the partially-copied new block and the original is untouched. If it used moves and a move threw halfway through, the original elements would be in moved-from (gutted) states — unrecoverable.

**Rule: always mark move constructors and move assignment `noexcept` if you can**. It enables O(n) reallocation with moves instead of copies.

---

## reserve() — pre-allocate to prevent reallocation

```cpp
v.reserve(1000);   // allocates for 1000 elements, size remains 0
```

```
reserve(n):
  → if n <= capacity: no-op
  → else: allocate new block of size n
  → move existing elements (same as reallocation above)
  → NO new elements constructed — just changes capacity
```

Use `reserve()` when you know the final size upfront. Eliminates all reallocations and iterator invalidation.

---

## Cache Locality — Why Vector Beats List

`vector<int>` of 1000 elements: 4000 bytes, fits in L1 cache. Sequential scan: one cache line (64 bytes = 16 ints) fetched per miss, then 15 more ints at L1 speed.

`list<int>` of 1000 elements: each node is a separate heap allocation (24+ bytes: data + prev + next pointers). 1000 nodes scattered across heap. Sequential scan: potentially one cache miss PER NODE. 1000x more cache misses than vector for same data.

For anything involving iteration, vector wins unless you need O(1) insert-in-middle.

---

## Hidden Costs

- Reallocation during push_back: O(n) amortized O(1) — occasional O(n) spike
- Iterator invalidation: any reallocation invalidates all iterators — silent UB if used after
- Destructor on vector<T>: calls T::~T() for every element — can be expensive if T is complex
- `erase(it)` in the middle: O(n) shift of all elements after `it`
- `insert(it, x)` in the middle: O(n) shift — use `push_back` + `sort` instead if possible

---

## Related Machines

→ [[08 - malloc and free — The Machine]]
→ [[08 - Cache Hierarchy — The Machine]]
→ [[01 - RAII — The Machine]]
→ [[03 - Move Semantics — The Machine]]
→ [[08 - STL Containers]]
