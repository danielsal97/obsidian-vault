# Risk Register

**Updated:** 2026-05-01

---

## Active Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Phase 2 scope creep (network layer is complex) | Medium | High | Define clear API contracts before coding. Stop at MVP. |
| R2 | Concurrent bugs when ThreadPool executes commands | High | High | Fix Dispatcher + LocalStorage thread-safety before Phase 2 starts |
| R3 | NBD kernel module not available on test machine | Low | High | Use Docker with `--privileged` + `modprobe nbd`. Alternative: mock NBD for unit tests |
| R4 | UDP packet loss in LAN causing false timeouts | Low | Medium | Tune Scheduler timeouts. Use loopback for integration tests first |
| R5 | Raspberry Pi hardware not available for Phase 5 | Medium | Medium | Use Docker containers as fake minions. Real hardware only for final system test |
| R6 | Phase 5 (68 hrs) under-estimated | High | Medium | This is the most uncertain phase. Add 20% buffer = 82 hrs |
| R7 | Data corruption bug in RAID01 mapping | Low | Critical | Thorough unit tests for all edge cases in GetBlockLocation() before using in production |

---

## Resolved Risks

| ID | Risk | Resolution | Date |
|---|---|---|---|
| RR1 | Race conditions in filesystem monitoring | Fixed with proper locking in DirMonitor | 2026-04-18 |
| RR2 | Static constructor ordering (SIOF) | Solved with Singleton lazy initialization | 2026-04-18 |
| RR3 | Memory leaks with shared libraries | RAII + smart pointers throughout | 2026-04-18 |
| RR4 | Thread safety in global state (Factory, Logger) | Mutex in Singleton + Logger | 2026-04-18 |

---

## Risk Deep-Dives

### R2 — Concurrent Bugs (HIGH PRIORITY before Phase 2)

Phase 1 is single-threaded in the request path. Phase 2 introduces ThreadPool executing ReadCommand/WriteCommand concurrently.

Two bugs that WILL crash under concurrent load:
1. `Dispatcher::NotifyAll` + `Register` concurrent = use-after-free (Bug #8)
2. `LocalStorage::Read/Write` concurrent = data race (Bug #9)

**Action:** Fix both before writing Phase 2 code. See [[Known Bugs]].

---

### R3 — NBD Module Availability

The `nbd` kernel module must be loaded before `/dev/nbd0` exists.

On macOS (Docker Desktop):
```bash
docker run --rm --privileged --pid=host justincormack/nsenter1 \
  /bin/sh -c "modprobe nbd max_part=8"
```

On Linux:
```bash
sudo modprobe nbd max_part=8
```

Unit tests and integration tests (with FakeMinion) don't need NBD. Only `make test_nbd` and the final system test need it.

---

### R6 — Phase 5 Underestimate

Phase 5 (Integration & Testing) is 35% of total effort (68/194 hrs). This is realistic for a distributed system but the estimate is uncertain because:
- Integration bugs are discovered late and expensive to fix
- Real hardware behavior differs from simulated
- Concurrent operation bugs are hard to reproduce

**Recommendation:** Start Phase 5 tests early (write test stubs in Phase 2-4, not all at the end).

---

## Related Notes
- [[Timeline & Milestones]]
- [[Project Status & Metrics]]
- [[Known Bugs]]
