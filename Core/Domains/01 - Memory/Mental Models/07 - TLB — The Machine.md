# TLB — The Machine

## The Model
A cheat sheet taped to the MMU's desk. The full answer (walking the 4-level page table) takes dozens of memory accesses. The cheat sheet holds the last ~64–1536 answers. If your virtual address is on the cheat sheet — done in 1 cycle. If not — look up the full table, write the answer on the cheat sheet, evict an old entry.

## How It Moves

```
Virtual address arrives at MMU
        ↓
TLB lookup (hardware, parallel, ~1 cycle)
  ├── HIT: VPN matches a cached entry
  │         → read physical frame number from entry
  │         → check permissions (WRITABLE, NX, USER)
  │         → physical address = frame_number + page_offset
  │         → send to cache hierarchy  (total: ~1–4 cycles)
  │
  └── MISS: no matching entry
            → hardware page table walk (see Page Walk)
            → finds PTE → loads physical frame number
            → installs new TLB entry (evicts LRU entry if full)
            → retry the access  (total: ~10–100+ cycles)
```

**TLB structure on x86-64 (typical):**
```
L1 ITLB: ~128 entries for instruction fetches
L1 DTLB: ~64  entries for data accesses
L2 TLB:  ~1536 unified entries (shared ITLB+DTLB)
Each entry: VPN → PFN + permission bits
```

## The Blueprint

- **TLB flush on context switch**: when the kernel loads a new `CR3`, the TLB is flushed (all entries invalid). The new process starts with a cold TLB — first accesses to each page are TLB misses. **This is the hidden cost of context switching.**
- **ASID (Address Space Identifier)**: each TLB entry can be tagged with an ASID. Kernel can switch processes without flushing TLB entries for the old process — they'll simply miss if the ASID doesn't match. Reduces context switch overhead significantly.
- **TLB shootdown**: when one CPU modifies a PTE, other CPUs may still have the old mapping cached in their TLBs. The OS sends an IPI (Inter-Processor Interrupt) to all CPUs to flush that entry. On a 64-core machine, this stalls 63 cores briefly.
- **Huge pages reduce TLB pressure**: a 2MB huge page covers 512 × 4KB pages with a single TLB entry. Dense memory accesses (matrix multiply, video buffers) benefit enormously.

## Where It Breaks

- **TLB thrashing**: working set spans more unique pages than TLB entries → every access is a miss → performance cliff. Typical 4KB pages: a 1MB buffer = 256 pages, fits comfortably. A 10MB scatter-gather pattern = 2560 pages → misses.
- **Kernel KPTI overhead**: Meltdown mitigation uses two sets of page tables (kernel and user). Every syscall requires a `CR3` switch + TLB flush → 5–30% overhead on syscall-heavy workloads.
- **`mprotect()` stalls all cores**: changing a page permission requires TLB shootdown — all CPUs must flush that entry.

## In LDS

The LDS ThreadPool keeps worker threads in the same process — they share `CR3` and TLB entries. Switching between workers doesn't flush the TLB. If LDS were redesigned as multiple processes (one per worker), each context switch would flush the TLB, making thread-local stack accesses cold on the first few accesses after each switch.

## Validate

1. LDS processes 1000 small requests per second, each touching a 4KB buffer. Is the TLB hot or cold for those buffer accesses? Why?
2. If LDS is pinned to 2 CPU cores and the kernel switches between 8 worker threads, how many TLB flushes occur per second if ASID is NOT used?
3. Why would switching to 2MB huge pages for the `m_data` buffer in `LocalStorage` improve TLB hit rate?

## Connections

**Theory:** [[07 - TLB]]
**Mental Models:** [[MMU — The Machine]], [[Page Walk — The Machine]], [[Paging — The Machine]], [[Cache Hierarchy — The Machine]]
**Related:** [[Virtual Memory — The Machine]], [[Process Memory Layout — The Machine]]
