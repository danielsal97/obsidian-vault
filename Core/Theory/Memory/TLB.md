# TLB — Translation Lookaside Buffer

The TLB is a small, extremely fast cache inside the MMU that stores recent virtual-to-physical address translations. Without it, every memory access would require 4 DRAM reads (the page table walk) before the actual access — a 5× slowdown on top of every load/store.

---

## Structure

```
L1 DTLB (data):       64 entries,   4-way set-associative, ~1 cycle latency
L1 ITLB (instruction): 128 entries, ~1 cycle latency
L2 TLB (unified):    1536 entries,  ~7 cycle latency

Each entry stores:
  VPN (Virtual Page Number) + PCID → PFN (Physical Frame Number) + permissions
```

With 64 entries and 4KB pages, L1 DTLB covers 64 × 4KB = **256KB** of memory with no translation overhead.

---

## TLB Hit vs Miss

```
Memory access:
  Virtual address → split into VPN + offset
       ↓
  TLB lookup (hardware, fully parallel across all entries)
       ├── HIT (VPN matches a cached entry)
       │     → read PFN → physical address = PFN + offset
       │     → check permissions (WRITABLE, NX, USER)
       │     → proceed to cache hierarchy
       │     Total: ~1–4 cycles
       │
       └── MISS
             → hardware page table walk (4 DRAM reads worst case)
             → find PTE → load PFN into TLB (evict LRU entry)
             → retry access
             Total: ~40–400 cycles
```

---

## TLB Invalidation

TLB entries must be invalidated when page table entries change:

**Context switch (different process):**
```c
// Kernel: load new CR3
asm volatile("mov %0, %%cr3" : : "r"(new_pgd_pa));
// Without PCID: all TLB entries flushed
// With PCID: entries tagged — old process entries stale but don't match new PCID
```

**`mprotect()` / `munmap()`:**
```c
// Kernel calls invlpg on every affected virtual address:
asm volatile("invlpg (%0)" : : "r"(va));
// Removes just that one TLB entry
// On SMP: must also send IPI to all other CPUs (TLB shootdown)
```

**TLB shootdown on multi-core:**
1. CPU 0 modifies a PTE
2. CPU 0 sends IPI to CPUs 1–63 (all other cores)
3. CPUs 1–63 pause, execute `invlpg`, acknowledge
4. CPU 0 continues
Cost: ~1–10 µs × number of CPUs. Reason why frequent `mprotect()` in multi-threaded code is expensive.

---

## PCID — Process Context Identifier

Linux (since kernel 4.14 on PCID-capable CPUs) assigns each process a 12-bit PCID. TLB entries are tagged with the PCID. On `CR3` load:
- Old PCID entries remain valid and are reused when the same process runs again
- New process starts with any old entries for that PCID already invalidated

Effectively: TLB acts as an N-process associative cache instead of being flushed on every switch. Significant speedup on syscall-heavy / context-switch-heavy workloads.

---

## Huge Pages and TLB Pressure

```
4KB pages:  1MB buffer = 256 TLB entries needed
2MB pages:  1MB buffer = 1 TLB entry needed
```

A database doing sequential scans over a 1GB buffer with 4KB pages would need 262,144 TLB entries — far beyond the ~1536 available. Every access past the working set causes a TLB miss. With 1GB huge pages, that's 1 entry.

---

## Measuring TLB Performance

```bash
# perf events for TLB:
perf stat -e dTLB-load-misses,iTLB-load-misses ./program

# Or on Intel:
perf stat -e mem_inst_retired.stlb_miss_rd,mem_inst_retired.stlb_miss_wr ./program
```

---

## Understanding Check

> [!question]- If L1 DTLB has 64 entries and pages are 4KB, what is the maximum working set size that can be accessed with zero TLB misses?
> 64 entries × 4KB per page = 256KB. If a tight loop accesses data that fits within 256KB of non-contiguous pages, all TLB entries can be hot simultaneously. In practice, with set-associativity, aliasing can cause evictions even within 256KB if pages map to the same TLB set — real effective coverage is somewhat less.

> [!question]- Why is TLB shootdown expensive on a 64-core machine, even when only one page's permission is being changed?
> Changing one PTE means every CPU that has cached that VPN→PFN mapping must immediately invalidate it — otherwise CPUs could use a stale (now-wrong) translation. The kernel sends an IPI to all 63 other cores. Each core must stop what it's doing, handle the IPI, execute `invlpg`, and acknowledge. Meanwhile the initiating CPU waits for all acknowledgements before continuing. At 64 cores, you briefly pause 63 execution streams for a single `mprotect()` call. Minimizing `mprotect()` and `mmap()`/`munmap()` frequency is a real concern for high-performance memory management.

> [!question]- A process switches between 8 threads rapidly (100,000 context switches/second). With PCID disabled vs enabled, how does this affect TLB behavior?
> Without PCID: every context switch (even between threads of *different processes*) flushes the entire TLB. 100,000 switches/second = 100,000 TLB flushes/second. After each flush, the new thread's first ~1536 memory accesses are TLB misses. With PCID: entries are tagged per process. Thread switches within the same process never flush the TLB. Switches between processes preserve entries under different PCIDs. The TLB functions more like a shared cache across all recent processes rather than being wiped clean 100,000 times per second.

---

**Mental Model:** [[TLB — The Machine]]
**Related:** [[MMU]], [[Page Walk]], [[Paging]], [[Cache Hierarchy]], [[Virtual Memory]]
