# Key Terms & Concepts

Every significant term used in this project has its own note in the unified [[Core/Glossary/]]. Click to open.

---

### Hardware & Domain

| Term | One-line summary |
|------|-----------------|
| [[NAS]] | Network-Attached Storage — what LDS looks like to the user |
| [[Raspberry Pi]] | The single-board Linux computers acting as minion nodes |
| [[IoT]] | Internet of Things — the hardware class LDS belongs to |
| [[RAID01 Explained]] | How blocks are mirrored across two minions for redundancy |
| [[Block Device]] | What a block device is and how LDS registers as one |
| [[Block Number]] | How byte offsets map to block IDs for RAID distribution |

---

### Linux Kernel APIs

| Term | One-line summary |
|------|-----------------|
| [[NBD Layer]] | Network Block Device — how the kernel hands I/O to our process |
| [[epoll]] | I/O event notification — the engine behind the Reactor |
| [[socketpair]] | The kernel ↔ userspace bridge used by NBD |
| [[Inotify]] | Filesystem event API — detects new plugin `.so` files |
| [[pthreads]] | POSIX thread API — what ThreadPool and workers are built on |
| [[VFS]] | Virtual File System — the kernel layer above our block device |
| [[Decisions/06 - Why signalfd not sigaction\|signalfd]] | Receiving UNIX signals as epoll events for clean shutdown |

---

### Networking

| Term | One-line summary |
|------|-----------------|
| [[UDP]] | The transport used for master ↔ minion communication |
| [[TCP]] | The alternative to UDP — and why LDS doesn't use it |
| [[MSG_ID]] | 4-byte correlation key that matches UDP replies to requests |
| [[Fire and Forget]] | Send a UDP packet and return immediately; receive asynchronously |
| [[Wire Protocol Spec]] | The full byte-level packet format |

---

### C++ & Software Patterns

| Term | One-line summary |
|------|-----------------|
| [[RAII]] | Tie resource lifetime to stack objects — no manual cleanup |
| [[shared_ptr]] | Reference-counted smart pointer — how DriverData travels zero-copy |
| [[Templates]] | Compile-time type parameterization used in Factory, Dispatcher, Singleton |
| [[WPQ]] | Waitable Priority Queue — workers sleep here until a command arrives |
| [[Exponential Backoff]] | 1s → 2s → 4s retry strategy before failing over to replica |
| [[EIO]] | The errno surfaced to the user when all retries are exhausted |
| [[Decisions/01 - Why RAII\|Why RAII]] | Design decision: why RAII is enforced everywhere |
| [[Decisions/04 - Why UDP not TCP\|Why UDP not TCP]] | Design decision: full reasoning |
| [[Decisions/02 - Why Observer Pattern\|Why Observer]] | Design decision: loose coupling via Dispatcher |
| [[Decisions/03 - Why Templates not Virtual Functions\|Why Templates]] | Design decision: compile-time vs runtime dispatch |
