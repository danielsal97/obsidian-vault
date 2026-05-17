# Scheduler — The Machine

## The Model

The Linux CFS (Completely Fair Scheduler) is a red-black tree of runnable tasks ordered by `vruntime` — virtual runtime. The task that has received the least CPU time (lowest vruntime) runs next. vruntime ticks faster for high-priority tasks and slower for low-priority ones, so low-priority tasks always eventually get scheduled.

The scheduler runs in kernel mode. It is not a thread — it is code that runs whenever a scheduling decision is needed (timer interrupt, blocking syscall, explicit yield).

---

## How It Moves

```
Timer interrupt fires (every 1ms at HZ=1000)
      │
      ▼
Scheduler entry: update_curr()
  → calculate how long current task has been running
  → increment task's vruntime by (elapsed_ns * weight_factor)
    (weight_factor > 1 for low-priority, < 1 for high-priority)
  → update task's position in the red-black tree
      │
      ▼
Check if preemption needed:
  → is there a task with lower vruntime than current task?
  → if yes: set TIF_NEED_RESCHED flag on current task
      │
      ▼
At next safe preemption point (return from interrupt):
  → kernel sees TIF_NEED_RESCHED set
  → calls schedule()
      │
      ▼
schedule():
  → pick_next_task():
      → leftmost node of red-black tree = task with lowest vruntime
      → that task runs next
  → context_switch(current, next)
      (see Context Switch — The Machine)
```

---

## How a Sleeping Task Re-enters the Tree

```
Task is sleeping (TASK_INTERRUPTIBLE), NOT in the runqueue tree

Event occurs (packet arrives, mutex released, timer fires):
  → kernel: try_to_wake_up(task)
  → set task state = TASK_RUNNING
  → update task's vruntime: "lag compensation"
      → sleeping task's vruntime was frozen while it slept
      → subtract a fraction of sleep time so it doesn't become unfairly disadvantaged
      → but cap: can't go more than one "scheduling period" behind
  → enqueue_task(): insert task into red-black tree at its vruntime position
  → if new task's vruntime < current task's vruntime:
      → set TIF_NEED_RESCHED → preempt current task
```

---

## Priority: nice values and cgroups

**nice(-20 to +19)**: translates to weight factor. nice -20 = weight 88761. nice 0 = weight 1024. nice +19 = weight 15. A nice -20 task accumulates vruntime 88x slower than a nice +19 task — meaning it gets 88x more CPU time in a period.

**Real-time tasks (SCHED_FIFO / SCHED_RR)**: bypass CFS entirely. They sit in a separate priority queue and always preempt any CFS task when runnable. A SCHED_FIFO task at priority 99 will run until it blocks or yields — nothing can preempt it except a higher-priority RT task.

**cgroups**: group tasks and assign CPU bandwidth quotas. Useful for containers. A cgroup with 50% quota gets at most 50ms per 100ms period.

---

## NUMA Awareness

On multi-socket systems, the scheduler tracks which NUMA node's memory a task has accessed. It prefers to schedule the task on a CPU in the same NUMA node to minimize cross-socket memory access latency (~30-300ns penalty per remote access vs ~5ns local).

`taskset` and `numactl` pin tasks to specific CPUs/NUMA nodes when you need deterministic latency.

---

## Where Scheduling Decisions Are Made

| Event | Schedule triggered |
|---|---|
| Timer interrupt | Periodic preemption check |
| Blocking syscall (read, mutex, sleep) | Immediate: current task deschedules |
| `sched_yield()` | Voluntary: re-insert at back of vruntime order |
| `pthread_cond_wait()` | Sleep: removed from tree |
| Wakeup (signal, data ready) | Task re-inserted into tree |

---

## Related Machines

→ [[10 - Context Switch — The Machine]]
→ [[04 - Threads and pthreads — The Machine]]
→ [[01 - Multithreading Patterns — The Machine]]
→ [[04 - Threads - pthreads]]
→ [[01 - Processes]]
