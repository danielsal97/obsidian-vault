# Page Walk — The Machine

## The Model
A four-story filing cabinet. Each drawer is indexed by 9 bits of the virtual address. To find the physical room number, you open the top drawer with the first 9 bits, find an entry pointing to the second cabinet, open its drawer with the next 9 bits, and so on — four lookups to get the physical frame. Each lookup is a memory read, so a single page walk = 4 memory accesses before you can even do the one you wanted.

## How It Moves

```
Virtual address: 0x00007f3a4000_1234
Binary decomposition (x86-64, 4-level):
  bits [47:39] = PGD index  (9 bits) = points into top-level table
  bits [38:30] = PUD index  (9 bits) = page upper directory
  bits [29:21] = PMD index  (9 bits) = page middle directory
  bits [20:12] = PTE index  (9 bits) = page table entry
  bits [11:0]  = offset     (12 bits)= byte within the 4KB page

Walk:
  CR3 register → physical address of PGD
      ↓
  PGD[47:39] → physical address of PUD table
      ↓
  PUD[38:30] → physical address of PMD table
      ↓
  PMD[29:21] → physical address of PTE table
      ↓
  PTE[20:12]:
      PRESENT=1 → physical frame number → + offset = physical address ✓
      PRESENT=0 → PAGE FAULT (kernel allocates frame, sets PTE, retry)
```

**Cost:** each arrow above is a memory read (~100 cycles if DRAM). Full walk = 4 reads = ~400 cycles. This is why the TLB exists — the walk only happens on TLB miss.

**Hardware page walker:** on modern x86, the CPU's hardware page walker (part of the MMU) performs all 4 reads automatically in hardware. Software is not involved unless a page fault occurs.

## The Blueprint

- **Each level is a 4KB page of entries**: 512 entries × 8 bytes = 4096 bytes = one page. A 4-level tree can address 512^4 × 4KB = 256 TB of virtual space.
- **Huge pages short-circuit the walk**:
  - 2MB huge page: PMD entry points directly to a 2MB frame, skip the PTE level — 3 reads not 4
  - 1GB huge page: PUD entry points to a 1GB frame — 2 reads not 4
- **`cr3` physical address**: the PGD physical address is stored in `CR3`. This is a physical address (not virtual) — the MMU needs it before it can do any translation.
- **Page table pages are also in RAM**: the walk reads from RAM. If the PGD, PUD, or PMD pages are cold (evicted from cache), the walk takes even longer.

## Where It Breaks

- **Cold page tables**: page table pages themselves can be evicted from CPU cache. A process with a huge, sparse virtual address space has large page tables that rarely fit in L1/L2 cache — every TLB miss triggers 4 slow DRAM reads.
- **Kernel mapped at fixed address**: to avoid the kernel needing its own walk just to do the walk, kernel page tables are always pinned in memory (never paged out).
- **Meltdown**: speculative execution reads physical frame addresses from page table entries before PRESENT/permission checks complete → information leakage. KPTI mitigation removes kernel PTEs from user-mode page tables entirely.

## In LDS

LDS accesses the same hot buffers repeatedly — `m_data`, the socket fd table, the WPQ nodes. These addresses are TLB-hot after the first access. The page table entries for these pages are likely L2/L3 cache-hot too. If LDS were redesigned to use a large sparse virtual address space (e.g., one mmap region per connection, each 1GB apart), the page table would become large and cold — TLB misses would trigger expensive walks.

## Validate

1. A 64-bit process maps 1TB of virtual address space (sparse mmap). Estimate the number of PTE pages needed. Why might this hurt TLB miss cost even if actual physical memory is small?
2. Why must `CR3` hold a **physical** address rather than a virtual address?
3. On a system with 4KB pages and a 4-level page table, what is the maximum virtual address space a single process can use? Show the math.

## Connections

**Theory:** [[Core/Theory/Memory/06 - Page Walk]]
**Mental Models:** [[MMU — The Machine]], [[TLB — The Machine]], [[Paging — The Machine]], [[Virtual Memory — The Machine]]
**Related:** [[Cache Hierarchy — The Machine]], [[Process Memory Layout — The Machine]]
