# Paging

Paging divides virtual and physical memory into fixed-size units called **pages** (4KB by default on x86-64). The OS manages memory in page-granular chunks — it can't move 1 byte to disk; it moves whole pages.

---

## Page Size

```
Standard:    4 KB  (4096 bytes)
Huge page:   2 MB  (512 × 4KB — skips PTE level in page walk)
1GB page:    1 GB  (skips both PMD and PTE levels)
```

The 4KB page size was chosen decades ago as a balance between:
- Small → less wasted RAM (internal fragmentation) when a process needs just a few bytes
- Large → fewer TLB entries needed, less page table overhead

---

## Page Table Entry (PTE)

Each PTE is 8 bytes on x86-64 and holds:

```
Bit  0:    PRESENT     — is the page in physical RAM?
Bit  1:    WRITABLE    — can this page be written?
Bit  2:    USER        — accessible from ring 3 (user mode)?
Bit  3:    PWT         — page-level write-through cache
Bit  4:    PCD         — page cache disable
Bit  5:    ACCESSED    — set by MMU on first access (used by page replacement)
Bit  6:    DIRTY       — set by MMU on write (determines if swap-out needs write)
Bit  7:    PS          — page size (for huge pages at PMD/PUD level)
Bit 63:    NX          — no execute (hardware-enforced DEP/W^X)
Bits 12–51: Physical Frame Number (PFN)
```

---

## Page Fault Types

When PRESENT=0, the CPU raises a page fault (interrupt 14). The kernel's fault handler determines why:

| Cause | Action |
|---|---|
| Demand-zero page (new heap/stack) | Allocate frame, zero-fill, set PTE |
| Copy-on-write (after fork, first write) | Copy frame, update PTE, continue |
| Swapped-out page | Read from swap, install PTE |
| File-backed mmap page | Read page from file, install PTE |
| Stack growth | Grow VMA, allocate frame |
| NULL or unmapped address | Send SIGSEGV |
| Permission violation (write to RO page) | Send SIGSEGV |

---

## Guard Pages

A guard page is an intentionally unmapped page placed at:
- Bottom of each thread stack
- Below the kernel stack

Any stack overflow hits the guard page → page fault with an unmapped address → SIGSEGV. Without a guard page, the stack would silently grow into the heap, corrupting heap data.

```bash
# See guard pages in /proc/PID/maps:
# A page with no permissions (---p) at the bottom of a stack region is the guard page
```

---

## Huge Pages

```c
// Explicit huge page via mmap:
void* p = mmap(NULL, 2*1024*1024,
               PROT_READ|PROT_WRITE,
               MAP_PRIVATE|MAP_ANONYMOUS|MAP_HUGETLB, -1, 0);

// Transparent Huge Pages (THP) — kernel promotes automatically:
// Check: cat /sys/kernel/mm/transparent_hugepage/enabled
```

Benefits: one TLB entry covers 2MB instead of 512 entries covering 2MB. 512× TLB pressure reduction for large dense allocations (databases, video buffers).

Drawback: 2MB physical contiguous frames must exist — hard to satisfy on fragmented memory. Internal fragmentation if allocation is smaller than 2MB.

---

## Page Replacement (LRU Approximation)

When physical RAM is full and a new page must be brought in:
1. Kernel's page replacement algorithm selects a victim page
2. If DIRTY bit is set → write to swap before evicting
3. PTE of victim is updated: PRESENT=0
4. Physical frame given to new page
5. If victim is accessed again → major page fault → read back from swap

---

## Observing Paging

```bash
# Page fault statistics:
/usr/bin/time -v ./program   # "Major (requiring I/O) page faults" and "Minor (reclaiming a frame) page faults"

# Swap usage:
vmstat 1          # si (swap in), so (swap out) columns

# Per-process page stats:
/proc/PID/status  # VmRSS, VmPTE (page table memory itself)
/proc/PID/smaps   # per-region: Size, Rss, Shared_Clean, Private_Dirty, Swap
```

---

## Understanding Check

> [!question]- Why is a minor page fault much cheaper than a major page fault, and when does each occur?
> A minor fault doesn't require disk I/O — the kernel satisfies it from memory: allocating and zeroing a fresh frame (demand-zero), or finding a page already in the page cache from a previous mapping of the same file. A major fault requires reading from disk — either a swapped-out anonymous page or a file-backed page never previously read. Minor faults cost ~1–10 µs. Major faults cost ~1–100 ms. Most heap and stack growth causes minor faults; swapping and first file-backed mmap accesses cause major faults.

> [!question]- Why does the kernel track the DIRTY bit in each PTE, and what happens if a clean page is evicted vs a dirty page?
> A clean page's content in RAM is identical to what's on disk (it was never written, or was already written back). Evicting a clean page requires only removing the PTE mapping — no disk write needed. A dirty page has been modified since it was last written to disk — evicting it requires writing the modified content to swap or updating the file (for file-backed mappings). Skipping the dirty check and always writing on eviction would cause unnecessary disk I/O; never checking it would lose data. The DIRTY bit is set by the MMU hardware on any write access.

> [!question]- A process calls `mmap(MAP_ANONYMOUS, 100MB)`. When does the 100MB of physical RAM actually get used?
> None of it is used at mmap time — the kernel creates a virtual memory area (VMA) record describing the 100MB range, but installs no PTEs (or installs PTEs with PRESENT=0). Physical frames are allocated one 4KB page at a time as each page is first written. If only 1MB of the 100MB is ever touched, only 256 physical frames (~1MB) are ever allocated. The difference between `VmVirt` and `VmRSS` in `/proc/PID/status` captures this exactly.

---

**Mental Model:** [[Paging — The Machine]]
**Related:** [[Virtual Memory]], [[MMU]], [[TLB]], [[Page Walk]], [[Process Memory Layout]]
