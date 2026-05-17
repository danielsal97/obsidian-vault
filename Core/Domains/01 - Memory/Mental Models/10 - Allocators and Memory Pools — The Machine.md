# Allocators and Memory Pools — The Machine

## The Model

When `malloc()` needs memory it hasn't seen before, it asks the kernel via `brk()` or `mmap()`. The kernel maps a virtual page — 4KB of address space backed by a physical page only when first touched. The allocator owns the page from there, carving it into small blocks as requests come in. The question is how it organizes those blocks, how it finds a free one, and what happens under multi-threaded load.

This note covers the runtime path. For allocator design patterns (arena, pool, tcmalloc) see [[24 - Allocators — The Machine]].

---

## ptmalloc2 Internals — How Linux malloc Works

### Free lists

```
ptmalloc2 maintains "bins" — singly/doubly-linked lists of freed chunks:

  fastbins  [16B, 24B, 32B, ..., 80B]  — singly linked, LIFO, no coalescing
  smallbins [32B, ..., 512B]            — doubly linked, FIFO, exact size match
  largebins [512B+]                     — sorted by size
  unsorted bin                          — freed chunks queued before sorting
```

Allocation path:
1. Round up to next chunk size (always multiple of 16 on x86-64)
2. Check fastbin (if size ≤ 80B) — O(1) pop from LIFO list
3. Check smallbin — O(1) if exact match exists
4. Check unsorted bin, sort into bins
5. Search largebin for best fit
6. If nothing: extend heap with `sbrk()` or new `mmap()` anonymous mapping

### Chunk layout on heap

```
Heap memory for a 32-byte alloc:
  [prev_size: 8B][size+flags: 8B]  ← header (hidden, before returned ptr)
  [user data: 32B]                 ← what malloc() returns
  [next chunk header...]

If you write past user data: you corrupt the next chunk's header → heap corruption
```

Freed chunk:
```
  [prev_size: 8B][size+flags: 8B][fd: 8B → next free][bk: 8B → prev free][...]
                                   ↑ free list pointers overlaid on user data
```

---

## Multi-threaded Allocation — The Arena Problem

ptmalloc2's default arena is global — protected by a mutex. Under high concurrency:

```
Thread pool, 8 threads, each allocating 1000 objects/sec:

Without per-thread arenas:
  Thread 1: lock(arena_mutex) → alloc → unlock  ← 30ns holding the lock
  Threads 2-8: spinning on arena_mutex → wasted CPU cycles
  Throughput: ~1/8 of theoretical maximum

With per-thread arenas (ptmalloc2 creates multiple arenas):
  Thread 1: acquires arena #1 (no contention)
  Thread 2: acquires arena #2 (no contention)
  ...
  Throughput: near-linear scaling
```

Each arena is an independent heap: separate `brk`-extended region (or separate `mmap` regions). Fragmentation per-arena is higher (each arena grows independently), but throughput is far better.

---

## Page-Level View — What the Kernel Sees

```
malloc(256KB) path on Linux:

Request > MMAP_THRESHOLD (128KB by default):
  → mmap(NULL, 256KB, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0)
  → kernel assigns virtual address range (NOT physical pages yet)
  → returns ptr

First write to ptr[0]:
  → page fault → kernel allocates physical page → maps into TLB
  → store completes
  Cost: ~1μs for first touch per 4KB page

malloc(4KB) path:
  → heap has room: return from sbrk-extended region
  → no syscall, no page fault (pages already mapped from previous brk extensions)
  Cost: ~30ns
```

---

## The True Cost of Allocation in Hot Loops

```cpp
// BAD: allocating in a tight loop
for (int i = 0; i < 1000000; ++i) {
    Packet* p = new Packet();  // 30-100ns each + cache miss on first use
    process(p);
    delete p;
}
// Total hidden cost: 30-100μs allocator overhead + cold cache misses

// GOOD: pool allocator
Pool<Packet, 256> pool;
for (int i = 0; i < 1000000; ++i) {
    Packet* p = pool.alloc();  // ~2ns, cache warm (reusing freed slots)
    process(p);
    pool.free(p);
}
// Total hidden cost: ~2μs
```

---

## Fragmentation — The Silent Performance Killer

```
Timeline of allocations on a long-running server:

t=0:    [A: 64B][B: 128B][C: 64B][D: 512B]...
t=100:  free B → [A: 64B][free: 128B][C: 64B][D: 512B]
t=200:  malloc(256B) → 128B hole too small → new 256B at end
t=300:  [A][free:128B][C][D][E:256B]...

After hours: heap looks like swiss cheese.
Effective utilization: 60-70%. Address space and physical memory wasted.
Worst case: an allocation that "should fit" requires mmap because no
  contiguous free region of the right size exists.
```

Fix: arena allocator (batch-free at epoch boundary eliminates fragmentation entirely).

---

## Hidden Costs Summary

| Scenario | Cost |
|---|---|
| malloc, free block available | 30-100ns (free list lookup + cache miss) |
| malloc, heap extension (`sbrk`) | 100-500ns (no syscall if mapped, else +μs) |
| malloc, `mmap` for large block | 500ns-2μs (syscall + TLB registration) |
| First touch of newly allocated page | ~1μs (page fault → physical page mapping) |
| Arena bump allocation | ~1-2ns |
| Pool alloc/free | ~2-3ns |
| Fragmentation waste (long-running) | 10-30% extra memory |

---

## Related Machines

→ [[08 - malloc and free — The Machine]]
→ [[03 - Virtual Memory — The Machine]]
→ [[04 - Paging — The Machine]]
→ [[09 - Cache Hierarchy — The Machine (deep)]]
→ [[24 - Allocators — The Machine]]
