# Kernel Concepts

---

## What the Kernel Does

The kernel is the core of the OS. It sits between hardware and user programs and manages:
- **CPU** — scheduling which process runs when
- **Memory** — virtual address spaces, page tables, swap
- **Devices** — drivers, block devices, network interfaces
- **File system** — VFS layer, inodes, file descriptors
- **IPC** — pipes, sockets, shared memory, signals

User programs cannot access hardware directly. They ask the kernel via **system calls**.

---

## System Calls

A syscall is a controlled entry point into the kernel. The CPU switches from user mode to kernel mode, executes the kernel function, then switches back.

```c
// User space — you write:
int fd = open("file.txt", O_RDONLY);

// Under the hood:
// 1. Arguments placed in registers
// 2. syscall instruction → CPU switches to kernel mode
// 3. Kernel runs sys_open() — checks permissions, finds inode, creates fd
// 4. Returns to user mode with fd number
```

Every I/O call (`read`, `write`, `send`, `recv`, `accept`, `epoll_wait`) is a syscall. Syscalls are expensive compared to function calls — they require a mode switch.

`strace ./program` — prints every syscall a program makes. Essential debugging tool.

---

## Processes vs Threads

**Process:** independent execution unit with its own virtual address space. Created with `fork()`.

**Thread:** execution unit inside a process. Shares the same address space as its siblings. Created with `pthread_create()` / `std::thread`.

| | Process | Thread |
|---|---|---|
| Address space | Independent | Shared |
| Memory isolation | Yes | No |
| Creation cost | High (copy page tables) | Low |
| Communication | IPC (pipes, sockets, shm) | Direct (shared variables + mutex) |
| Crash isolation | Yes (one crash doesn't kill others) | No (one crash kills all threads) |

**Context switch:** the kernel saves CPU registers for the current thread/process and restores them for the next one. Happens on scheduling tick, syscall, or blocking I/O.

---

## File Descriptors

In Unix, everything is a file. A file descriptor (fd) is a small integer (per-process) that refers to an open kernel resource.

| fd | What it is |
|---|---|
| 0 | stdin |
| 1 | stdout |
| 2 | stderr |
| 3+ | opened files, sockets, pipes, epoll instances, signalfd, inotify fd, etc. |

All use the same interface: `read()`, `write()`, `close()`, `select()`/`poll()`/`epoll()`.

This uniformity is why a Reactor can watch an NBD socketpair, a signalfd, and TCP client sockets in the same `epoll_wait()` — they're all just fds.

**fd lifecycle:** `open()`/`socket()`/`accept()` → use → `close()`. Not closing = fd leak. Each process has a limit (check with `ulimit -n`).

---

## Virtual Memory

Each process sees a private virtual address space (typically 0 to 2^48 on x86-64). The MMU translates virtual → physical addresses using page tables maintained by the kernel.

**Page:** smallest unit of memory mapping (typically 4KB). Each page has permissions (read/write/execute).

**Page fault:** CPU tries to access a virtual address with no physical mapping:
- Kernel allocates a physical page and maps it → program continues (transparent)
- Or: access to unmapped address → segfault (`SIGSEGV`)

**Copy-on-write:** after `fork()`, parent and child share physical pages. On first write by either, kernel copies the page. This makes `fork()` fast even for large processes.

---

## Kernel Modules

Code that runs inside the kernel, loaded dynamically. Can add device drivers, filesystems, network protocols.

```bash
sudo modprobe nbd       # load NBD module
lsmod                   # list loaded modules
rmmod nbd               # unload
```

**NBD (Network Block Device):** a kernel module that creates `/dev/nbdX` as a block device. All I/O to that device is forwarded to a userspace process via a socket. LDS uses this to intercept every read/write to `/dev/nbd0`.

Kernel modules run in kernel mode — a bug crashes the whole machine, not just a process.

---

## Scheduling

The kernel decides which thread runs on which CPU core and for how long.

**Preemptive scheduling:** kernel can interrupt a running thread at any time (timer interrupt) and switch to another. User threads don't cooperate — kernel forces context switches.

**Priority:** higher-priority threads run first. Real-time priority (`SCHED_FIFO`) guarantees a thread runs until it blocks or yields.

**Voluntary blocking:** a thread calls `epoll_wait()`, `read()`, `sem_wait()`, etc. — kernel marks it as sleeping and runs something else. When the event arrives, kernel wakes the thread.

This is why `epoll_wait()` uses zero CPU while waiting — the thread is not running, the kernel only wakes it when an fd becomes ready.

---

## IPC — Inter-Process Communication

| Mechanism | Description | Use case |
|---|---|---|
| Pipe | Unidirectional byte stream, parent↔child | Shell pipes |
| Named pipe (FIFO) | Like pipe but has a filesystem path | Unrelated processes |
| Unix socket | Bidirectional, AF_UNIX | Same machine, high performance |
| TCP/UDP socket | Network | Cross-machine |
| Shared memory | Map same physical page in two processes | Fastest IPC, needs synchronization |
| Message queue | Kernel-managed message passing | Structured messages |
| Signal | Async notification | Simple events (SIGINT, SIGUSR1) |

LDS uses: Unix socketpair (NBD), signalfd (signals via epoll), TCP (Mac client).

---

## Understanding Check

> [!question]- Why is a syscall more expensive than a regular function call?
> A syscall requires a CPU mode switch from user mode to kernel mode — the CPU saves registers, switches the stack pointer to the kernel stack, validates arguments, runs the kernel function, then switches back. A regular function call just pushes a stack frame. The mode switch alone costs hundreds of nanoseconds vs a few nanoseconds for a function call. This is why minimising syscalls (e.g., using `epoll` to batch I/O events rather than calling `read` repeatedly) matters for performance.

> [!question]- After `fork()`, parent and child share physical memory pages. A child writes to a variable. What happens?
> Copy-on-write. The kernel marks all shared pages as read-only. When the child writes to a page, the CPU raises a page fault. The kernel catches it, copies just that page for the child, marks it writable, and the write completes transparently. The parent's page is unchanged. This makes `fork()` fast even for a 1GB process — only pages that are actually written get copied.

> [!question]- Why does `epoll_wait()` use zero CPU while waiting for events?
> When a thread calls `epoll_wait()`, the kernel marks it as sleeping (blocked). The scheduler does not schedule it until at least one registered fd becomes ready. While sleeping, the thread uses no CPU cycles. When a packet arrives or a connection is accepted, the kernel wakes the thread and `epoll_wait` returns. This is the difference between blocking I/O (efficient) and busy-waiting (burns CPU checking in a loop).

> [!question]- Why does a bug in a kernel module crash the entire machine, but a bug in a userspace program only crashes that process?
> Kernel modules run in kernel mode — they share the kernel's address space with no memory protection between them. A bad pointer write can corrupt any kernel data structure. Userspace processes run in isolated virtual address spaces — a segfault only affects that process; the kernel catches the fault, kills the process, and keeps running. The NBD kernel module in LDS means a bug there would be catastrophic, which is why LDS runs the actual storage logic in userspace (safer, debuggable).

> [!question]- Why can the LDS Reactor watch an NBD socketpair fd, a signalfd, and TCP client sockets all in the same `epoll_wait()`?
> Because in Unix, everything is a file descriptor — they all implement the same `read`/`write`/`poll` kernel interface. `epoll` works at the fd level, not the type level. The kernel tracks readiness for any fd registered with epoll. This uniformity is the core design principle that makes the single-threaded Reactor pattern work across heterogeneous I/O sources.
