# MMU — Memory Management Unit

The MMU is a hardware unit inside the CPU that translates virtual addresses to physical addresses on every memory access. It also enforces memory protection — user code cannot access kernel memory, read-only pages cannot be written, and non-executable pages cannot be jumped to.

---

## Role in the System

```
User Code                Kernel
    │                      │
    │  mov [0x7fff1234], rax  (virtual address)
    ↓
  MMU (hardware, inside CPU)
    ├── TLB lookup: is 0x7fff1234 cached?
    │     HIT  → PFN from TLB + permissions check
    │     MISS → page table walk (4 levels) → update TLB
    ├── Permission check: PRESENT, WRITABLE, USER, NX bits
    │     FAIL → page fault / protection fault (kernel handles)
    └── Physical address = PFN × 4096 + (0x7fff1234 & 0xFFF)
         ↓
       Memory hierarchy (L1/L2/L3/DRAM)
```

---

## CR3 Register

`CR3` holds the physical address of the current process's Page Global Directory (PGD — top-level page table).

- Loading a new `CR3` value is how the OS switches address spaces (context switch)
- `CR3` write flushes the entire TLB (unless ASID/PCID is used)
- `CR3` contains a physical address — the MMU needs it before it can translate anything

```bash
# You can't read CR3 from user space — it's a privileged register
# In kernel code: read_cr3_pa() returns the physical PGD address
```

---

## Permission Bits Enforced by MMU

| Bit | Name | Effect if violated |
|---|---|---|
| PRESENT | Is page in RAM? | Page fault → kernel handles |
| WRITABLE | Can be written? | Protection fault → SIGSEGV |
| USER | User-mode accessible? | Protection fault → SIGSEGV |
| NX | No-execute | Execution fault → SIGSEGV |

The NX bit (also called XD — Execute Disable) is the hardware implementation of W^X (write XOR execute). Stack and heap pages are writable but NX — code injected there cannot be executed.

---

## SMEP and SMAP

Modern CPUs add two more protections controlled by CR4:

- **SMEP** (Supervisor Mode Execution Prevention): kernel cannot execute code from user-mode pages. Prevents kernel from jumping to user-supplied shellcode.
- **SMAP** (Supervisor Mode Access Prevention): kernel cannot read/write user-mode memory without explicitly setting a flag (`STAC` instruction). Prevents confused-deputy attacks where kernel is tricked into dereferencing user pointers.

---

## Context Switch Cost: Address Space Switch

When the OS schedules a new process:
```
1. Save current CPU registers (including rsp, rip)
2. Load new CR3 (new process's PGD physical address)
   → TLB flush (all cached VPN→PFN mappings invalidated)
3. Load new registers
4. Resume execution
```

The TLB flush is the expensive part — the new process's first ~64–1536 memory accesses each trigger a TLB miss and page table walk. This is why:
- Thread switching (same process, same CR3) is cheaper than process switching
- Process switching is particularly painful after a long-running process had a warm TLB

**PCID (Process Context Identifier)**: modern Linux tags TLB entries with a 12-bit PCID. On CR3 load, the TLB is NOT flushed — old entries remain but are tagged with the old PCID and won't match the new process's lookups. Entries are reused when the same process is scheduled back. Dramatically reduces TLB miss rate on frequent context switches.

---

## Meltdown and KPTI

Meltdown (2018): speculative execution reads the value at a kernel virtual address before the MMU's permission check completes. Side-channel via cache timing reveals the value.

**KPTI** (Kernel Page Table Isolation) mitigation:
- Maintains two sets of page tables per process: one for user mode (no kernel mappings), one for kernel mode (full mappings)
- On syscall: switch to kernel page tables (`CR3` write), flush TLB
- On return to user: switch back, flush TLB
- Cost: ~5–30% overhead on syscall-heavy workloads

---

## Understanding Check

> [!question]- Why must CR3 hold a physical address rather than a virtual address?
> The MMU uses CR3 to start the page table walk — it needs to read the PGD before it can translate any virtual address. If CR3 held a virtual address, the MMU would need to translate CR3 before it could begin the translation, creating a circular dependency. Physical addresses bypass the translation machinery entirely, so CR3 as a physical address is the bootstrap entry point for all virtual-to-physical translation.

> [!question]- Two threads in the same process context-switch. Does the MMU flush the TLB?
> No — both threads belong to the same process and thus share the same page tables and the same CR3 value. The kernel does not write a new CR3 value when switching between threads of the same process, so no TLB flush occurs. The TLB retains all its valid entries. This is the key performance advantage of threads over processes for work that shares the same memory.

> [!question]- What happens when user-mode code tries to execute an instruction from a stack address, given that the stack is NX by default?
> The MMU checks the NX bit in the PTE for the stack page on every instruction fetch (not just data reads). Because the stack is mapped NX=1, an instruction fetch from a stack address causes a protection fault — the CPU raises an exception, the kernel sends SIGSEGV to the process. This is the hardware implementation of data execution prevention (DEP), which blocks classic return-to-stack shellcode injection.

---

**Mental Model:** [[MMU — The Machine]]
**Related:** [[TLB]], [[Page Walk]], [[Paging]], [[Virtual Memory]], [[Cache Hierarchy]]
