# LDS — Local Drive Storage

LDS is a distributed NAS built on Raspberry Pi minions that presents as a block device (`/dev/nbdX`) to Linux. Writes fan out via RAID01 across two minions over UDP; reads are served from the primary. The full pipeline is: NBD kernel module → Reactor (epoll event loop) → InputMediator → ThreadPool (WPQ) → RAID01Manager → MinionProxy UDP → ResponseManager.

---

## Layer 0 — Linux / OS Primitives

What the kernel gives us. Every higher layer depends on one or more of these.

- [[04 - epoll|epoll]] — Reactor's engine; all I/O events funnel through here
- [[02 - Sockets TCP|socketpair / TCP]] — NBD transport (socketpair) and client transport (TCP)
- [[04 - Threads - pthreads|pthreads]] — ThreadPool worker threads
- [[06 - Why signalfd not sigaction|signalfd]] — clean shutdown without async-signal races
- [[06 - Inotify|inotify]] — plugin directory hot-loading events
- [[03 - UDP Sockets|UDP sockets]] — minion communication (fire-and-forget writes, ACK returns)

---

## Layer 1 — Core Infrastructure

Always-running framework components. Application logic sits on top of these.

| Component | Role | Note |
|---|---|---|
| [[03 - Reactor]] | epoll event loop | Central dispatcher for all fd events |
| [[06 - ThreadPool]] | N workers + WPQ priority queue | Admin > High > Med priority lanes |
| [[01 - Singleton]] | Global instance management | Controlled lifecycle for shared objects |
| [[09 - Logger]] | Thread-safe logging | Lock-free sink, level filtering |
| [[05 - Observer Pattern Internals]] | Event subscription + notification | Decouples producers from consumers |
| [[10 - Utilities Framework]] | Shared helpers | Timers, buffers, type utilities |
| [[08 - Dispatcher]] | Event dispatch to registered handlers | Observer pattern implementation |
| [[07 - Threading Deep Dive]] | Thread lifecycle, stack, TLS internals | Deep reference for ThreadPool workers |

---

## Layer 2 — Linux Integration

Bridges between kernel interfaces and the application layer.

| Component | Role | Note |
|---|---|---|
| [[02 - NBDDriverComm]] | Linux NBD kernel module via socketpair | |
| [[04 - TCPServer]] | TCP listener for client connections | |
| [[01 - BlockClient]] | Mac-side TCP client (dev / test) | |
| [[05 - DirMonitor]] | Watches plugin dir with inotify | |
| [[06 - Inotify]] | inotify fd wrapper | |
| [[07 - PNP]] | `dlopen()` plugin loader | |
| [[08 - Plugin Loading Internals]] | dlopen sequence, symbol resolution | |

---

## Layer 3 — Application

Business logic. All handlers run on ThreadPool workers, not on the Reactor thread.

| Component | Role |
|---|---|
| [[InputMediator]] | NBD event → ICommand, enqueues to WPQ |
| [[Commands]] | ReadCommand / WriteCommand — unit of work |
| [[Factory]] | Creates commands at runtime |
| [[01 - LocalStorage]] | In-memory block store (Phase 1) |
| [[02 - RAID01 Manager]] | Maps block# → (minionA, minionB) |
| [[03 - MinionProxy]] | UDP sender, fire-and-forget |
| [[04 - ResponseManager]] | Matches UDP ACKs to pending requests |
| [[05 - Scheduler]] | Timeout + exponential backoff retry |
| [[06 - Watchdog]] | Pings minions every 5 s, marks dead at 15 s |
| [[AutoDiscovery]] | Listens for UDP broadcasts from new minions |

---

## Runtime Machines (Synthesis)

Each machine animates one slice of the system. Read these after you understand the layers above.

| Machine | What it shows | Layers |
|---|---|---|
| [[01 - LDS System — The Machine]] | Full pipeline: kernel → Reactor → WPQ → storage | All |
| [[02 - Request Lifecycle — The Machine]] | NBD → InputMediator → Command → reply | 0→1→2→3 |
| [[03 - Reactor — The Machine]] | epoll loop internals, handler dispatch | 0+1 |
| [[04 - ThreadPool and WPQ — The Machine]] | WPQ priority, worker thread lifecycle | 1 |
| [[07 - NBDDriverComm — The Machine]] | Kernel socketpair, NBD request parsing | 0+2 |
| [[08 - TCPDriverComm — The Machine]] | TCP client driver, frame parsing | 0+2 |
| [[09 - RAID01Manager — The Machine]] | Block → minion mapping, UDP send x2, ACK wait | 2+3 |
| [[05 - Plugin System — The Machine]] | inotify → DirMonitor → PNP → dlopen() | 0+2 |
| [[10 - InputMediator — The Machine]] | Event → Command creation, WPQ enqueue | 1+3 |
| [[06 - LocalStorage — The Machine]] | In-memory vector, block read / write | 3 |

→ Also see Core vault: [[Linux Runtime — The Machine]] — subsystems map · [[Networking Stack — The Machine]] — NIC → epoll

---

## Architecture

→ [[01 - System Overview|System Overview]]
→ [[02 - Three-Tier Architecture|Three-Tier Architecture]]
→ [[03 - Client-Server Architecture|Client-Server Architecture]]
→ [[04 - Concurrency Model|Concurrency Model]]
→ [[06 - NBD Layer|NBD Layer]]
→ [[07 - RAID01 Explained|RAID01 Explained]]
→ [[08 - Request Lifecycle|Request Lifecycle]]
→ [[10 - Wire Protocol Spec|Wire Protocol Spec]]
→ [[05 - App Layer|App Layer]]
→ [[09 - Services|Services]] — future service mesh design

---

## Flows

→ [[01 - Write Request — End to End]]

---

## Decisions

→ [[01 - Why RAII|Why RAII]]
→ [[02 - Why Observer Pattern|Why Observer Pattern]]
→ [[03 - Why Templates not Virtual Functions|Why Templates not Virtual Functions]]
→ [[04 - Why UDP not TCP|Why UDP not TCP]]
→ [[05 - Why TCP for Client|Why TCP for Client]]
→ [[06 - Why signalfd not sigaction|Why signalfd not sigaction]]
→ [[07 - Why IN_CLOSE_WRITE not IN_CREATE|Why IN_CLOSE_WRITE not IN_CREATE]]

---

## UML

→ [[01 - Class Diagram - Full System|Class Diagram]]
→ [[02 - Sequence - NBD Handshake|Sequence: NBD Handshake]]
→ [[03 - Sequence - Plugin Loading|Sequence: Plugin Loading]]
→ [[04 - Sequence - Read Request|Sequence: Read Request]]
→ [[05 - Sequence - Write Request|Sequence: Write Request]]
→ [[06 - State Diagram - Minion|State Diagram: Minion]] — Discovering → Active → Degraded → Failed lifecycle
→ [[07 - Phase Dependencies|Phase Dependencies]] — full build dependency graph + critical path

---

## Project Status

→ [[01 - Roadmap|Roadmap]]
→ [[04 - Project Status & Metrics|Project Status & Metrics]]
→ [[07 - Phase 2A Execution Plan|Phase 2A Execution Plan]] — active sprint
→ [[02 - The Plan|The Plan]] · [[03 - Progress Tracker|Progress Tracker]] · [[05 - Timeline & Milestones|Timeline & Milestones]]
→ [[08 - Risk Register|Risk Register]] · [[09 - Test Strategy|Test Strategy]] · [[10 - Lessons Learned|Lessons Learned]]
→ [[11 - Job Search Plan|Job Search Plan]]

---

## Build Phases

→ [[01 - Phase 1 - Core Framework Integration|Phase 1: Core Framework]] — complete
→ [[03 - Phase 2A - Mac Client TCP Bridge|Phase 2A: Mac Client TCP Bridge]] — active
→ [[02 - Phase 2 - Data Management & Network|Phase 2: Data Management & Network]]
→ [[04 - Phase 3 - Reliability Features|Phase 3: Reliability Features]]
→ [[05 - Phase 4 - Minion Server|Phase 4: Minion Server]]
→ [[06 - Phase 5 - Integration & Testing|Phase 5: Integration & Testing]]
→ [[07 - Phase 6 - Optimization & Polish|Phase 6: Optimization & Polish]]

---

## Debug

→ [[01 - Testing]]
→ [[02 - Unit Tests]]
→ [[03 - Known Bugs]]

---

## Interview Prep

→ [[01 - Interview Guide]] — pitch, cold Q&A, bugs to mention
→ [[02 - main() Wiring Explained]] — how it all connects at startup

---

## Vocabulary

LDS-specific: [[01 - Key Terms|Key Terms]] · [[02 - Block Device|Block Device]] · [[03 - Block Number|Block Number]] · [[05 - Exponential Backoff|Exponential Backoff]] · [[06 - Fire and Forget|Fire and Forget]] · [[08 - MSG_ID|MSG_ID]] · [[09 - NAS|NAS]] · [[11 - WPQ|WPQ]]

Generic terms (epoll, TCP, UDP, RAII, Templates, pthreads, shared_ptr, VFS, socketpair) — see Core/Glossary/
