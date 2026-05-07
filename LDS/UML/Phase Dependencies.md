# Phase Dependencies

## Full Dependency Graph

```mermaid
flowchart TD
    R["✅ Reactor\n(epoll event loop)"]
    TP["✅ ThreadPool + WPQ"]
    F["✅ Factory Pattern"]
    IC["✅ ICommand base"]
    PLUG["✅ Plugin System\n(DirMonitor + PNP)"]
    LOG["✅ Logger"]

    IM["❌ InputMediator\nPhase 1.1"]
    RC["❌ ReadCommand\nPhase 1.2"]
    WC["❌ WriteCommand\nPhase 1.3"]

    RAID["❌ RAID01Manager\nPhase 2.1"]
    MP["❌ MinionProxy\nPhase 2.2"]
    RM["❌ ResponseManager\nPhase 2.3"]
    SCH["❌ Scheduler\nPhase 2.4"]

    WD["❌ Watchdog\nPhase 3.1"]
    AD["❌ AutoDiscovery\nPhase 3.2"]

    MIN["❌ Minion Server\nPhase 4.1"]

    IT["❌ Integration Tests\nPhase 5"]

    R --> IM
    TP --> IM
    F --> IM
    IC --> RC
    IC --> WC
    IM --> RC
    IM --> WC

    RAID --> RC
    RAID --> WC
    MP --> RC
    MP --> WC
    RM --> RC
    RM --> WC
    SCH --> MP
    SCH --> RM

    RAID --> WD
    MP --> WD
    RAID --> AD
    SCH --> AD

    WD --> MIN
    AD --> MIN

    RC --> IT
    WC --> IT
    MIN --> IT
```

---

## Critical Path

The longest chain of dependencies (must be done in order):

```
Reactor → InputMediator → ReadCommand
                        → RAID01Manager → Watchdog    → Minion Server → Integration Tests
                        → MinionProxy   → Scheduler   
                        → ResponseManager → AutoDiscovery
```

**Start with InputMediator.** Everything else follows.

---

## What You Can Mock

To unblock Phase 1 before Phase 2 is complete:

| Component | Mock Strategy |
|---|---|
| RAID01Manager | `FakeRAID` always returns `{minion0, minion1}` |
| MinionProxy | `FakeProxy` records calls, no UDP |
| ResponseManager | `FakeRM` immediately calls registered callback |
| Scheduler | `FakeScheduler` no-op track/OnResponse |

This lets you build and test InputMediator + ReadCommand + WriteCommand before the network layer exists.
