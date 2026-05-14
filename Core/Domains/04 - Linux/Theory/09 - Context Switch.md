# Context Switch

A context switch is the act of saving one thread's CPU state and restoring another's so the CPU can switch execution between threads. From the thread's perspective it is invisible — execution pauses at instruction N and resumes at instruction N+1 with no observable gap, except in elapsed time.

---

## What Gets Saved

The kernel must preserve all state that a thread needs to resume correctly.

| State | Where saved | Notes |
|---|---|---|
| General-purpose registers (RAX–R15) | Thread's kernel stack | ~16 stores |
| Program counter (RIP) | Kernel stack (hardware) | CPU saves this automatically on interrupt |
| Stack pointer (RSP) | `task_struct` | Restored to switch stacks |
| Flags register (RFLAGS) | Kernel stack (hardware) | Condition codes, interrupt enable |
| FP / SIMD registers (XMM, YMM) | Kernel stack | **Lazy**: skipped until another thread uses FPU |
| CR3 (page table root) | `task_struct` | Only loaded on process switch |

FPU state is deferred: if two threads never use floating-point, the kernel never saves or restores it. On the first FPU instruction after a switch, the CPU raises a `#NM` exception and the kernel saves the old FPU context then.

---

## Kernel Structures Involved

Each thread has a `task_struct` in the kernel — its control block. Among other fields it holds the saved stack pointer, scheduling metadata (`vruntime`), and state (`TASK_RUNNING`, `TASK_INTERRUPTIBLE`, etc.). Each thread also has a dedicated **kernel stack** (typically 8 KB or 16 KB) where register state is pushed during interrupt or syscall entry.

---

## When a Context Switch Occurs

**Preemptive (involuntary):** A hardware timer fires every ~1 ms (HZ=1000). The CPU saves RIP/RSP/RFLAGS automatically and enters the kernel's timer interrupt handler. If the current thread's time slice has expired, the scheduler sets `TIF_NEED_RESCHED`. On return from the interrupt, the kernel calls `schedule()` and picks the next thread.

**Voluntary (blocking):** The thread calls a syscall that cannot complete immediately — `read()` on an empty socket, `pthread_mutex_lock()` on a held mutex, `futex_wait()`. The kernel sets the thread state to `TASK_INTERRUPTIBLE`, removes it from the runqueue, and calls `schedule()` directly. The thread stays off-CPU until the event it is waiting for wakes it.

**Yield:** `sched_yield()` voluntarily re-queues the current thread at the back of its priority class, triggering a reschedule without blocking.

---

## Process Switch vs Thread Switch

The most important distinction for cost:

**Thread switch within the same process:** The threads share the same address space (`mm_struct`). CR3 is not changed. The TLB remains valid. The switch costs only the register save/restore.

**Process switch (different address spaces):** CR3 is loaded with the new process's page table root. This **flushes the entire TLB**. Every virtual-to-physical translation must be re-learned from page tables. The first few hundred memory accesses incur TLB misses at 10–100 ns each. This is the primary reason a single-process thread pool (epoll + workers) is cheaper than a process-per-connection design.

---

## Cost

- Direct switch cost (register save/restore): ~2–5 µs
- After an inter-process switch: cold TLB, cold instruction cache, cold data cache
- Total effective cost including cache warming: 5–50 µs depending on working set size

For LDS: ThreadPool workers are all in one process, so switches between them do not flush the TLB. The dominant cost is the working-set going cold if a worker sleeps long enough that its data evicts from L1/L2.

---

## Voluntary vs Involuntary

| Type | Trigger | Example |
|---|---|---|
| Involuntary | Timer interrupt, time-slice expiry | Any running thread |
| Voluntary | Thread blocks on a resource | `futex_wait`, `read`, `mutex_lock` |
| Yield | Explicit `sched_yield` | Cooperative multitasking patterns |

Both types execute the same `switch_to()` machinery in the kernel. The difference is only in the trigger.

---

## Related

- [[10 - Context Switch — The Machine]] — step-by-step execution trace
- [[11 - Scheduler — The Machine]] — how the scheduler picks the next thread
- [[10 - Scheduler]] — CFS, vruntime, runqueue structure
- [[04 - Threads - pthreads]] — pthreads API, blocking primitives
