# MMU — The Machine

## The Model
A hardware customs officer at the border between your code and physical RAM. Every memory access your program makes passes through the MMU. It checks your virtual address against the current process's page tables, translates it to a physical address, enforces permissions (read/write/execute), and either approves or raises a fault — all in hardware, every single cycle.

## How It Moves

```
CPU core issues virtual address  (e.g. 0x00007f3a4000)
        ↓
      MMU
        ├── check TLB (Translation Lookaside Buffer)
        │     HIT  → get physical address in ~1 cycle → send to cache/RAM
        │     MISS → initiate page table walk (see Page Walk)
        │               → load PTE → cache in TLB → send physical addr
        ↓
  Permission check on PTE bits:
        ├── PRESENT=0    → PAGE FAULT (kernel handles)
        ├── WRITABLE=0 and it's a write → PROTECTION FAULT → SIGSEGV
        ├── NX=1 and it's an instruction fetch → EXECUTION FAULT → SIGSEGV
        └── OK → physical address sent to memory subsystem
        ↓
  Cache lookup (L1 → L2 → L3 → DRAM)
```

**MMU state per CPU core:**
- `CR3` register: physical address of the current process's top-level page table (PGD). Kernel loads this on every context switch — this is what makes address spaces private.
- **TLB**: set-associative cache storing recent virtual→physical mappings. Flushed (invalidated) on `CR3` load (context switch) unless tagged with ASID (Address Space ID, avoids full flush).

## The Blueprint

- **Hardware enforcement**: permissions are enforced by the MMU, not software. A bug in user code cannot bypass them — only the kernel (ring 0) can modify page tables.
- **Granularity**: 4KB pages minimum. Huge pages (2MB, 1GB) use fewer TLB entries — the MMU skips one or two page table levels.
- **SMEP/SMAP**: Supervisor Mode Execution/Access Prevention — prevents the kernel from accidentally executing or reading user-space memory. Enforced by MMU control register bits.
- **NX bit**: marks pages as non-executable. Stack and heap pages are NX by default — code injected there cannot be executed (blocks classic shellcode injection).
- **Context switch cost**: `CR3` reload flushes the entire TLB (unless ASID is used). This is why inter-process communication has higher cost than intra-process communication — address space switch means cold TLB.

## Where It Breaks

- **TLB shootdown**: when one CPU changes a page table entry, all other CPUs caching that mapping must invalidate it. Done via IPI (inter-processor interrupt). On NUMA machines with many cores this stalls everyone.
- **Spectre/Meltdown**: CPU speculative execution reads data before the MMU's permission check completes. Mitigations (KPTI — kernel page table isolation) add overhead by keeping separate page tables for user/kernel mode.
- **CR3 write = expensive**: OS does this on every context switch. This is why thread switching within a process is cheaper than process switching — threads share `CR3`.

## In LDS

Every pointer dereference in LDS (reading `m_data`, accessing `m_mutex`, walking the WPQ linked list) goes through the MMU. The reason LDS worker threads are cheap to switch compared to separate processes: they all share the same `CR3` value — no TLB flush on thread switch. Only the stack pointer changes.

## Validate

1. LDS spawns 8 worker threads. How many `CR3` loads does the kernel perform when context-switching between them, vs switching between 8 separate single-threaded processes?
2. What happens if LDS's code attempts to write to a `.text` segment address (e.g. overwriting a function pointer stored in read-only memory)?
3. A `malloc`'d buffer is freed, then a new `malloc` returns the same virtual address. Has the physical frame changed? Has the TLB entry changed?

## Connections

**Theory:** [[Core/Theory/Memory/MMU]]
**Mental Models:** [[Virtual Memory — The Machine]], [[TLB — The Machine]], [[Page Walk — The Machine]], [[Paging — The Machine]], [[Cache Hierarchy — The Machine]]
**Related:** [[Pointers — The Machine]], [[Process Memory Layout — The Machine]]
