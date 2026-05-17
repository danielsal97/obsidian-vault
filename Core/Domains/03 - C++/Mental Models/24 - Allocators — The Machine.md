# Allocators — The Machine

## The Model

`operator new` calls `malloc`. `malloc` calls `brk()` or `mmap()`. Every heap allocation goes through the system allocator (ptmalloc2 on Linux by default). The allocator maintains a **free list** of previously freed blocks. The two costs of allocation are: (1) finding a free block (or calling the kernel if none), and (2) the cache miss on the returned memory. Custom allocators eliminate one or both.

---

## How It Moves — Default Allocator (ptmalloc2)

```
operator new(size):
  → calls malloc(size)
  → ptmalloc2 checks per-thread arena free bins
  → if a bin has a block of suitable size: return it
      cost: ~30ns (no syscall, but cache miss on the returned block)
  → if no suitable free block: grow the heap
      → brk() for small requests: extends the heap segment (+/- 128KB at a time)
      → mmap(MAP_ANONYMOUS) for large requests (>128KB): new mapping
      cost: ~100-500ns (syscall + TLB miss on new page)
  → return pointer to newly allocated block (surrounded by bookkeeping metadata)
```

**The bookkeeping overhead:** ptmalloc stores a header (chunk size, flags) immediately before the returned pointer. An 8-byte allocation becomes a 16-byte+ chunk in the allocator's view. Small allocations cluster in 8-16 byte bins; large allocations are served from the wilderness at the top of the heap.

---

## The Hidden Allocation Tax

Every heap allocation carries three hidden costs:

1. **Allocator overhead** (~30-100ns): free-list lookup, metadata update
2. **Cold cache miss** (~100-200ns): newly allocated memory is not in L1/L2 cache
3. **Fragmentation**: interleaved small/large allocations leave holes; 10-30% overhead is common

For tight loops: even if the allocator is "fast," the allocation itself causes a cache miss on the first access. Amortizing allocations (pools, arenas) eliminates both the allocator overhead and the cold-cache penalty.

---

## Arena Allocator — The Pattern

```cpp
class Arena {
    char buf[1 << 20];   // 1MB pre-allocated slab
    size_t offset = 0;

    void* alloc(size_t size, size_t align = 8) {
        offset = (offset + align - 1) & ~(align - 1);  // align
        void* p = buf + offset;
        offset += size;
        return p;
    }
    void reset() { offset = 0; }  // free everything at once
};
```

```
Arena allocation path:
  → pointer bump (add size to offset)
  → return pointer
  Cost: ~1ns, no cache miss if the arena is in L1/L2
  
Arena free path:
  → reset(): single integer reset
  → or: no individual frees needed
  Cost: ~0ns
```

**When to use:** a group of objects with the same lifetime (a request, a frame, a parser invocation). Allocate everything into the arena, process, then `reset()`. Zero fragmentation, cache-warm, no per-object free.

---

## Pool Allocator — Fixed-Size Objects

```cpp
template<typename T, size_t N>
class Pool {
    union Slot { T obj; Slot* next; };
    Slot slots[N];
    Slot* free_head;
    
    Pool() {
        for (int i = 0; i < N-1; i++) slots[i].next = &slots[i+1];
        slots[N-1].next = nullptr;
        free_head = &slots[0];
    }
    
    T* alloc() {
        if (!free_head) return nullptr;
        Slot* s = free_head;
        free_head = s->next;
        return &s->obj;
    }
    
    void free(T* p) {
        reinterpret_cast<Slot*>(p)->next = free_head;
        free_head = reinterpret_cast<Slot*>(p);
    }
};
```

```
Pool allocation path:
  → pop from free list (two pointer operations)
  → return pointer
  Cost: ~2ns

Pool free path:
  → push back to free list
  Cost: ~2ns
```

**When to use:** high-frequency allocation/deallocation of one fixed-size type (network packets, command objects, timer entries). No fragmentation, O(1) alloc and free, objects reuse warm cache lines.

---

## tcmalloc / jemalloc — Thread-Caching Allocators

Default ptmalloc2 uses a global lock (or per-arena lock). Under heavy multi-threaded allocation:

```
Thread 1: malloc() → lock arena → search bins → unlock arena
Thread 2: malloc() → wait for lock → 200ns wasted
```

tcmalloc/jemalloc give each thread its own small-object cache:

```
Thread 1: malloc(32) → check thread-local freelist → pop → return (~5ns, no lock)
Thread 1: free(32-byte block) → push to thread-local freelist → return (~3ns, no lock)
```

When the thread-local freelist overflows, it returns a batch to the central cache (infrequent). Lock contention vanishes for small objects.

---

## Hidden Costs Summary

| Allocator | Alloc cost | Free cost | Fragmentation | Use case |
|---|---|---|---|---|
| ptmalloc2 (default) | 30-500ns | 30-100ns | Yes | General |
| tcmalloc/jemalloc | 5-20ns | 3-10ns | Yes | Multi-threaded |
| Arena | ~1ns | 0 (reset) | None | Same-lifetime group |
| Pool | ~2ns | ~2ns | None | Fixed-size hot path |
| Stack (`alloca`) | 0 | 0 | None | Small, bounded-size |

---

## Related Machines

→ [[08 - malloc and free — The Machine]]
→ [[01 - Process Memory Layout — The Machine]]
→ [[09 - Cache Hierarchy — The Machine (deep)]]
→ [[17 - std::vector — The Machine]]
→ [[02 - Smart Pointers]]
