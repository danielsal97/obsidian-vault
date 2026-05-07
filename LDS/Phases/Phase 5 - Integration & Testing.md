# Phase 5 — Integration & Testing

**Duration:** Week 5 | **Effort:** 68 hours | **Status:** ⏳ Not Started

---

## Goal

Put everything together and prove it works — unit tests per component, integration tests for flows, and system tests on real Raspberry Pi hardware.

**Milestone:** All tests pass. Mount LDS as a filesystem. Read/write files. Kill a minion. Data still accessible.

---

## Task 5.1 — End-to-End Integration (16 hrs)

Wire all components in `app/LDS.cpp`:

```cpp
int main() {
    // Core
    ThreadPool pool(4);
    Reactor reactor;

    // Storage
    RAID01Manager raid;
    raid.AddMinion(0, "192.168.1.10", 9000);
    raid.AddMinion(1, "192.168.1.11", 9000);
    raid.AddMinion(2, "192.168.1.12", 9000);

    // Network
    ResponseManager resp_mgr;
    resp_mgr.Start(8080);
    MinionProxy proxy(raid, resp_mgr);

    // Reliability
    Scheduler scheduler(resp_mgr);
    Watchdog watchdog(raid, proxy);
    watchdog.Start();
    AutoDiscovery discovery(raid);
    discovery.Start();

    // Entry point
    InputMediator mediator(pool, raid, proxy, scheduler);
    reactor.Register(nbd_fd, &mediator);
    reactor.Run();
}
```

---

## Integration Test Checklist

### Normal Operation
- [ ] Single READ works end-to-end
- [ ] Single WRITE works end-to-end (2 copies sent)
- [ ] 100 concurrent READs complete correctly
- [ ] 100 concurrent WRITEs complete correctly

### Fault Tolerance
- [ ] Kill Minion1 → READ succeeds via Minion2 replica
- [ ] Kill Minion1 → WRITE succeeds to Minion2 (single copy)
- [ ] Kill both minions for block B → proper EIO returned
- [ ] Restart Minion1 → AutoDiscovery detects it
- [ ] After rejoin → full RAID01 restored

### Persistence
- [ ] Write data → restart master → data accessible
- [ ] RAID mapping persists across restart
- [ ] Minion data persists across minion restart

---

## Task 5.2 — Unit Tests (20 hrs)

**Testing framework:** Google Test (gtest)

| Test File | Component | Key Cases |
|---|---|---|
| `test_raid01_manager.cpp` | RAID01Manager | mapping, failure, persistence |
| `test_minion_proxy.cpp` | MinionProxy | serialization, UDP send |
| `test_response_manager.cpp` | ResponseManager | callback matching, concurrency |
| `test_scheduler.cpp` | Scheduler | retry, exponential backoff |
| `test_read_command.cpp` | ReadCommand | success, replica fallback |
| `test_write_command.cpp` | WriteCommand | 2 copies, degraded mode |
| `test_watchdog.cpp` | Watchdog | failure detection, recovery |
| `test_input_mediator.cpp` | InputMediator | event → command → queue |

---

## Task 5.3 — Integration Tests (20 hrs)

```
test/integration/
├── test_read_write.cpp         ← normal read/write flows
├── test_fault_tolerance.cpp    ← minion failure scenarios
├── test_minion_failure.cpp     ← kill and restart minion
└── test_auto_discovery.cpp     ← new minion joins mid-run
```

**Fake Minion for testing** (no real RPi needed):
```cpp
class FakeMinion {
public:
    FakeMinion(int port);
    void SimulateFailure(int duration_ms);   // drop packets for N ms
    void Start();
};
```

---

## Task 5.4 — System Tests on Real Hardware (12 hrs)

```bash
# Setup: 3 Raspberry Pis + 1 master machine

# On each RPi:
./minion --port 9000 --id 0   # RPi 0
./minion --port 9000 --id 1   # RPi 1
./minion --port 9000 --id 2   # RPi 2

# On master:
./lds &

# Mount the block device
mkfs.ext4 /dev/nbd0
mount /dev/nbd0 /mnt/lds

# Run test suite
./scripts/system_test.sh
```

**System test scenarios:**
1. Write 1GB file → read it back → verify checksum
2. Kill RPi1 mid-write → verify write completed
3. Mount, write 100 files, unmount, remount → all files present
4. Stress: 10 concurrent writers for 60 seconds

---

## Test Coverage Target

> **Goal: >80% line coverage across all new components**

```bash
# Generate coverage report
cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_COVERAGE=ON ..
make && make test
gcovr -r . --html --html-details -o coverage/index.html
```

---

## Previous / Next

← [[Phase 4 - Minion Server]]
→ [[Phase 6 - Optimization & Polish]]
