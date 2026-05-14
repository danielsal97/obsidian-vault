# LDS — Local Drive Storage

LDS is a distributed NAS built on Raspberry Pi minions that presents as a block device (`/dev/nbdX`) to Linux. Writes fan out via RAID01 across two minions over UDP; reads are served from the primary. The full pipeline is: NBD kernel module → Reactor (epoll event loop) → InputMediator → ThreadPool (WPQ) → RAID01Manager → MinionProxy UDP → ResponseManager.

---

## Layer 0 — Linux / OS Primitives

What the kernel gives us. Every higher layer depends on one or more of these.

- [[../Core/Domains/06 - Networking/Theory/04 - epoll|epoll]] — Reactor's engine; all I/O events funnel through here
- [[../Core/Domains/06 - Networking/Theory/02 - Sockets TCP|socketpair / TCP]] — NBD transport (socketpair) and client transport (TCP)
- [[../Core/Domains/04 - Linux/Theory/04 - Threads - pthreads|pthreads]] — ThreadPool worker threads
- [[Decisions/06 - Why signalfd not sigaction|signalfd]] — clean shutdown without async-signal races
- [[Linux Integration/06 - Inotify|inotify]] — plugin directory hot-loading events
- [[../Core/Domains/06 - Networking/Theory/03 - UDP Sockets|UDP sockets]] — minion communication (fire-and-forget writes, ACK returns)

---

## Layer 1 — Core Infrastructure

Always-running framework components. Application logic sits on top of these.

| Component                                                               | Role                              | Note                                    |
| ----------------------------------------------------------------------- | --------------------------------- | --------------------------------------- |
| [[Infrastructure/03 - Reactor\|Reactor]]                                | epoll event loop                  | Central dispatcher for all fd events    |
| [[Infrastructure/06 - ThreadPool\|ThreadPool]]                          | N workers + WPQ priority queue    | Admin > High > Med priority lanes       |
| [[Infrastructure/01 - Singleton\|Singleton]]                            | Global instance management        | Controlled lifecycle for shared objects |
| [[Infrastructure/09 - Logger\|Logger]]                                  | Thread-safe logging               | Lock-free sink, level filtering         |
| [[Infrastructure/05 - Observer Pattern Internals\|Observer/Dispatcher]] | Event subscription + notification | Decouples producers from consumers      |
| [[Infrastructure/10 - Utilities Framework\|Utilities]]                  | Shared helpers                    | Timers, buffers, type utilities         |
| [[Infrastructure/08 - Dispatcher\|Dispatcher]]                          | Event dispatch to registered handlers | Observer pattern implementation     |
| [[Infrastructure/07 - Threading Deep Dive\|Threading Deep Dive]]        | Thread lifecycle, stack, TLS internals | Deep reference for ThreadPool workers |

---

## Layer 2 — Linux Integration

Bridges between kernel interfaces and the application layer.

| Component | Role | Link |
|---|---|---|
| NBDDriverComm | Linux NBD kernel module via socketpair | [[Linux Integration/02 - NBDDriverComm\|NBDDriverComm]] |
| TCPServer | TCP listener for client connections | [[Linux Integration/04 - TCPServer\|TCPServer]] |
| BlockClient | Mac-side TCP client (dev / test) | [[Linux Integration/01 - BlockClient\|BlockClient]] |
| DirMonitor | Watches plugin dir with inotify | [[Linux Integration/05 - DirMonitor\|DirMonitor]] |
| Inotify | inotify fd wrapper | [[Linux Integration/06 - Inotify\|Inotify]] |
| PNP | `dlopen()` plugin loader | [[Linux Integration/07 - PNP\|PNP]] |
| Plugin Loading Internals | dlopen sequence, symbol resolution | [[Linux Integration/08 - Plugin Loading Internals\|Plugin Loading Internals]] |

---

## Layer 3 — Application

Business logic. All handlers run on ThreadPool workers, not on the Reactor thread.

| Component | Role | Link |
|---|---|---|
| InputMediator | NBD event → ICommand, enqueues to WPQ | [[Application/InputMediator]] |
| Commands | ReadCommand / WriteCommand — unit of work | [[Application/Commands]] |
| Factory | Creates commands at runtime | [[Application/Factory]] |
| LocalStorage | In-memory block store (Phase 1) | [[Application/01 - LocalStorage\|LocalStorage]] |
| RAID01Manager | Maps block# → (minionA, minionB) | [[Application/02 - RAID01 Manager\|RAID01Manager]] |
| MinionProxy | UDP sender, fire-and-forget | [[Application/03 - MinionProxy\|MinionProxy]] |
| ResponseManager | Matches UDP ACKs to pending requests | [[Application/04 - ResponseManager\|ResponseManager]] |
| Scheduler | Timeout + exponential backoff retry | [[Application/05 - Scheduler\|Scheduler]] |
| Watchdog | Pings minions every 5 s, marks dead at 15 s | [[Application/06 - Watchdog\|Watchdog]] |
| AutoDiscovery | Listens for UDP broadcasts from new minions | [[Application/AutoDiscovery]] |

---

## Runtime Machines (Synthesis)

Each machine animates one slice of the system. Read these after you understand the layers above.

| Machine | What it shows | Key layers |
|---|---|---|
| [[Runtime Machines/01 - LDS System — The Machine\|LDS System]] | Full pipeline: kernel → Reactor → WPQ → storage | All |
| [[Runtime Machines/02 - Request Lifecycle — The Machine\|Request Lifecycle]] | NBD → InputMediator → Command → reply | 0 → 1 → 2 → 3 |
| [[Runtime Machines/03 - Reactor — The Machine\|Reactor]] | epoll loop internals, handler dispatch | Layer 0 + 1 |
| [[Runtime Machines/04 - ThreadPool and WPQ — The Machine\|ThreadPool + WPQ]] | WPQ priority, worker thread lifecycle | Layer 1 |
| [[Runtime Machines/07 - NBDDriverComm — The Machine\|NBDDriverComm]] | Kernel socketpair, NBD request parsing | Layer 0 + 2 |
| [[Runtime Machines/08 - TCPDriverComm — The Machine\|TCPDriverComm]] | TCP client driver, frame parsing | Layer 0 + 2 |
| [[Runtime Machines/09 - RAID01Manager — The Machine\|RAID01Manager]] | Block → minion mapping, UDP send x2, ACK wait | Layer 2 + 3 |
| [[Runtime Machines/05 - Plugin System — The Machine\|Plugin System]] | inotify → DirMonitor → PNP → dlopen() | Layer 0 + 2 |
| [[Runtime Machines/10 - InputMediator — The Machine\|InputMediator]] | Event → Command creation, WPQ enqueue | Layer 1 + 3 |
| [[Runtime Machines/06 - LocalStorage — The Machine\|LocalStorage]] | In-memory vector, block read / write | Layer 3 |

→ Also see Core vault: [[../Core/Runtime Machines/Linux Runtime — The Machine]] — subsystems map · [[../Core/Runtime Machines/Networking Stack — The Machine]] — NIC → epoll

---

## Architecture

→ [[Architecture/01 - System Overview|System Overview]]
→ [[Architecture/02 - Three-Tier Architecture|Three-Tier Architecture]]
→ [[Architecture/03 - Client-Server Architecture|Client-Server Architecture]]
→ [[Architecture/04 - Concurrency Model|Concurrency Model]]
→ [[Architecture/06 - NBD Layer|NBD Layer]]
→ [[Architecture/07 - RAID01 Explained|RAID01 Explained]]
→ [[Architecture/08 - Request Lifecycle|Request Lifecycle]]
→ [[Architecture/10 - Wire Protocol Spec|Wire Protocol Spec]]
→ [[Architecture/05 - App Layer\|App Layer]]
→ [[Architecture/09 - Services\|Services]] — future service mesh design

---

## Flows

→ [[Flows/01 - Write Request — End to End]]

---

## Decisions

→ [[Decisions/01 - Why RAII|Why RAII]]
→ [[Decisions/02 - Why Observer Pattern|Why Observer Pattern]]
→ [[Decisions/03 - Why Templates not Virtual Functions|Why Templates not Virtual Functions]]
→ [[Decisions/04 - Why UDP not TCP|Why UDP not TCP]]
→ [[Decisions/05 - Why TCP for Client|Why TCP for Client]]
→ [[Decisions/06 - Why signalfd not sigaction|Why signalfd not sigaction]]
→ [[Decisions/07 - Why IN_CLOSE_WRITE not IN_CREATE|Why IN_CLOSE_WRITE not IN_CREATE]]

---

## UML

→ [[UML/01 - Class Diagram - Full System|Class Diagram]]
→ [[UML/02 - Sequence - NBD Handshake|Sequence: NBD Handshake]]
→ [[UML/03 - Sequence - Plugin Loading|Sequence: Plugin Loading]]
→ [[UML/04 - Sequence - Read Request|Sequence: Read Request]]
→ [[UML/05 - Sequence - Write Request|Sequence: Write Request]]
→ [[UML/06 - State Diagram - Minion\|State Diagram: Minion]] — Discovering → Active → Degraded → Failed lifecycle
→ [[UML/07 - Phase Dependencies\|Phase Dependencies]] — full build dependency graph + critical path

---

## Project Status

→ [[Roadmap/01 - Roadmap|Roadmap]]
→ [[Roadmap/04 - Project Status & Metrics|Project Status & Metrics]]
→ [[Roadmap/07 - Phase 2A Execution Plan|Phase 2A Execution Plan]] — active sprint
→ [[Roadmap/02 - The Plan\|The Plan]] · [[Roadmap/03 - Progress Tracker\|Progress Tracker]] · [[Roadmap/05 - Timeline & Milestones\|Timeline & Milestones]]
→ [[Roadmap/08 - Risk Register\|Risk Register]] · [[Roadmap/09 - Test Strategy\|Test Strategy]] · [[Roadmap/10 - Lessons Learned\|Lessons Learned]]
→ [[Roadmap/11 - Job Search Plan\|Job Search Plan]]

---

## Build Phases

→ [[Phases/01 - Phase 1 - Core Framework Integration|Phase 1: Core Framework]] — complete
→ [[Phases/03 - Phase 2A - Mac Client TCP Bridge|Phase 2A: Mac Client TCP Bridge]] — active
→ [[Phases/02 - Phase 2 - Data Management & Network|Phase 2: Data Management & Network]]
→ [[Phases/04 - Phase 3 - Reliability Features|Phase 3: Reliability Features]]
→ [[Phases/05 - Phase 4 - Minion Server|Phase 4: Minion Server]]
→ [[Phases/06 - Phase 5 - Integration & Testing\|Phase 5: Integration & Testing]]
→ [[Phases/07 - Phase 6 - Optimization & Polish\|Phase 6: Optimization & Polish]]

---

## Debug

→ [[Debugging/01 - Testing]]
→ [[Debugging/02 - Unit Tests]]
→ [[Debugging/03 - Known Bugs]]

---

## Interview Prep

→ [[Interview/01 - Interview Guide]] — pitch, cold Q&A, bugs to mention
→ [[Interview/02 - main() Wiring Explained]] — how it all connects at startup

---

## Vocabulary

LDS-specific: [[Glossary/01 - Key Terms\|Key Terms]] · [[Glossary/02 - Block Device|Block Device]] · [[Glossary/03 - Block Number|Block Number]] · [[Glossary/05 - Exponential Backoff|Exponential Backoff]] · [[Glossary/06 - Fire and Forget|Fire and Forget]] · [[Glossary/08 - MSG_ID|MSG_ID]] · [[Glossary/09 - NAS|NAS]] · [[Glossary/11 - WPQ|WPQ]]

Generic terms (epoll, TCP, UDP, RAII, Templates, pthreads, shared_ptr, VFS, socketpair) — see Core/Glossary/
