# Linux Runtime — The Machine

## The Model

A running Linux process is the intersection of six kernel subsystems operating simultaneously. Understanding where each concept lives — and where it hands off to the next — is the foundation of all systems debugging and design.

This is the map. Every other Runtime Machine is a zoom-in on one path through it.

---

## The Full Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER SPACE                               │
│                                                                 │
│  Thread 1 (main)        Thread 2 (worker)    Thread 3 (worker) │
│  ┌──────────────┐       ┌──────────────┐     ┌──────────────┐  │
│  │ stack        │       │ stack        │     │ stack        │  │
│  │ registers    │       │ registers    │     │ registers    │  │
│  │ TLS          │       │ TLS          │     │ TLS          │  │
│  └──────┬───────┘       └──────┬───────┘     └──────┬───────┘  │
│         │                      │                    │           │
│         └──────────────────────┴────────────────────┘           │
│                         shared heap                             │
│                         shared .text                            │
│                         shared globals                          │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │  syscall / interrupt
┌────────────────────────────▼────────────────────────────────────┐
│                       KERNEL SPACE                              │
│                                                                 │
│  ┌─────────────┐   ┌──────────────┐   ┌────────────────────┐   │
│  │  Scheduler  │   │  MM subsys   │   │  VFS / Net stack   │   │
│  │  CFS rbtree │   │  page tables │   │  socket buffers    │   │
│  │  vruntime   │   │  VMAs        │   │  fd table          │   │
│  │  runqueues  │   │  page cache  │   │  epoll instances   │   │
│  └──────┬──────┘   └──────┬───────┘   └────────┬───────────┘   │
│         │                 │                    │                │
│         └─────────────────┴────────────────────┘                │
│                    kernel core                                  │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                        HARDWARE                                 │
│                                                                 │
│  ┌──────────┐   ┌────────────┐   ┌──────────┐  ┌────────────┐  │
│  │  CPU     │   │  MMU + TLB │   │  DRAM    │  │  NIC / SSD │  │
│  │  cores   │   │  CR3 reg   │   │  pages   │  │  DMA       │  │
│  └──────────┘   └────────────┘   └──────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Subsystem 1 — Memory: Virtual Address Space

Every process has its own virtual address space. The MMU translates virtual → physical on every memory access, using the page tables pointed to by CR3.

```
Process virtual address space (64-bit Linux):
  0x0000 0000 0000 0000  ← NULL (unmapped, catches null deref)
  0x0000 0000 0040 0000  ← .text (executable code, PROT_EXEC)
  0x0000 0000 ????        ← .data / .bss (globals)
  0x0000 0000 ????        ← heap (grows upward via brk/mmap)
  ...
  0x00007fff ????        ← stack (grows downward, per thread)
  0x00007fff ffff f000   ← stack top
  0xffff8000 0000 0000   ← kernel space (not accessible in user mode)
```

**All threads share the virtual address space.** Each thread has its own stack (separate mmap region), but they all read/write the same heap, same globals, same .text.

→ Deep dive: [[Page Fault — The Machine]] — what happens when a VA has no physical mapping
→ Deep dive: [[04 - Paging — The Machine]]

---

## Subsystem 2 — MMU: Translating Every Access

```
Thread accesses address 0x7fff1234:
  → CPU sends VA to MMU
  → MMU walks page tables (CR3 → PGD → PUD → PMD → PTE)
  → TLB hit: physical address returned in ~1 cycle
  → TLB miss: full 4-level walk, ~20 cycles, loads TLB entry
  → PTE not present: #PF exception → kernel page fault handler
  → PTE present, wrong permissions (write to read-only): SIGSEGV
```

The TLB is per-core. On a context switch to a **different process** (different CR3), the TLB is flushed — next access is a TLB miss. Switching between **threads of the same process** (same CR3) does NOT flush the TLB.

→ Deep dive: [[07 - TLB — The Machine]]
→ Deep dive: [[06 - Page Walk — The Machine]]

---

## Subsystem 3 — Scheduler: Who Gets the CPU

```
Every ~1ms: hardware timer fires → CPU interrupt
  → kernel interrupt handler runs
  → update current thread's vruntime += elapsed × weight_factor
  → check: does any other thread have lower vruntime?
      → YES: set TIF_NEED_RESCHED flag on current thread
      → NO: continue running

On return from interrupt (or syscall):
  → if TIF_NEED_RESCHED:
      → call schedule()
      → pick_next_task: find thread with lowest vruntime in CFS rbtree
      → context switch to that thread
```

**Context switch cost:** ~2-5μs direct. The expensive part is not saving/restoring registers — it's the cache warm-up after switching (new thread's working set is cold).

→ Deep dive: [[10 - Context Switch — The Machine]]
→ Deep dive: [[11 - Scheduler — The Machine]]

---

## Subsystem 4 — Threads: Shared Space, Independent Execution

```
pthread_create() / std::thread:
  → clone() syscall with CLONE_VM | CLONE_FILES | CLONE_SIGHAND
  → kernel creates new task_struct
  → shares mm_struct (same page tables, same address space)
  → allocates new kernel stack for the thread
  → new thread added to scheduler's runqueue
  → scheduler picks it up when a CPU is free

Each thread has:
  → its own stack (mmap'd)
  → its own registers (saved/restored on context switch)
  → its own TLS (thread-local storage)
  → its own errno

All threads share:
  → virtual address space (heap, globals, .text)
  → file descriptor table
  → signal handlers
```

**Synchronization crosses the user/kernel boundary:**
- Fast path (uncontended mutex): pure user-space atomic operation, no syscall
- Slow path (contended): `futex(FUTEX_WAIT)` syscall → thread sleeps in kernel wait queue → `futex(FUTEX_WAKE)` when lock released

→ Deep dive: [[Concurrency Runtime — The Machine]]
→ Deep dive: [[04 - Atomics — The Machine]]

---

## Subsystem 5 — File Descriptors: Everything Is a File

```
Every fd is an index into the process's fd table.
Every fd table entry points to a kernel file description.
Every file description points to a kernel object (inode, socket, epoll, pipe...).

fd 0 → stdin  → terminal
fd 1 → stdout → terminal
fd 2 → stderr → terminal
fd 3 → socket → TCP connection
fd 4 → epoll  → epoll instance
fd 5 → file   → on-disk inode

All of these respond to: read() / write() / close() / epoll_ctl()
```

The uniformity of fds is what makes `Reactor` possible: one epoll loop watches sockets, signals (signalfd), timers (timerfd), and filesystem events (inotify) — all as fds.

→ Deep dive: [[02 - File Descriptors — The Machine]]

---

## Subsystem 6 — Networking: From NIC to recvfrom()

```
Packet arrives at NIC:
  → DMA into kernel ring buffer (no CPU involved yet)
  → NIC raises hardware interrupt
  → kernel: schedule softirq (NET_RX_SOFTIRQ)
  → softirq runs: pull packets from ring buffer
  → IP layer: route lookup, TTL check
  → TCP/UDP layer: socket hash lookup by (src IP, src port, dst IP, dst port)
  → append sk_buff to socket's receive queue
  → wake any thread blocked in recv()/epoll_wait() on this socket

Thread blocked in epoll_wait():
  → kernel: socket has data → add fd to epoll ready list
  → wake epoll_wait() → return to user space
  → user calls recv() → copy data from sk_buff to user buffer → return
```

→ Deep dive: [[Networking Stack — The Machine]]

---

## How the Subsystems Interact — One Request

```
UDP packet arrives:
  NIC DMA → softirq → socket queue             (Subsystem 6)
  → epoll fd becomes ready                      (Subsystem 5)
  → epoll_wait() wakes thread                   (Subsystem 3 + 4)
  → thread runs: recvfrom() returns data        (Subsystem 1 + 2)
  → handler allocates Packet object: malloc()
      → ptmalloc arena → brk/mmap if needed    (Subsystem 1)
      → first touch: page fault → physical page (Subsystem 2)
  → post to thread pool (WPQ push)
  → worker thread unblocks (futex wake)         (Subsystem 3 + 4)
  → worker processes: accesses heap data
      → TLB hit or miss                         (Subsystem 2)
      → L1/L2/L3 cache hit or miss              (Hardware)
```

Every request touches all six subsystems. When something is slow, it lives in one of them.

---

## Where Time Goes (Profiling Guide)

| Symptom | Likely subsystem |
|---|---|
| High sys% in `top` | Subsystem 3 — too many syscalls / context switches |
| High page faults (`/proc/pid/stat`) | Subsystem 1+2 — working set doesn't fit in RAM |
| High TLB misses (perf stat) | Subsystem 2 — pointer-heavy data structures |
| High cache misses (perf stat) | Hardware — random access patterns |
| Threads blocking frequently | Subsystem 4 — lock contention, false sharing |
| Network throughput low | Subsystem 6 — socket buffer size, softirq budget |

---

## Links

→ [[Fork and Exec — The Machine]] — how a process is born
→ [[Program Startup — The Machine]] — exec() → dynamic linker → main()
→ [[Page Fault — The Machine]] — when a VA has no physical backing
→ [[Memory System — The Machine]] — malloc → page fault → cache hierarchy
→ [[Concurrency Runtime — The Machine]] — thread pool → mutex → wakeup
→ [[Networking Stack — The Machine]] — NIC → packet → fd → handler
→ [[Virtual Dispatch — The Machine]] — vptr → vtable → indirect call
