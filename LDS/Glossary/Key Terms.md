# Key Terms & Concepts

Every significant term used in this project has its own note. Click to open.

---

### Hardware & Domain

| Term | One-line summary |
|------|-----------------|
| [[Glossary/NAS\|NAS]] | Network-Attached Storage — what LDS looks like to the user |
| [[Glossary/Raspberry Pi\|Raspberry Pi]] | The single-board Linux computers acting as minion nodes |
| [[Glossary/IoT\|IoT]] | Internet of Things — the hardware class LDS belongs to |
| [[RAID01 Explained]] | How blocks are mirrored across two minions for redundancy |
| [[Glossary/Block Device\|Block Device]] | What a block device is and how LDS registers as one |
| [[Glossary/Block Number\|Block Number]] | How byte offsets map to block IDs for RAID distribution |

---

### Linux Kernel APIs

| Term | One-line summary |
|------|-----------------|
| [[NBD Layer]] | Network Block Device — how the kernel hands I/O to our process |
| [[Glossary/epoll\|epoll]] | I/O event notification — the engine behind the Reactor |
| [[Glossary/socketpair\|socketpair]] | The kernel ↔ userspace bridge used by NBD |
| [[Inotify]] | Filesystem event API — detects new plugin `.so` files |
| [[Glossary/pthreads\|pthreads]] | POSIX thread API — what ThreadPool and workers are built on |
| [[Glossary/VFS\|VFS]] | Virtual File System — the kernel layer above our block device |
| [[Decisions/Why signalfd not sigaction\|signalfd]] | Receiving UNIX signals as epoll events for clean shutdown |

---

### Networking

| Term | One-line summary |
|------|-----------------|
| [[Glossary/UDP\|UDP]] | The transport used for master ↔ minion communication |
| [[Glossary/TCP\|TCP]] | The alternative to UDP — and why LDS doesn't use it |
| [[Glossary/MSG_ID\|MSG_ID]] | 4-byte correlation key that matches UDP replies to requests |
| [[Glossary/Fire and Forget\|Fire-and-Forget]] | Send a UDP packet and return immediately; receive asynchronously |
| [[Wire Protocol Spec]] | The full byte-level packet format |

---

### C++ & Software Patterns

| Term | One-line summary |
|------|-----------------|
| [[Glossary/RAII\|RAII]] | Tie resource lifetime to stack objects — no manual cleanup |
| [[Glossary/shared_ptr\|shared_ptr]] | Reference-counted smart pointer — how DriverData travels zero-copy |
| [[Glossary/Templates\|C++ Templates]] | Compile-time type parameterization used in Factory, Dispatcher, Singleton |
| [[Glossary/WPQ\|WPQ]] | Waitable Priority Queue — workers sleep here until a command arrives |
| [[Glossary/Exponential Backoff\|Exponential Backoff]] | 1s → 2s → 4s retry strategy before failing over to replica |
| [[Glossary/EIO\|EIO]] | The errno surfaced to the user when all retries are exhausted |
| [[Decisions/Why RAII\|Why RAII]] | Design decision: why RAII is enforced everywhere |
| [[Decisions/Why UDP not TCP\|Why UDP not TCP]] | Design decision: full reasoning |
| [[Decisions/Why Observer Pattern\|Why Observer]] | Design decision: loose coupling via Dispatcher |
| [[Decisions/Why Templates not Virtual Functions\|Why Templates]] | Design decision: compile-time vs runtime dispatch |
