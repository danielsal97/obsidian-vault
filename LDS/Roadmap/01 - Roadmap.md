1# LDS — Master Roadmap
## Complete Coverage: Implementation · Testing · DevOps · Architecture

**Project:** IoT-based NAS/RAID01 Drive System (Master-Minion)  
**Language:** C++20 | **Target:** August 2026 | **Total effort:** ~210 hrs  
**Last updated:** 2026-05-08

---

## At-a-Glance Status

```
Phase 1 — Core Framework Integration   ✅ COMPLETE   (18 hrs)
Phase 2A — Mac Client TCP Bridge       ✅ DONE       (16 hrs)
Phase 2 — Data Management & Network    ⏳ ACTIVE     (46 hrs)  ← YOU ARE HERE
Phase 3 — Reliability Features         ⏳ Pending    (24 hrs)
Phase 4 — Minion Server                ⏳ Pending    (12 hrs)
Phase 5 — Integration & Testing        ⏳ Pending    (68 hrs)
Phase 6 — Optimization & Polish        ⏳ Pending    (26 hrs)
─────────────────────────────────────────────────────────────
Total                                              ~210 hrs
```

> **Active sprint:** RAID01Manager → MinionProxy → ResponseManager → Scheduler.  
> See [[Phase 2 Execution Plan]].

---

## Full Component Status

| Component | Phase | Hours | Status |
|---|---|---|---|
| Reactor (epoll event loop) | 1 | — | ✅ Done |
| ThreadPool + WPQ | 1 | — | ✅ Done |
| Factory Pattern | 1 | — | ✅ Done |
| ICommand (abstract interface) | 1 | — | ✅ Done |
| Plugin System (PNP + DirMonitor) | 1 | — | ✅ Done |
| NBD Driver Communication | 1 | — | ✅ Done |
| Logger | 1 | — | ✅ Done |
| InputMediator | 1 | 4 | ✅ Done |
| Shared interfaces/ (IDriverComm, IMediator, IStorage) | 2A | — | ✅ Done |
| TCPDriverComm (Linux TCP server) | 2A | — | ✅ Done |
| LDS.cpp dual mode (nbd / tcp) | 2A | — | ✅ Done |
| TCP client test (Python) | 2A | — | ✅ Done |
| RAID01 Manager | 2 | 12 | ❌ Todo |
| MinionProxy | 2 | 14 | ❌ Todo |
| ResponseManager | 2 | 10 | ❌ Todo |
| Scheduler (retry + backoff) | 2 | 10 | ❌ Todo |
| Watchdog | 3 | 8 | ❌ Todo |
| AutoDiscovery | 3 | 10 | ❌ Todo |
| Error Handling & Logging | 3 | 6 | ❌ Todo |
| Minion Server (UDP + storage) | 4 | 12 | ❌ Todo |
| End-to-End Integration | 5 | 16 | ❌ Todo |
| Unit Tests | 5 | 20 | ❌ Todo |
| Integration Tests | 5 | 20 | ❌ Todo |
| System Tests (real hardware) | 5 | 12 | ❌ Todo |
| Performance Optimization | 6 | 10 | ❌ Todo |
| Documentation | 6 | 8 | ❌ Todo |
| CI/CD Pipeline | 6 | 8 | ❌ Todo |

---

## Phase-by-Phase Breakdown

### Phase 1 — Core Framework Integration ✅
**Dates:** Apr 2026 | **Effort:** 18 hrs | [[Phase 1 - Core Framework Integration]]

All done. Reactor, NBD, ThreadPool, Factory, PNP, InputMediator wired together.

**Phase 1 milestone:** InputMediator routes NBD events → LocalStorage → NBD reply.

---

### Phase 2A — Mac Client TCP Bridge ✅ Done
**Dates:** May 6–20 2026 | **Effort:** 16 hrs | [[Phase 2A - Mac Client TCP Bridge]]

**What was built:**
- `TCPDriverComm` — implements `IDriverComm`, drop-in for `NBDDriverComm` over TCP
- `interfaces/` — shared `IDriverComm.hpp`, `IMediator.hpp`, `IStorage.hpp`
- `LDS.cpp` — dual mode: `./lds nbd <dev> <size>` or `./lds tcp <port> <size>`
- `test/integration/test_tcp_client.py` — Python client (used in place of C++ BlockClient)
- `test/unit/test_tcp_driver.cpp` — unit tests for TCPDriverComm

#### Pre-work (before any new code)
- [x] Fix bug #3 — always reply to kernel even on storage error
- [x] Fix bug #8 — Dispatcher needs shared_mutex
- [x] Fix bug #10 — ThreadPool static mutex/cv

#### Task 2A.1 — Reactor Upgrade (2 hrs)
- [x] Change `Add(fd)` + `SetHandler(fn)` → `Add(fd, fn)` with per-fd handler map
- [x] Update `LDS.cpp` to new API
- [x] Verify all existing tests still pass

#### Task 2A.2 — Wire Protocol (1 hr)
- [x] Define `services/network/include/NetworkProtocol.hpp`
- [x] `ClientRequest` struct: type (1B) + offset (8B big-endian) + length (4B big-endian)
- [x] `ServerResponse` struct: status (1B) + length (4B big-endian)

#### Task 2A.3 — TCPServer on Linux (5 hrs)
[[04 - TCPServer|TCPServer]]
- [x] `socket()` + `bind()` + `listen()` on port 7800
- [x] `OnAccept()` — `accept()` + `reactor.Add(client_fd, handler)`
- [x] `RecvAll()` helper — loops until all N bytes received
- [x] `OnClientData()` — parse header, call `LocalStorage`, send response
- [x] Wire into `LDS.cpp`

#### Task 2A.4 — BlockClient on Mac (4 hrs)
[[01 - BlockClient|BlockClient]]
- [x] `Connect(ip, port)` — TCP socket + connect
- [x] `Write(offset, data)` — serialize request, send, recv response
- [x] `Read(offset, len)` — serialize request, send, recv response + data
- [x] CLI demo: `ldsclient <ip> <port> write/read <args>` (implemented as Python client)

#### Task 2A.5 — End-to-End Test (3 hrs)
- [x] Start master on Linux, connect from Mac
- [x] Write 1 MB of random data, read it back, `diff` is empty
- [x] Tests on real Mac ↔ Linux (not just localhost)

**Phase 2A milestone:** Mac client writes and reads blocks from Linux server over TCP on real hardware. Two machines, real network.

---

### Phase 2 — Data Management & Network ⏳
**Dates:** May 21 – Jun 17 2026 | **Effort:** 46 hrs | [[Phase 2 - Data Management & Network]]  
See full execution plan: [[Phase 2 Execution Plan]]

#### Pre-work (before any new code)
- [ ] Fix bug #8 — (see [[Known Bugs]])
- [ ] Fix bug #9
- [ ] Fix bug #10

#### Task 2.1 — RAID01 Manager (12 hrs)
[[RAID01 Manager]]
- [ ] Minion registry: id, ip, port, status
- [ ] Block mapping: `primary = block % n`, `replica = (block+1) % n`
- [ ] `FailMinion(id)` — reroute to healthy replica
- [ ] `SaveMapping` / `LoadMapping` for persistence
- [ ] Tests: 3/4/5-minion mapping, failure reroute, round-trip persistence

#### Task 2.2 — MinionProxy (14 hrs)
[[MinionProxy]]
- [ ] UDP socket per minion
- [ ] Serialize: `[MSG_ID:4B][OP:1B][OFFSET:8B][LEN:4B][DATA:var]`
- [ ] `SendGetBlock(minion_id, offset, len)` → MSG_ID
- [ ] `SendPutBlock(minion_id, offset, data)` → MSG_ID
- [ ] Fire-and-forget — ResponseManager handles replies
- [ ] Tests: serialization, correct routing, fake-minion round-trip

#### Task 2.3 — ResponseManager (10 hrs)
[[ResponseManager]]
- [ ] UDP listener thread on master port
- [ ] Parse: `[MSG_ID:4B][STATUS:1B][LEN:4B][RESERVED:4B][DATA:var]`
- [ ] `RegisterCallback(MSG_ID, fn)` — call fn when reply arrives
- [ ] Thread-safe callback map
- [ ] Timeout hook for Scheduler
- [ ] Tests: reception, callback, concurrent responses

#### Task 2.4 — Scheduler / Retry (10 hrs)
[[Scheduler]]
- [ ] Track pending requests: MSG_ID → deadline
- [ ] `OnResponse(MSG_ID, response)` — mark complete
- [ ] Timeout detection (poll or timer)
- [ ] Exponential backoff: 1s → 2s → 4s, max 3 retries
- [ ] Give up after max retries → propagate error
- [ ] Tests: success path, timeout + retry, max-retry fail

**Phase 2 milestone:** Master ↔ Minion UDP working end-to-end. Async responses + retry on timeout.

---

### Phase 3 — Reliability Features ⏳
**Dates:** Jun 2026 | **Effort:** 24 hrs | [[Phase 3 - Reliability Features]]

#### Task 3.1 — Watchdog (8 hrs)
[[Watchdog]]
- [ ] Background health-check thread
- [ ] PING each minion every 5 seconds
- [ ] FAILED if no response for 15 seconds
- [ ] Notify RAID01Manager + trigger AutoDiscovery
- [ ] Recovery detection: FAILED → HEALTHY on response

#### Task 3.2 — AutoDiscovery (10 hrs)
[[AutoDiscovery]]
- [ ] UDP broadcast listener: `"Hello, I'm Minion-N, Port XXXX"`
- [ ] New minion → register with RAID01Manager + rebalance
- [ ] Rejoin → resync missing blocks via Scheduler
- [ ] Rebalance: copy missing blocks to new/returning minion

#### Task 3.3 — Error Handling & Logging (6 hrs)
- [ ] All ops logged: READ, WRITE, FLUSH, errors
- [ ] Log levels: DEBUG / INFO / WARN / ERROR
- [ ] Graceful degradation on partial minion failure
- [ ] Propagate proper status codes to NBD layer

**Phase 3 milestone:** RAID01 working (2 copies). Failure detected + failover. Auto-discovery restores system.

---

### Phase 4 — Minion Server ⏳
**Dates:** Jun–Jul 2026 | **Effort:** 12 hrs | [[Phase 4 - Minion Server]]

#### Task 4.1 — Minion Server Framework (12 hrs)
- [ ] UDP server — listen for master commands
- [ ] Parse message format (same wire protocol as MinionProxy)
- [ ] `GET_BLOCK` handler — read from local storage
- [ ] `PUT_BLOCK` handler — write to local storage
- [ ] `DELETE_BLOCK` handler
- [ ] Response sender — include MSG_ID
- [ ] Local storage backend (file or memory-mapped)
- [ ] Broadcast `"Hello"` on startup for AutoDiscovery
- [ ] Tests: GET/PUT/DELETE round-trip, message parsing

**Phase 4 milestone:** Standalone minion binary. Receives commands, stores blocks, responds correctly.

---

### Phase 5 — Integration & Testing ⏳
**Dates:** Jul 2026 | **Effort:** 68 hrs | [[Phase 5 - Integration & Testing]]  
See test plan: [[Test Strategy]]

#### Task 5.1 — End-to-End Integration (16 hrs)
Wire all components in `main()`. Verify these flows work:

- [ ] Single READ: NBD → Reactor → InputMediator → ReadCommand → MinionProxy → response → NBD
- [ ] Single WRITE: NBD → WriteCommand → 2× MinionProxy (RAID01) → both ACKs → NBD
- [ ] Kill minion 1 → ReadCommand falls back to replica automatically
- [ ] Kill minion 1 → WriteCommand still writes to surviving minion
- [ ] Restart minion → AutoDiscovery finds it, resync starts
- [ ] Data survives master restart (mapping persistence)

#### Task 5.2 — Unit Tests (20 hrs)
Files to create in `test/unit/`:
- [ ] `test_raid01_manager.cpp`
- [ ] `test_minion_proxy.cpp`
- [ ] `test_response_manager.cpp`
- [ ] `test_scheduler.cpp`
- [ ] `test_read_command.cpp`
- [ ] `test_write_command.cpp`
- [ ] `test_watchdog.cpp`

Framework: Google Test (gtest). Use mocks for cross-component dependencies.

#### Task 5.3 — Integration Tests (20 hrs)
Files in `test/integration/`:
- [ ] `test_read_write.cpp` — normal operation
- [ ] `test_fault_tolerance.cpp` — single/double minion failure
- [ ] `test_minion_failure.cpp` — live failure injection
- [ ] `test_auto_discovery.cpp` — join / rejoin / rebalance

#### Task 5.4 — System Tests on Real Hardware (12 hrs)
- [ ] Deploy master on host, 3–4 Raspberry Pi minions
- [ ] Run all scenarios end-to-end
- [ ] Verify data integrity (checksums)
- [ ] Measure latency / throughput
- [ ] Stress test: 100+ concurrent operations

**Phase 5 milestone:** All tests green. Real hardware validated. Full system working.

---

### Phase 6 — Optimization & Polish ⏳
**Dates:** Aug 2026 | **Effort:** 26 hrs | [[Phase 6 - Optimization & Polish]]

#### Task 6.1 — Performance Optimization (10 hrs)
- [ ] Profile with `perf` / `gprof` — identify hot paths
- [ ] Optimize message serialization (zero-copy where possible)
- [ ] Tune thread pool size and WPQ priorities
- [ ] Batch small writes if beneficial
- [ ] Tune retry timeouts and backoff constants

#### Task 6.2 — Documentation (8 hrs)
- [ ] API documentation for all public interfaces
- [ ] Deployment guide (master + minion setup)
- [ ] Wire protocol spec (finalized) — [[Wire Protocol Spec]]
- [ ] Troubleshooting guide
- [ ] Update all Obsidian notes to match final implementation

#### Task 6.3 — CI/CD Pipeline (8 hrs)
- [ ] GitHub Actions: build + unit test on every push
- [ ] Code coverage report (target: >80%)
- [ ] Static analysis (clang-tidy)
- [ ] Docker image for master and minion — [[Docker Setup]]
- [ ] Automated deploy to test hardware (optional)

**Phase 6 milestone:** Production-ready. Optimized, documented, CI green.

---

## Dependency Chain

```
Reactor ✅
  ├─→ InputMediator ✅ (dispatches via lambdas → LocalStorage)
  │
  ├─→ [Phase 2A] Reactor upgrade (per-fd handlers)
  │         └─→ TCPServer ──→ LocalStorage
  │                └─→ BlockClient (Mac) ← two real machines talking
  │
  └─→ [Phase 2] ReadCommand / WriteCommand (classes, replace lambdas)
        └─→ RAID01Manager (2.1) ──→ MinionProxy (2.2)
                 └─→ Scheduler (2.4) ──→ ResponseManager (2.3)
                          └─→ Watchdog (3.1)
                          └─→ AutoDiscovery (3.2)
                                  └─→ Minion Server (4.1)
                                          └─→ Integration Tests (5.x)
                                                  └─→ Polish (6.x)
```

**Build order for Phase 2:** RAID01Manager → MinionProxy → ResponseManager → Scheduler

---

## Testing Coverage Map

| Layer | What to test | Files |
|---|---|---|
| Unit | Each component in isolation, mocked deps | `test/unit/` |
| Integration | 2+ components talking to each other | `test/integration/` |
| System | Full stack on real or simulated hardware | manual + scripts |
| Performance | Latency, throughput, stress | `test/perf/` |

See full strategy: [[Test Strategy]]

---

## Architecture Coverage

| Topic | Note |
|---|---|
| System overview | [[System Overview]] |
| RAID01 design | [[RAID01 Explained]] |
| NBD layer | [[NBD Layer]] |
| Three-tier architecture | [[Three-Tier Architecture]] |
| Concurrency model | [[Concurrency Model]] |
| Full request lifecycle | [[Request Lifecycle]] |
| Wire protocol | [[Wire Protocol Spec]] |
| Class diagram | [[Class Diagram - Full System]] |
| Write sequence | [[Sequence - Write Request]] |
| Read sequence | [[Sequence - Read Request]] |
| Minion state machine | [[State Diagram - Minion]] |
| NBD handshake | [[Sequence - NBD Handshake]] |

---

## Design Decisions

| Decision | Note |
|---|---|
| UDP not TCP | [[Why UDP not TCP]] |
| Templates not virtual functions | [[Why Templates not Virtual Functions]] |
| RAII everywhere | [[Why RAII]] |
| Observer pattern | [[Why Observer Pattern]] |
| IN_CLOSE_WRITE not IN_CREATE | [[Why IN_CLOSE_WRITE not IN_CREATE]] |
| signalfd not sigaction | [[Why signalfd not sigaction]] |

---

## Known Issues

See full list: [[Known Bugs]]

- Bug #8, #9, #10 — **critical, block Phase 2**
- 6 total critical bugs as of last update

---

## Milestones

| # | Name | Target | Status |
|---|---|---|---|
| M0 | Foundation complete | 2026-04-18 | ✅ Done |
| M1 | Components wire together | End Phase 1 | ✅ Done |
| M2A | Mac ↔ Linux TCP working on real hardware | 2026-05-08 | ✅ Done |
| M2 | Master ↔ Minion UDP + async | End Phase 2 | ⏳ Jun 2026 |
| M3 | Fault tolerance (RAID01 + discovery) | End Phase 3 | ⏳ Jun 2026 |
| M4 | Full system working | End Phase 5 | ⏳ Jul 2026 |
| M5 | Production ready | End Phase 6 | ⏳ Aug 2026 |

Full schedule: [[Timeline & Milestones]]

---

## What "Done" Looks Like

When all phases complete, the system will have:

- Fully functional NAS accessible over NBD
- RAID01: every block on 2 minions — survives 1 minion failure
- Automatic failover (Watchdog detects → ReadCommand uses replica)
- Dynamic minion discovery — plug in a new Pi, it joins automatically
- Graceful degradation — partial failure never causes data loss
- Scalable to 10+ minions and 1TB+ storage
- >80% test coverage with unit + integration + hardware tests
- CI/CD pipeline green on every commit
- Deployed via Docker (master) and a minion binary (Raspberry Pi)

---

## Quick Links

- [[00 Dashboard]] — live status table
- [[Phase 2 Execution Plan]] — active sprint
- [[Known Bugs]] — open issues
- [[Risk Register]] — what can go wrong
- [[Lessons Learned]] — retrospective notes
- [[Project Status & Metrics]] — progress numbers
