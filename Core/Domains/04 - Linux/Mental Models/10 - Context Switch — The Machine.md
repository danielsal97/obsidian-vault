# Context Switch — The Machine

## The Model

A context switch is the CPU saving one thread's execution state and loading another's. It happens invisibly to your code. One moment your thread is executing instruction N — then another thread ran for 5ms — then your thread resumes at instruction N+1. You cannot tell it happened unless you measure time.

The kernel scheduler is not a separate process. It runs in kernel mode, triggered by hardware timer interrupt or blocking syscall. It owns no CPU time of its own.

---

## How It Moves — Preemptive Switch (timer interrupt)

```
Thread A is executing (user mode, CPU running thread A's instructions)
      │
      ▼
Hardware timer fires (every ~1ms, configurable via HZ kernel param)
  → CPU raises interrupt 0x20 (timer interrupt)
  → CPU automatically:
      → saves current RIP (instruction pointer) to kernel stack
      → saves current RSP (stack pointer) to kernel stack
      → saves EFLAGS (flags register) to kernel stack
      → switches to kernel mode (ring 0)
      → jumps to interrupt handler
      │
      ▼
Kernel timer interrupt handler:
  → saves all remaining registers (RAX, RBX, RCX... R15, XMM0...) to thread A's kernel stack
  → decrements thread A's remaining time slice
  → if time slice expired: mark thread A as TASK_RUNNING but preempted
      │
      ▼
Scheduler runs (pick_next_task):
  → evaluates runqueue (CFS: red-black tree ordered by vruntime)
  → picks thread B (lowest virtual runtime = most deprived of CPU)
  → switch_to(thread_A, thread_B):
      → saves thread A's stack pointer to A's task_struct
      → loads thread B's stack pointer from B's task_struct
      → restores thread B's general-purpose registers from B's kernel stack
      → restores thread B's FPU state (if different)
      → updates CR3 if thread B is in a different process (different page table root)
        ← THIS IS THE EXPENSIVE CASE: TLB flush on address space switch
      │
      ▼
CPU returns to thread B's saved RIP
  → thread B resumes in user mode exactly where it left off
  → thread A is now waiting in the runqueue
```

---

## How It Moves — Voluntary Switch (blocking syscall)

```
Thread A calls read(socket_fd, ...) — socket is empty
      │
      ▼
Kernel read() handler:
  → checks socket receive buffer: empty
  → adds thread A to socket's wait queue
  → marks thread A as TASK_INTERRUPTIBLE (sleeping)
  → calls schedule() directly
      │
      ▼
Scheduler picks next runnable thread
  → same switch_to() process as above
      │
      ▼
Later: packet arrives (see Networking Stack — The Machine)
  → kernel marks thread A as TASK_RUNNING
  → thread A added back to runqueue
  → next time scheduler runs, thread A may be selected
  → thread A resumes from inside the read() syscall, which now returns
```

---

## The Expensive Part: TLB Flush

When switching between threads in the **same process**: no TLB flush. Virtual address mappings are identical.

When switching between threads in **different processes**: `CR3` register is loaded with the new process's page table pointer. This **invalidates the entire TLB**. Every virtual-to-physical translation for the new process must be re-learned from page tables. First few hundred memory accesses after an inter-process switch are TLB misses — 10-100ns each.

This is why epoll + one Reactor thread + thread pool (all in one process) is cheaper than a process-per-connection model.

---

## What Gets Saved and Restored

| State | Saved to | Cost |
|---|---|---|
| General registers (RAX..R15) | Kernel stack | ~16 stores |
| Floating point / SSE regs | Kernel stack (lazy: only if used) | ~32-256 stores |
| CR3 (page table) | task_struct | + TLB flush if process switch |
| Stack pointer (RSP) | task_struct | 1 store |
| Program counter (RIP) | Kernel stack (hardware) | automatic |

**FPU state is lazy**: kernel skips saving FPU registers until another thread uses FPU. On first FPU instruction after context switch, CPU raises #NM exception; kernel then saves old FPU state and restores new thread's FPU state.

---

## Hidden Costs

- Direct switch cost: ~2-5μs (register save/restore)
- Indirect cost: cold instruction cache, cold data cache, TLB misses
- Total effective cost: 5-50μs depending on cache state
- Voluntary vs preemptive: same save/restore cost, different trigger

---

## Related Machines

→ [[../Domains/04 - Linux/Mental Models/04 - Threads and pthreads — The Machine]]
→ [[../Domains/04 - Linux/Mental Models/07 - Kernel — The Machine]]
→ [[../Domains/05 - Concurrency/Mental Models/01 - Multithreading Patterns — The Machine]]
→ [[../Domains/01 - Memory/Mental Models/07 - TLB — The Machine]]
→ [[11 - Scheduler — The Machine]]
→ [[../Domains/04 - Linux/Theory/04 - Threads - pthreads]]
