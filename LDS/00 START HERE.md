# 00 START HERE — LDS Project

Choose what you want to do.

---

## Understand what LDS is
→ [[Architecture/System Overview]]
→ [[Architecture/Three-Tier Architecture]]

## Trace a single request end to end
→ [[Flows/Write Request — End to End]]
→ [[Runtime Machines/LDS System — The Machine]]
→ [[Runtime Machines/Request Lifecycle — The Machine]]

## Study a specific component

### Infrastructure (event loop, threading, logging)
→ [[Infrastructure/Reactor]] — epoll event loop
→ [[Infrastructure/ThreadPool]] — worker threads
→ [[Infrastructure/Dispatcher]] — Observer/Dispatcher pattern
→ [[Infrastructure/Logger]] — thread-safe logging
→ [[Infrastructure/Singleton]] — global instances
→ [[Infrastructure/Utilities Framework]]

### Application (storage, networking, RAID)
→ [[Application/InputMediator]] — event → command bridge
→ [[Application/Commands]] — ICommand + ReadCommand/WriteCommand
→ [[Application/Factory]] — runtime object creation
→ [[Application/LocalStorage]] — in-memory block storage
→ [[Application/RAID01 Manager]] — block → minion mapping
→ [[Application/MinionProxy]] — UDP sender
→ [[Application/ResponseManager]] — async response matching
→ [[Application/Scheduler]] — deadlines and retry
→ [[Application/Watchdog]] — minion health monitoring
→ [[Application/AutoDiscovery]] — minion registration

### Linux Integration (kernel interfaces)
→ [[Linux Integration/NBDDriverComm]] — NBD kernel driver
→ [[Linux Integration/TCPServer]] — TCP listener
→ [[Linux Integration/BlockClient]] — Mac-side TCP client
→ [[Linux Integration/Inotify]] → [[Linux Integration/DirMonitor]] → [[Linux Integration/PNP]] — plugin loading chain
→ [[Linux Integration/NBD Protocol Deep Dive]]

## See runtime machines (how each component moves)
→ [[Runtime Machines/Reactor — The Machine]]
→ [[Runtime Machines/ThreadPool and WPQ — The Machine]]
→ [[Runtime Machines/InputMediator — The Machine]]
→ [[Runtime Machines/NBDDriverComm — The Machine]]
→ [[Runtime Machines/RAID01Manager — The Machine]]
→ [[Runtime Machines/Plugin System — The Machine]]

## Understand why decisions were made
→ [[Decisions/Why UDP not TCP]]
→ [[Decisions/Why TCP for Client]]
→ [[Decisions/Why signalfd not sigaction]]
→ [[Decisions/Why RAII]]
→ [[Decisions/Why Observer Pattern]]
→ [[Decisions/Why Templates not Virtual Functions]]
→ [[Decisions/Why IN_CLOSE_WRITE not IN_CREATE]]

## Study the architecture
→ [[Architecture/Concurrency Model]]
→ [[Architecture/Request Lifecycle]]
→ [[Architecture/Client-Server Architecture]]
→ [[Architecture/RAID01 Explained]]
→ [[Architecture/Wire Protocol Spec]]
→ [[Architecture/NBD Layer]]

## See UML diagrams
→ [[UML/Class Diagram - Full System]]
→ [[UML/Sequence - Read Request]]
→ [[UML/Sequence - Write Request]]
→ [[UML/Sequence - NBD Handshake]]
→ [[UML/Sequence - Plugin Loading]]

## Check project status and next steps
→ [[Roadmap/Roadmap]]
→ [[Roadmap/Project Status & Metrics]]
→ [[Roadmap/Phase 2A Execution Plan]] ← active sprint

## Debug — known bugs and testing
→ [[Debugging/Known Bugs]]
→ [[Debugging/Unit Tests]]
→ [[Debugging/Testing]]

## Prepare to explain LDS in an interview
→ [[Interview/Interview Guide]] — pitch, cold Q&A, bugs to mention
→ [[Interview/main() Wiring Explained]] — how it's all wired together

## Build phases (in order)
→ [[Phases/Phase 1 - Core Framework Integration]] ✅
→ [[Phases/Phase 2A - Mac Client TCP Bridge]] ⏳ active
→ [[Phases/Phase 2 - Data Management & Network]]
→ [[Phases/Phase 3 - Reliability Features]]
→ [[Phases/Phase 4 - Minion Server]]

---

## Quick vocabulary lookup (LDS-specific terms)
→ [[Glossary/WPQ]] · [[Glossary/MSG_ID]] · [[Glossary/Block Device]] · [[Glossary/Block Number]] · [[Glossary/NAS]] · [[Glossary/Fire and Forget]] · [[Glossary/Exponential Backoff]]

## Generic terms → Core vault
→ epoll, TCP, UDP, RAII, Templates, pthreads, shared_ptr, VFS, socketpair — see Core/Glossary/
