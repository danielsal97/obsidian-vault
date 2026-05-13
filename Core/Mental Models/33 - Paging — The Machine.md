# Paging — The Machine

## The Model
Memory cut into uniform 4KB tiles. The OS never moves individual bytes — it moves whole tiles between RAM and disk. You can only allocate in 4KB increments. The MMU maps virtual tiles to physical tiles via a lookup table (the page table). When a tile isn't in RAM, the CPU faults and waits for the OS to fetch it.

## How It Moves

```
Virtual Address (64-bit x86-64):
┌────────┬───────┬───────┬───────┬───────┬──────────────┐
│ unused │  PGD  │  PUD  │  PMD  │  PTE  │    offset    │
│  16b   │   9b  │   9b  │   9b  │   9b  │     12b      │
└────────┴───────┴───────┴───────┴───────┴──────────────┘
  bits 63-48  47-39  38-30  29-21  20-12       11-0

The 12-bit offset = byte position within the 4KB page (2^12 = 4096).
The 4 × 9-bit indices walk the 4-level page table tree.
```

**Page fault flow:**
```
CPU issues virtual address → MMU looks up TLB → miss
  → MMU walks page table tree:
      CR3 register → PGD[47:39] → PUD[38:30] → PMD[29:21] → PTE[20:12]
  → PTE PRESENT bit = 0 → PAGE FAULT raised
      kernel page fault handler:
        case 1: demand-zero page (new heap/stack)
                → allocate physical frame, zero-fill, set PTE PRESENT=1
        case 2: page on swap disk
                → allocate frame, read from swap, set PTE
        case 3: invalid address (NULL, gap)
                → send SIGSEGV to process
  → TLB updated → execution resumes
```

**Page fault cost:** ~1–10 µs for a minor fault (kernel allocates frame), ~1–100 ms for a major fault (disk read from swap).

## The Blueprint

- **Page size**: 4KB standard; huge pages = 2MB or 1GB (skip levels of the page table walk, reduce TLB pressure)
- **Page Table Entry (PTE)** bits: PRESENT (in RAM), WRITABLE, USER/SUPERVISOR, NX (no-execute), DIRTY, ACCESSED, physical frame number
- **Guard pages**: unmapped pages placed at stack bottom — stack overflow hits the guard → SIGSEGV immediately instead of silently corrupting heap
- **mmap** maps files page by page — on read of a mapped page, kernel reads from file into a frame; dirty pages written back by the page cache
- **Copy-on-write**: two PTEs point to the same physical frame, both read-only. On write → fault → kernel copies the frame → both PTEs now point to their own copies

## Where It Breaks

- **Thrashing**: working set larger than physical RAM → constant page faults → CPU spends more time handling faults than doing work
- **Huge page fragmentation**: 2MB huge pages require 2MB-aligned contiguous physical frames — hard to satisfy on fragmented memory
- **mlock() needed for real-time**: real-time processes call `mlock()` to pin pages into RAM — prevents page faults during time-critical paths

## In LDS

Every memory access in LDS is paged. The `.text` segment is backed by the ELF file — kernel demand-pages it on first execution. The `m_data` vector buffer is backed by anonymous pages (demand-zero, allocated on first write). If LDS were deployed on a memory-constrained device, the heap pages could be swapped — `mlock()` on hot buffers prevents this.

## Validate

1. LDS has a `char buf[8192]` local variable. How many pages does this span? What happens if the stack pointer moves across a page boundary for the first time?
2. Why does a `read()` into a just-`mmap`'d file region cause a major page fault but subsequent reads to the same region do not?
3. What is a "minor" vs "major" page fault, and how can you observe the difference with `/usr/bin/time -v`?

## Connections

**Theory:** [[Core/Theory/Memory/04 - Paging]]
**Mental Models:** [[Virtual Memory — The Machine]], [[MMU — The Machine]], [[TLB — The Machine]], [[Page Walk — The Machine]], [[Process Memory Layout — The Machine]]
**Related:** [[mmap — The Machine]], [[Stack vs Heap — The Machine]]
