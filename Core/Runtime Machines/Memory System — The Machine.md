# Memory System — The Machine

## The Model

Memory has four levels, each 10-100x slower than the previous. Your program lives at L1 cache (0.5ns). DRAM is 100ns. A page fault to bring in a new page is 1μs (if the OS has a free frame) to 10ms (if it needs to evict a dirty page). Understanding performance means understanding which level you're hitting.

```
L1 cache      — 32KB, 0.5ns     ← your hot loop lives here
L2 cache      — 256KB, 3ns
L3 cache      — 8MB, 10ns
DRAM          — unlimited, 100ns ← malloc returns memory here
Page fault    — N/A, 1-10μs     ← first access to a new page
```

## How It Moves — malloc()

```
malloc(256)
      │
      ▼
allocator checks free list for a 256-byte block
  → found: return it (nanoseconds)
  → not found: need more heap memory
      │
      ▼
allocator calls brk() / sbrk() OR mmap(MAP_ANONYMOUS)
  → kernel: extends virtual address space
  → no physical page allocated yet — just virtual address range reserved
      │
      ▼
malloc returns pointer (virtual address)
      │
      ▼
first write to that address:
  → CPU tries to translate virtual → physical (walks page table)
  → page table entry: NOT PRESENT
  → CPU raises page fault exception → kernel takes over
      │
      ▼
Kernel page fault handler:
  → verify the address is in a valid VMA (else: SIGSEGV)
  → allocate a physical frame from free list
  → zero-fill it (security: don't expose previous process data)
  → insert page table entry: virtual → physical mapping
  → return to user — the write that faulted now completes
```

## How It Moves — Cache Miss

```
CPU executes: mov rax, [ptr]   (load from address ptr)
      │
      ▼
CPU checks L1 cache: miss
  → check L2: miss
  → check L3: miss
  → send request to memory controller: fetch cache line (64 bytes) from DRAM
  → wait ~100ns (stall, or out-of-order execution continues if independent work)
  → cache line arrives, fills L1, L2, L3
  → load completes
      │
      ▼
next access to nearby address (within 64 bytes): L1 hit → 0.5ns
```

## Where Allocations Fail

- `malloc()` returns NULL: virtual address space exhausted, or OS out of physical memory and swap
- SIGSEGV on access: valid virtual address but page not mapped (bug) or stack overflow (guard page fault)
- Heap fragmentation: many small allocs/frees leave holes — allocator can't satisfy a large request even with free bytes scattered

## Links

→ [[02 - Memory - malloc and free]] — allocator internals
→ [[01 - Process Memory Layout]] — virtual address space regions
→ [[03 - Virtual Memory]] — page tables, demand paging
→ [[04 - Paging]] — page fault handling in detail
→ [[07 - TLB]] — address translation cache
→ [[08 - Cache Hierarchy]] — L1/L2/L3 details
→ [[04 - Paging — The Machine]] — page fault runtime story
