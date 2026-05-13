# Page Walk

A page walk is the hardware process of traversing the multi-level page table tree to resolve a virtual address to a physical frame number. It happens on every TLB miss — which means any memory access after a context switch, or to a rarely-used page.

---

## 4-Level Page Table (x86-64)

Virtual address breakdown:

```
63        48 47      39 38      30 29      21 20      12 11        0
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ sign ext │  PGD idx │  PUD idx │  PMD idx │  PTE idx │  offset  │
│  16 bits │   9 bits │   9 bits │   9 bits │   9 bits │  12 bits │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

- Bits 63–48: must sign-extend bit 47 (canonical form) — otherwise GPF
- Each index: 9 bits → 512 entries per table × 8 bytes = 4096 bytes = one page
- Offset: 12 bits → 4096 byte page (2^12)

---

## Walk Sequence

```
CR3  → physical address of PGD (Page Global Directory)
   ↓
PGD[bits 47:39]  → physical address of PUD table
   ↓                (if entry not PRESENT → segfault)
PUD[bits 38:30]  → physical address of PMD table
   ↓
PMD[bits 29:21]  → physical address of PTE table
   ↓                (if PS=1 here → huge page, stop — 2MB page)
PTE[bits 20:12]  → physical frame number (PFN)
   ↓
physical address = PFN × 4096 + offset (bits 11:0)
```

Each arrow = one memory read. Full walk = **4 memory reads** before the actual access.

---

## Huge Pages Short-Circuit the Walk

```
2MB huge page (PMD points directly to 2MB frame):
  CR3 → PGD → PUD → PMD (PS=1) → physical address   (3 reads)

1GB huge page (PUD points directly to 1GB frame):
  CR3 → PGD → PUD (PS=1) → physical address           (2 reads)
```

Huge pages: fewer levels = fewer memory reads per TLB miss AND fewer TLB entries needed.

---

## Hardware Page Walker

On x86, the page walk is performed entirely in hardware by the MMU's **page table walker unit**. The CPU does not execute any software instructions during the walk — it's a dedicated finite state machine that reads memory autonomously. Software is only involved if a fault is raised (PRESENT=0, protection violation).

This hardware walker also uses the **page walk cache** (a micro-TLB for intermediate page table entries) to avoid reading PGD/PUD/PMD on consecutive accesses to pages in the same region.

---

## Cost Breakdown

| Event | Typical cycles |
|---|---|
| TLB hit (no walk needed) | ~1–4 |
| Page walk, all tables L1-cached | ~20–40 |
| Page walk, tables in DRAM | ~100–400 |
| Page walk + page fault (minor) | ~1,000–10,000 |
| Page walk + page fault (major/disk) | ~1,000,000+ |

---

## Why Page Tables Are in RAM

The page table pages themselves are regular physical pages. On a system under memory pressure, they can be evicted — except kernel page tables, which are pinned. When a walk needs to read a page table page that's not in L1/L2/L3 cache, it stalls for a DRAM read (~100+ cycles), compounding TLB miss cost.

A process with a huge sparse virtual address space (many mmap regions) has large page tables. Those page table pages may be cold, making TLB miss resolution extremely slow.

---

## Observing Page Walks

```bash
# Count TLB misses (proxy for page walks):
perf stat -e dTLB-load-misses,dTLB-store-misses ./program

# Page fault counts:
/usr/bin/time -v ./program
# → "Minor (reclaiming a frame) page faults"
# → "Major (requiring I/O) page faults"
```

---

## Understanding Check

> [!question]- Why must CR3 store a physical address, not a virtual address?
> The page walk uses CR3 as the starting point to resolve virtual addresses. If CR3 were a virtual address, the MMU would need to translate it — which requires the page table — before it could even begin the page table walk. That's circular. Using a physical address in CR3 breaks the dependency: the MMU can directly read the PGD without any prior translation.

> [!question]- A 4-level page table walk takes 4 memory reads. If all 4 tables are in L3 cache (40-cycle latency each), what is the total walk cost, and how does that compare to a TLB hit?
> 4 × 40 cycles = 160 cycles for the walk itself, plus 40 cycles for the actual data access = ~200 cycles total. A TLB hit costs ~1–4 cycles for the lookup plus ~4 cycles for L1 data = ~5 cycles total. The TLB hit path is roughly **40× faster** than even a fully-cached page walk. This is why TLB hit rate is critical — a few percent of TLB misses on a hot loop can dominate total execution time.

> [!question]- What is the page walk cache, and how does it differ from the TLB?
> The TLB caches the final result of a full walk: VPN → PFN. The page walk cache (also called paging-structure cache) caches intermediate results: a PGD entry pointing to a PUD, or a PUD entry pointing to a PMD. On a TLB miss, the hardware walker first checks the page walk cache before restarting from CR3. If the top 2 levels are cached, only the bottom 2 reads are needed. The page walk cache is opaque to software but implicitly flushed with `invlpg` and `CR3` writes.

---

**Mental Model:** [[Page Walk — The Machine]]
**Related:** [[MMU]], [[TLB]], [[Paging]], [[Virtual Memory]]
