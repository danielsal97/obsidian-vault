# Virtual Memory

Every process on Linux runs in its own private virtual address space. Physical RAM is shared by all processes, but each sees only its own virtual view.

---

## Why Virtual Memory Exists

Without it:
- Processes would share the same physical addresses → one buggy process corrupts another
- Programs would need to know exact physical addresses at compile time
- You couldn't run more programs than physical RAM
- No isolation between user space and kernel

Virtual memory solves all four problems.

---

## Virtual Address Space Layout (64-bit Linux)

```
0xFFFFFFFFFFFFFFFF  ┌─────────────────────────────┐
                    │   Kernel space               │  not accessible from user mode
0xFFFF800000000000  ├─────────────────────────────┤
                    │   (non-canonical hole)       │  invalid addresses — fault on access
0x00007FFFFFFFFFFF  ├─────────────────────────────┤
                    │   Stack                      │  grows down, per-thread
                    │   ↓                          │
                    ├─────────────────────────────┤
                    │   mmap / shared libraries    │  .so files, anonymous mmap
                    ├─────────────────────────────┤
                    │   ↑                          │
                    │   Heap                       │  grows up via brk()/mmap()
                    ├─────────────────────────────┤
                    │   BSS                        │  zero-init globals
                    ├─────────────────────────────┤
                    │   Data                       │  init globals/statics
                    ├─────────────────────────────┤
                    │   Text                       │  code (read-only)
0x0000000000400000  ├─────────────────────────────┤
                    │   (unmapped — null guard)    │
0x0000000000000000  └─────────────────────────────┘
```

---

## Virtual → Physical Translation

The MMU performs this on every memory access:

```
Virtual page number (VPN) + page offset
         ↓
   MMU checks TLB
         ├── HIT: get physical frame number (PFN) directly
         └── MISS: walk 4-level page table (CR3 → PGD → PUD → PMD → PTE)
                   PTE gives PFN
                   TLB updated
         ↓
Physical address = PFN × 4096 + offset
         ↓
   Cache lookup → DRAM if miss
```

---

## Demand Paging

Virtual pages are not backed by physical frames until they are accessed.

```bash
# malloc(1GB) returns immediately — no physical RAM used
# On first write to each 4KB page → page fault → kernel allocates frame → write completes
```

Check committed vs resident memory:
```bash
/proc/PID/status   # VmRSS = resident (physical), VmVirt = virtual committed
```

---

## Key Operations

**`mmap()`** — map files or anonymous memory into the virtual address space:
```c
// Anonymous (like malloc but page-granular):
void* p = mmap(NULL, 4096, PROT_READ|PROT_WRITE,
               MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);

// File-backed:
int fd = open("file", O_RDONLY);
void* p = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
// file contents appear as memory; OS pages them in on access
```

**`mprotect()`** — change page permissions:
```c
mprotect(ptr, size, PROT_READ);   // make pages read-only
// Writing to them now → SIGSEGV (enforced by MMU)
```

**`mlock()`** — prevent pages from being swapped out:
```c
mlock(ptr, size);   // pin pages in RAM — no page faults on access
// Required for real-time code, cryptographic keys
```

---

## Copy-on-Write (COW)

After `fork()`, parent and child share the same physical pages mapped read-only. On first write by either process:
1. Page fault fires
2. Kernel copies the physical frame
3. PTE updated to point to the new copy
4. Write completes

This makes `fork()` nearly O(1) regardless of process size.

---

## ASLR

The kernel randomizes base addresses of stack, heap, and libraries on each `execve()`:
```bash
cat /proc/PID/maps   # actual virtual layout for this run
echo 0 > /proc/sys/kernel/randomize_va_space   # disable for debugging
```

---

## Understanding Check

> [!question]- How does virtual memory enable two processes to each "have" 128TB of address space when total physical RAM is only 64GB?
> Virtual addresses are just integers — they don't cost physical resources to assign. Physical RAM is only consumed when a virtual page is actually accessed (demand paging). The OS can also swap cold pages to disk, reclaiming physical frames. Two processes each with 128TB of *committed* virtual space might only use a few hundred MB of physical RAM each if most of their address space is sparse. The OS tracks committed virtual pages in page tables (which themselves live in RAM), but the physical frames behind them are allocated lazily.

> [!question]- What is the difference between a minor page fault and a major page fault?
> A minor fault means the kernel can satisfy the fault without disk I/O — the page is either demand-zero (just allocate and zero-fill a fresh frame) or already in the page cache (another process had the same file mapped). A major fault requires reading from disk — a swapped-out page or a file-backed mapping that hasn't been read yet. Minor faults cost ~1–10 µs; major faults cost ~1–100 ms. You can see counts with `/usr/bin/time -v ./program` (Minor vs Major page faults).

> [!question]- Why can't user-space code access kernel virtual addresses, even though they appear in the same 64-bit address space?
> The MMU's page table entries for kernel virtual addresses have the USER bit cleared. The CPU runs in ring 3 (user mode) for normal code. On any memory access, the MMU checks the USER bit against the current privilege level — if the page is supervisor-only and the CPU is in ring 3, it raises a protection fault. The kernel lives at high virtual addresses and its PTEs are present in every process's page table (to avoid a full TLB flush on syscall), but those PTEs are inaccessible from user mode. KPTI removes even this — kernel PTEs are only present in kernel mode.

---

**Mental Model:** [[Virtual Memory — The Machine]]
**Related:** [[Process Memory Layout]], [[Paging]], [[MMU]], [[TLB]], [[Page Walk]]
