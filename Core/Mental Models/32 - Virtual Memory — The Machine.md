# Virtual Memory — The Machine

## The Model
A personal address book where every entry looks like it's in your private building — but the actual rooms are shared, rented, or don't physically exist yet. Each process believes it owns the entire 64-bit address space. The OS and MMU maintain the illusion: virtual addresses are mapped to physical RAM transparently, on demand, and with per-process isolation.

## How It Moves

```
Process A                         Process B
Virtual addr 0x7fff1000           Virtual addr 0x7fff1000
        ↓                                 ↓
      MMU                               MMU
        ↓ (different page tables)          ↓
Physical frame 0x1A3000           Physical frame 0x8F2000
```

Same virtual address, completely different physical location. Neither process can reach the other's frames — the kernel controls all page table mappings.

**Lifecycle of a virtual page:**

```
1. Process calls malloc(4096) or stack grows
   → malloc calls mmap()/sbrk() to request virtual pages from kernel
   → kernel creates virtual mapping (PTE with PRESENT=0, demand-zero)
   → malloc returns a pointer — no physical RAM allocated yet

2. Process writes *ptr = 42
   → CPU issues virtual address → MMU checks TLB → miss
   → MMU walks page table → PRESENT bit = 0 → PAGE FAULT
   → kernel: allocates physical frame, zero-fills it, sets PTE PRESENT=1
   → execution resumes — write completes

3. Physical RAM pressure:
   → kernel's swapper picks cold pages → writes to swap disk → marks PTE PRESENT=0
   → on next access: PAGE FAULT again → read from swap → resume

4. Process exits or munmap():
   → kernel unmaps PTEs → physical frames returned to free list
```

## The Blueprint

- **Private virtual address space**: each process gets a full 64-bit space (only ~128TB usable on x86-64). No process can access another's pages without explicit sharing (mmap with MAP_SHARED).
- **Demand paging**: physical RAM is only allocated on first write, not on virtual allocation. This is why `malloc(1GB)` is instant.
- **Copy-on-write (COW)**: after `fork()`, parent and child share the same physical pages, read-only. On first write by either process, the kernel copies just that page — fork is O(1), not O(address space).
- **ASLR (Address Space Layout Randomization)**: the kernel randomizes stack, heap, and library base addresses on every run. Makes exploits harder; makes raw address comparisons across runs meaningless.
- **Overcommit**: Linux by default allows allocating more virtual memory than physical RAM exists. If the system runs out of physical pages, the OOM killer terminates a process.

## Where It Breaks

- **Segfault (SIGSEGV)**: accessing a virtual address with no mapping — null, unmapped gap, stack overflow into guard page
- **OOM kill**: overcommitted memory plus actual use — kernel kills a process without warning
- **ASLR exploit**: attacker guesses randomized addresses; mitigated by ASLR + stack canaries + NX bit
- **Swap thrashing**: working set larger than physical RAM → constant page faults → performance collapse

## In LDS

When LDS starts, the kernel creates its virtual address space from the ELF binary. The `std::vector<char> m_data` in `LocalStorage` lives in the heap region — virtual pages are mapped by `new[]`/`malloc` and physical frames arrive on first write. Each worker thread's stack is a separate virtual region in the mmap area. All threads share the same virtual address space (`.text`, `.data`, heap), enforced as a single process by the kernel.

## Validate

1. LDS calls `malloc(1MB)` for a read buffer. No data has been written yet. How much physical RAM has been consumed?
2. After `fork()`, both parent and child have the same `m_data` pointer value. Do they point to the same physical frame? What happens when one writes to it?
3. What does `cat /proc/PID/maps` show that `top`'s VIRT vs RES columns don't?

## Connections

**Theory:** [[Core/Theory/Memory/03 - Virtual Memory]]
**Mental Models:** [[Process Memory Layout — The Machine]], [[Paging — The Machine]], [[MMU — The Machine]], [[malloc and free — The Machine]], [[mmap — The Machine]]
**Related:** [[TLB — The Machine]], [[Page Walk — The Machine]], [[Cache Hierarchy — The Machine]]
