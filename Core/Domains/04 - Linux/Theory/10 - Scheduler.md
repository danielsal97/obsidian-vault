# Scheduler

The Linux scheduler decides which thread runs on which CPU at any given moment. The default scheduler for normal tasks is CFS — the Completely Fair Scheduler. Its goal is to give every runnable thread a fair share of CPU time proportional to its priority.

---

## CFS: Virtual Runtime

CFS tracks `vruntime` — a per-thread counter of how much CPU time the thread has consumed, weighted by priority. The scheduler always picks the thread with the **lowest vruntime**: the one most deprived of CPU time.

`vruntime` increments on every timer tick:

```
vruntime += elapsed_ns × weight_factor
```

- High-priority (nice −20): small `weight_factor` → vruntime grows slowly → gets scheduled more often
- Low-priority (nice +19): large `weight_factor` → vruntime grows fast → gets scheduled less often

At nice 0, `weight = 1024`. At nice −20, `weight = 88761`. At nice +19, `weight = 15`. A nice −20 task accumulates vruntime ~88x slower than a nice +19 task and therefore receives ~88x more CPU time over the same period.

---

## Data Structure: Red-Black Tree

All runnable threads on a CPU sit in a red-black tree keyed by `vruntime`. `pick_next_task` is O(log n) — it takes the leftmost node (minimum vruntime). The leftmost node pointer is cached so the common case is O(1).

When a thread wakes from sleep, its vruntime is adjusted with **lag compensation**: the kernel subtracts a fraction of the sleep time so the thread is not unfairly penalized for sleeping, but caps the adjustment at one scheduling period so a thread that slept for hours cannot monopolize the CPU.

---

## TIF_NEED_RESCHED

The scheduler does not run continuously. It is triggered by events. The flag `TIF_NEED_RESCHED` in the current thread's `thread_info` is the signal that a reschedule is pending.

Flow:
1. Timer interrupt fires → `update_curr()` increments current thread's vruntime
2. If another thread now has lower vruntime: set `TIF_NEED_RESCHED`
3. On **return from interrupt** (or syscall return), the kernel checks the flag
4. If set: call `schedule()` → `pick_next_task()` → `context_switch()`

This deferred design means the scheduler does not preempt mid-instruction — it waits for the nearest safe preemption point.

---

## Preemption Points

| Event | What happens |
|---|---|
| Return from timer interrupt | Flag checked; reschedule if set |
| Return from any syscall | Flag checked; reschedule if set |
| `sched_yield()` | Voluntary re-queue; schedule() called directly |
| Blocking syscall (`read`, `futex_wait`) | Thread marked `TASK_INTERRUPTIBLE`; schedule() called |
| Wakeup of higher-priority thread | `TIF_NEED_RESCHED` set on current thread |

---

## Scheduler Classes

Linux has multiple scheduler classes with a strict priority ordering. Higher-class tasks always preempt lower-class ones.

| Class | Policy | Behavior |
|---|---|---|
| `SCHED_DEADLINE` | EDF — earliest deadline | Highest priority; for hard real-time |
| `SCHED_FIFO` | Real-time FIFO | Runs until it blocks or yields; no preemption by CFS |
| `SCHED_RR` | Real-time round-robin | Like FIFO but time-sliced within priority |
| `SCHED_OTHER` | CFS (normal) | Default for all user threads |
| `SCHED_IDLE` | Idle | Runs only when nothing else is runnable |

A `SCHED_FIFO` thread at priority 99 will preempt any `SCHED_OTHER` thread. It holds the CPU until it blocks voluntarily. This makes RT threads useful for low-latency work but dangerous if they spin without blocking.

---

## Per-CPU Runqueues and NUMA

Each CPU has its own runqueue (red-black tree). The scheduler does not lock a global structure on every tick — each CPU runs its own instance of CFS against its local queue.

A periodic **load balancer** migrates tasks between CPUs to keep queues balanced. On NUMA systems, the scheduler prefers to keep a task on the same NUMA node as its memory to avoid cross-socket access (30–300 ns penalty vs ~5 ns local).

`taskset -c <cpus> ./program` pins a process to specific CPUs. `numactl --membind=<node>` pins memory allocations to a NUMA node. Both are useful for latency-sensitive workloads.

---

## Relevance for LDS

ThreadPool workers are normal `SCHED_OTHER` threads. They can be preempted at any time by the timer interrupt. When a worker calls `futex_wait` (inside a mutex or condition variable), it is removed from the runqueue immediately — it consumes no CPU while sleeping. When the event fires, the kernel re-inserts the worker into the runqueue and may set `TIF_NEED_RESCHED` on the current running thread, triggering a context switch.

---

## Related

- [[11 - Scheduler — The Machine]] — step-by-step CFS execution trace
- [[09 - Context Switch]] — what happens inside context_switch()
- [[10 - Context Switch — The Machine]] — register-level trace of the switch
- [[04 - Threads - pthreads]] — pthreads blocking primitives that interact with the scheduler
