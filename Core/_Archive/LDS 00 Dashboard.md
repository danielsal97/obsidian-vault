# LDS — Local Drive Storage
## IoT-based NAS/RAID01 Drive System

**Language:** C++20 | **Duration:** ~17 weeks | **Difficulty:** Intermediate → Advanced  
**Last updated:** 2026-05-08

---

## Current Status

| Component | Status |
|---|---|
| Reactor (epoll event handling) | ✅ Done |
| ThreadPool + WPQ | ✅ Done |
| Factory Pattern | ✅ Done |
| Command Pattern (ICommand) | ✅ Done |
| Plugin System (PNP + DirMonitor) | ✅ Done |
| NBD Driver Communication | ✅ Done |
| Logger | ✅ Done |
| InputMediator | ✅ Done |
| Shared interfaces/ (IDriverComm, IMediator, IStorage) | ✅ Done — Phase 2A |
| TCPDriverComm (Linux TCP server, drop-in for IDriverComm) | ✅ Done — Phase 2A |
| TCP client test (Python — `test/integration/test_tcp_client.py`) | ✅ Done — Phase 2A |
| LDS.cpp dual mode (nbd / tcp via CLI arg) | ✅ Done — Phase 2A |
| RAID01 Manager | ❌ Phase 2 |
| MinionProxy | ❌ Phase 2 |
| ResponseManager | ❌ Phase 2 |
| Scheduler (C time-based, used by Watchdog) | ✅ Done in C — `Igit/ds/src/scheduler.c` |
| Scheduler (LDS UDP retry/timeout) | ❌ Phase 2 |
| Watchdog (C process watchdog) | ✅ Done in C — `Igit/ds/src/wd.c` |
| Watchdog (LDS minion health monitor) | ❌ Phase 3 |
| AutoDiscovery | ❌ Phase 3 |
| Minion Server | ❌ Phase 4 |
| Integration & Testing | ❌ Phase 5 |

---

## Active Phase

> **Phase 2 — Data Management & Network** (May 21 – Jun 17 2026, ~46 hrs)

**Phase 2A ✅ Done** — TCPDriverComm + Python client + dual-mode LDS.cpp on GitHub  
**Immediate next step:** RAID01Manager → MinionProxy → ResponseManager → Scheduler  
See: [[Phase 2 Execution Plan]]

---

## Phase Timeline

| Phase                                             | Focus                           | Dates         | Hours       | Status   |
| ------------------------------------------------- | ------------------------------- | ------------- | ----------- | -------- |
| [[Phase 1 - Core Framework Integration\]] | Core framework, NBD, wiring     | Apr 2026      | 18          | ✅ Done   |
| [[Phase 2A - Mac Client TCP Bridge\]]    | Mac client ↔ Linux TCP          | May 6–20 2026      | 16     | ✅ Done   |
| [[Phase 2 - Data Management & Network\]]  | RAID01, MinionProxy, Scheduler  | May 21–Jun 17 2026 | 46     | ⏳ Active |
| [[Phase 3 - Reliability Features\]]       | Watchdog, AutoDiscovery         | Jun 18–Jul 8 2026  | 24     | ⏳        |
| [[Phase 4 - Minion Server\]]              | Minion-side implementation      | Jul 9–22 2026      | 12     | ⏳        |
| [[Phase 5 - Integration & Testing\]]      | Full system integration + tests | Jul 23–Aug 12 2026 | 68     | ⏳        |
| [[Phase 6 - Optimization & Polish\]]      | Performance, CI/CD, docs        | Aug 13–26 2026     | 26     | ⏳        |
| **Total**                                         |                                 |               | **210 hrs** |          |

---

## Dependency Chain

```
Reactor ✅
  ├─→ InputMediator ✅ (dispatches via lambdas → LocalStorage ✅)
  │
  ├─→ [Phase 2A] Reactor upgrade (per-fd handlers)
  │         └─→ TCPServer ──→ LocalStorage
  │                └─→ BlockClient (Mac) ← two real machines talking
  │
  └─→ [Phase 2] ReadCommand / WriteCommand (classes, replace lambdas)
        └─→ RAID01Manager ──→ MinionProxy ──→ Minion Server
                  └─→ Scheduler ──→ ResponseManager
                          └─→ Watchdog ──→ AutoDiscovery
                                  └─→ Integration Tests
```

---

## Quick Links

### Architecture
- [[System Overview]]
- [[RAID01 Explained]]
- [[NBD Layer]]
- [[Three-Tier Architecture]]
- [[Concurrency Model]]
- [[Request Lifecycle]]
- [[Wire Protocol Spec]]
- [[Architecture/Client-Server Architecture]]

### Design Patterns
- [[Singleton]] — Logger, Factory access
- [[Factory]] — Plugin & command creation
- [[Observer]] — File system events
- [[Command]] — Task encapsulation & prioritization
- [[Reactor]] — epoll event loop

### UML Diagrams
- [[Class Diagram - Full System]]
- [[Sequence - NBD Handshake]]
- [[Sequence - Plugin Loading]]
- [[Sequence - Write Request]]
- [[Sequence - Read Request]]
- [[State Diagram - Minion]]
- [[Phase Dependencies]]

### Engineering Deep Dives
- [[Known Bugs]] — 12 bugs, 6 critical
- [[NBD Protocol Deep Dive]]
- [[Observer Pattern Internals]]
- [[Plugin Loading Internals]]
- [[Threading Deep Dive]]
- [[Singleton Memory Model]]
- [[Interview Guide]]

### Architecture Decisions
- [[Why TCP for Client]]
- [[Why UDP not TCP]]
- [[Why Templates not Virtual Functions]]
- [[Why RAII]]
- [[Why Observer Pattern]]
- [[Why IN_CLOSE_WRITE not IN_CREATE]]
- [[Why signalfd not sigaction]]

### Manager
- **[[00 Master Dashboard]] ← START HERE (daily entry point)**
- **[[Manager/Job Search Plan]] ← job search checklist**
- [[Phase 2 Execution Plan]] ← active sprint
- [[Timeline & Milestones]]
- [[Project Status & Metrics]]
- [[Risk Register]]
- [[Lessons Learned]]
- [[Test Strategy]]

### Components (Phase 2A)
- [[Components/TCPServer]]
- [[Components/BlockClient]]

### DevOps & Setup
- [[DevOps/Build System]] ← Make targets, flags, shared library, how to add components
- [[Engineering/Project Setup]] ← Repo layout, platform notes, ds/ library map, run commands
- [[Docker Setup]]
