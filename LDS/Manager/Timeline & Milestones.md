# Timeline & Milestones

## Overall Schedule

| Phase | Start | End | Weeks | Hours | Status |
|---|---|---|---|---|---|
| Phase 1 — Core Framework | 2026-04-01 | 2026-04-18 | 2 | 18 | ✅ Complete |
| Phase 2A — Mac Client TCP Bridge | 2026-05-06 | 2026-05-20 | 2 | 16 | ✅ Complete |
| Phase 2 — Data & Network | 2026-05-21 | 2026-06-17 | 4 | 46 | ⏳ Active |
| Phase 3 — Reliability | 2026-06-18 | 2026-07-08 | 3 | 24 | ⏳ |
| Phase 4 — Minion Server | 2026-07-09 | 2026-07-22 | 2 | 12 | ⏳ |
| Phase 5 — Integration | 2026-07-23 | 2026-08-12 | 3 | 68 | ⏳ |
| Phase 6 — Polish | 2026-08-13 | 2026-08-26 | 2 | 26 | ⏳ |
| **Total** | | | **~17 weeks** | **210 hrs** | |

**Target completion:** August 2026

---

## Milestone Tracker

| Milestone | Target | Status | Description |
|---|---|---|---|
| M0 — Foundation | 2026-04-18 | ✅ Done | Plugin system, NBD, all Phase 1 components |
| M1 — Components Wire Together | 2026-04-18 | ✅ Done | InputMediator + lambdas + ThreadPool flowing end-to-end |
| M2A — Mac ↔ Linux TCP on real hardware | 2026-05-20 | ✅ Done | TCPDriverComm + Python client, dual-mode LDS.cpp |
| M2 — Network Communication | End Phase 2 | ⏳ | Master ↔ Minion UDP working, async responses |
| M3 — Fault Tolerance | End Phase 3 | ⏳ | RAID01 working, failure detection + auto-discovery |
| M4 — Full System Working | End Phase 5 | ⏳ | All components integrated, tests passing |
| M5 — Production Ready | End Phase 6 | ⏳ | Optimized, documented, CI/CD pipeline |

---

## Completed Milestones Log

| Date | Event |
|---|---|
| 2026-04-18 | Phase 1 implementation complete |
| 2026-04-25 | Documentation complete (15+ READMEs, Project Book) |
| 2026-04-25 | Project planning documents created |
| 2026-04-30 | Obsidian vault created with full architecture coverage |
| 2026-05-01 | Docker setup created |
| 2026-05-06 | Phase 2A sprint started — TCPServer + BlockClient |
| 2026-05-08 | Phase 2A complete — TCPDriverComm + Python client + dual-mode LDS.cpp |

---

## Effort Breakdown by Phase

```mermaid
pie title Effort Distribution (194 hrs total)
    "Phase 1 (done)" : 18
    "Phase 2 Data+Network" : 46
    "Phase 3 Reliability" : 24
    "Phase 4 Minion" : 12
    "Phase 5 Testing" : 68
    "Phase 6 Polish" : 26
```

Phase 5 (68 hrs) is the largest because testing a distributed system is expensive. Budget accordingly.

---

## Weekly Pace

```
Target: ~5 hours/day, 5 days/week = 25 hrs/week
Phase 2: 46 hrs ÷ 25 = ~2 weeks
Phase 5: 68 hrs ÷ 25 = ~3 weeks (more than planned — add buffer)
```

---

## Task Dependencies (Must-Do-First)

```
Cannot start Phase 2A until: Bug fixes #3 #8 #10 + Phase 1 complete ✅
Cannot start Phase 2  until: Phase 2A complete (Reactor upgrade needed)
Cannot start Phase 3  until: RAID01Manager + MinionProxy (Phase 2)
Cannot start Phase 4  until: Phase 3 design agreed
Cannot start Phase 5  until: Phase 4 complete
Cannot start Phase 6  until: Phase 5 green
```

---

## Related Notes
- [[Risk Register]]
- [[Project Status & Metrics]]
- [[00 Dashboard]]
