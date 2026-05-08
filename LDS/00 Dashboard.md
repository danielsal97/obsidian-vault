1# LDS — Local Drive Storage
## IoT-based NAS/RAID01 Drive System

**Language:** C++20 | **Duration:** ~16 weeks | **Difficulty:** Intermediate → Advanced  
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
| **Bug fixes #3, #8, #10** | ❌ Must do before Phase 2A |
| **Reactor upgrade (per-fd handlers)** | ❌ Phase 2A |
| **TCPServer (Linux side)** | ❌ Phase 2A |
| **BlockClient (Mac side)** | ❌ Phase 2A |
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

> **Phase 2A — Mac Client TCP Bridge** (May 6–20 2026, ~16 hrs)

**Immediate next step:** Fix bugs #3, #8, #10 → upgrade Reactor → build TCPServer + BlockClient  
See: [[Phase 2A Execution Plan]]

---

## Phase Timeline

| Phase                                             | Focus                           | Dates         | Hours       | Status   |
| ------------------------------------------------- | ------------------------------- | ------------- | ----------- | -------- |
| [[Phase 1 - Core Framework Integration\|Phase 1]] | Core framework, NBD, wiring     | Apr 2026      | 18          | ✅ Done   |
| [[Phase 2A - Mac Client TCP Bridge\|Phase 2A]]    | Mac client ↔ Linux TCP          | May 6–20 2026 | 16          | ⏳ Active |
| [[Phase 2 - Data Management & Network\|Phase 2]]  | RAID01, MinionProxy, Scheduler  | May 21–Jun 17 2026 | 46     | ⏳        |
| [[Phase 3 - Reliability Features\|Phase 3]]       | Watchdog, AutoDiscovery         | Jun 18–Jul 8 2026  | 24     | ⏳        |
| [[Phase 4 - Minion Server\|Phase 4]]              | Minion-side implementation      | Jul 9–22 2026      | 12     | ⏳        |
| [[Phase 5 - Integration & Testing\|Phase 5]]      | Full system integration + tests | Jul 23–Aug 12 2026 | 68     | ⏳        |
| [[Phase 6 - Optimization & Polish\|Phase 6]]      | Performance, CI/CD, docs        | Aug 13–26 2026     | 26     | ⏳        |
| **Total**                                         |                                 |               | **210 hrs** |          |

---

## Dependency Chain

```
Reactor ✅
  ├─→ InputMediator ✅ ──→ LocalStorage ✅
  │
  ├─→ [Phase 2A] Reactor upgrade (per-fd handlers)
  │         └─→ TCPServer ──→ LocalStorage
  │                └─→ BlockClient (Mac) ← two real machines talking
  │
  └─→ [Phase 2+] RAID01Manager ──→ MinionProxy ──→ Minion Server
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
- [[Architecture/Client-Server Architecture]] ← NEW Phase 2A

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
- [[Why TCP for Client]] ← NEW Phase 2A
- [[Why UDP not TCP]]
- [[Why Templates not Virtual Functions]]
- [[Why RAII]]
- [[Why Observer Pattern]]
- [[Why IN_CLOSE_WRITE not IN_CREATE]]
- [[Why signalfd not sigaction]]

### Manager
- [[Phase 2A Execution Plan]] ← NEW active sprint
- [[Phase 2 Execution Plan]]
- [[Timeline & Milestones]]
- [[Project Status & Metrics]]
- [[Risk Register]]
- [[Lessons Learned]]
- [[Test Strategy]]

### Components (Phase 2A)
- [[Components/TCPServer]] ← NEW
- [[Components/BlockClient]] ← NEW

### DevOps & Setup
- [[DevOps/Build System]] ← Make targets, flags, shared library, how to add components
- [[Engineering/Project Setup]] ← Repo layout, platform notes, ds/ library map, run commands
- [[Docker Setup]]
