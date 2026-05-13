# 00 START HERE — LDS Project

Choose what you want to do.

---

## Understand what LDS is
→ [[Architecture/01 - System Overview]]
→ [[Architecture/02 - Three-Tier Architecture]]

## Trace a single request end to end
→ [[Flows/01 - Write Request — End to End]]
→ [[Runtime Machines/01 - LDS System — The Machine]]
→ [[Runtime Machines/02 - Request Lifecycle — The Machine]]

## Study a specific component

### Infrastructure (event loop, threading, logging)
→ [[Infrastructure/03 - Reactor]] — epoll event loop
→ [[Infrastructure/06 - ThreadPool]] — worker threads
→ [[Infrastructure/08 - Dispatcher]] — Observer/Dispatcher pattern
→ [[Infrastructure/09 - Logger]] — thread-safe logging
→ [[Infrastructure/01 - Singleton]] — global instances
→ [[Infrastructure/10 - Utilities Framework]]

### Application (storage, networking, RAID)
→ [[Application/InputMediator]] — event → command bridge
→ [[Application/Commands]] — ICommand + ReadCommand/WriteCommand
→ [[Application/Factory]] — runtime object creation
→ [[Application/01 - LocalStorage]] — in-memory block storage
→ [[Application/02 - RAID01 Manager]] — block → minion mapping
→ [[Application/03 - MinionProxy]] — UDP sender
→ [[Application/04 - ResponseManager]] — async response matching
→ [[Application/05 - Scheduler]] — deadlines and retry
→ [[Application/06 - Watchdog]] — minion health monitoring
→ [[Application/AutoDiscovery]] — minion registration

### Linux Integration (kernel interfaces)
→ [[Linux Integration/02 - NBDDriverComm]] — NBD kernel driver
→ [[Linux Integration/04 - TCPServer]] — TCP listener
→ [[Linux Integration/01 - BlockClient]] — Mac-side TCP client
→ [[Linux Integration/06 - Inotify]] → [[Linux Integration/05 - DirMonitor]] → [[Linux Integration/07 - PNP]] — plugin loading chain
→ [[Linux Integration/03 - NBD Protocol Deep Dive]]

## See runtime machines (how each component moves)
→ [[Runtime Machines/03 - Reactor — The Machine]]
→ [[Runtime Machines/04 - ThreadPool and WPQ — The Machine]]
→ [[Runtime Machines/10 - InputMediator — The Machine]]
→ [[Runtime Machines/07 - NBDDriverComm — The Machine]]
→ [[Runtime Machines/09 - RAID01Manager — The Machine]]
→ [[Runtime Machines/05 - Plugin System — The Machine]]

## Understand why decisions were made
→ [[Decisions/04 - Why UDP not TCP]]
→ [[Decisions/05 - Why TCP for Client]]
→ [[Decisions/06 - Why signalfd not sigaction]]
→ [[Decisions/01 - Why RAII]]
→ [[Decisions/02 - Why Observer Pattern]]
→ [[Decisions/03 - Why Templates not Virtual Functions]]
→ [[Decisions/07 - Why IN_CLOSE_WRITE not IN_CREATE]]

## Study the architecture
→ [[Architecture/04 - Concurrency Model]]
→ [[Architecture/08 - Request Lifecycle]]
→ [[Architecture/03 - Client-Server Architecture]]
→ [[Architecture/07 - RAID01 Explained]]
→ [[Architecture/10 - Wire Protocol Spec]]
→ [[Architecture/06 - NBD Layer]]

## See UML diagrams
→ [[UML/01 - Class Diagram - Full System]]
→ [[UML/04 - Sequence - Read Request]]
→ [[UML/05 - Sequence - Write Request]]
→ [[UML/02 - Sequence - NBD Handshake]]
→ [[UML/03 - Sequence - Plugin Loading]]

## Check project status and next steps
→ [[Roadmap/01 - Roadmap]]
→ [[Roadmap/04 - Project Status & Metrics]]
→ [[Roadmap/07 - Phase 2A Execution Plan]] ← active sprint

## Debug — known bugs and testing
→ [[Debugging/03 - Known Bugs]]
→ [[Debugging/02 - Unit Tests]]
→ [[Debugging/01 - Testing]]

## Prepare to explain LDS in an interview
→ [[Interview/01 - Interview Guide]] — pitch, cold Q&A, bugs to mention
→ [[Interview/02 - main() Wiring Explained]] — how it's all wired together

## Build phases (in order)
→ [[Phases/01 - Phase 1 - Core Framework Integration]] ✅
→ [[Phases/03 - Phase 2A - Mac Client TCP Bridge]] ⏳ active
→ [[Phases/02 - Phase 2 - Data Management & Network]]
→ [[Phases/04 - Phase 3 - Reliability Features]]
→ [[Phases/05 - Phase 4 - Minion Server]]

---

## Quick vocabulary lookup (LDS-specific terms)
→ [[Glossary/11 - WPQ]] · [[Glossary/08 - MSG_ID]] · [[Glossary/02 - Block Device]] · [[Glossary/03 - Block Number]] · [[Glossary/09 - NAS]] · [[Glossary/06 - Fire and Forget]] · [[Glossary/05 - Exponential Backoff]]

## Generic terms → Core vault
→ epoll, TCP, UDP, RAII, Templates, pthreads, shared_ptr, VFS, socketpair — see Core/Glossary/
