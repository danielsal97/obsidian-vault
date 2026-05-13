# Phase 6 — Optimization & Polish

**Duration:** Week 6 | **Effort:** 26 hours | **Status:** ⏳ Not Started

---

## Goal

Make the system production-ready. Profile and fix hotspots, add CI/CD, finalize documentation.

**Milestone:** Passes stress test. CI pipeline green. Deployment guide written.

---

## Task 6.1 — Performance Optimization (10 hrs)

### Profile First

```bash
# Build with profiling
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo ..
make

# Run with perf
perf record ./lds
perf report

# Or valgrind callgrind
valgrind --tool=callgrind ./lds
kcachegrind callgrind.out.*
```

### Known Optimization Opportunities

| Area | Current | Target |
|---|---|---|
| Message serialization | `memcpy` per field | Zero-copy with `iovec` |
| ThreadPool size | Fixed 4 threads | Tune to CPU count |
| UDP socket | One per minion | Shared with `sendto()` |
| Block size | Fixed 4KB | Tunable at startup |
| Retry timeout | Fixed 1s | Adaptive to measured RTT |

### Batch Operations

For large sequential writes, batch multiple blocks into one UDP packet:
```
Instead of:  PUT block_0 → PUT block_1 → PUT block_2
Batch into:  PUT [block_0, block_1, block_2] → single UDP datagram
```

---

## Task 6.2 — Documentation (8 hrs)

### API Documentation (Doxygen)

```cpp
/**
 * @brief Returns the two minion IDs that store a given block.
 *
 * Primary = block_num % num_minions
 * Replica = (block_num + 1) % num_minions
 *
 * @param block_num  Zero-indexed block number
 * @return Pair {primary_id, replica_id}
 * @throws std::runtime_error if fewer than 2 healthy minions available
 */
std::pair<int,int> RAID01Manager::GetBlockLocation(uint64_t block_num);
```

### Deployment Guide

```bash
# Install on master (Ubuntu/Debian)
apt-get install nbd-client nbd-server
systemctl start lds

# Configure minions in /etc/lds/minions.conf:
# minion 0 192.168.1.10 9000
# minion 1 192.168.1.11 9000
# minion 2 192.168.1.12 9000

# Mount storage
nbd-client localhost /dev/nbd0
mount /dev/nbd0 /mnt/lds
```

### Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| EIO on read | Both minions for block failed | Check Watchdog logs |
| Slow writes | Minion RTT high | Check network, adjust timeout |
| Startup crash | RAID map file corrupt | Delete raid_map.bin, restart |
| Minion not discovered | Broadcast blocked | Check firewall port 8888 |

---

## Task 6.3 — CI/CD Pipeline (8 hrs)

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: LDS CI

on: [push, pull_request]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: apt-get install -y cmake g++ libgtest-dev

      - name: Build
        run: |
          cmake -B build -DCMAKE_BUILD_TYPE=Debug -DENABLE_COVERAGE=ON
          cmake --build build

      - name: Unit tests
        run: cmake --build build --target test

      - name: Coverage report
        run: gcovr -r . --xml -o coverage.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Coverage Badge Target
> 80%+ line coverage required for merge

---

## Final Checklist

- [ ] All unit tests pass (>80% coverage)
- [ ] Integration tests pass with 3 minions
- [ ] System tests pass on real RPi hardware
- [ ] Stress test: 10 concurrent writers, 60 seconds, zero data loss
- [ ] Performance: <10ms p99 latency for 4KB reads
- [ ] `make` builds without warnings (`-Wall -Wextra`)
- [ ] Deployment guide written
- [ ] Doxygen API docs generated
- [ ] CI pipeline green on main branch

---

## Previous

← [[Phase 5 - Integration & Testing]]

---

## Congratulations

When this phase is complete you have:

✅ Fully functional IoT-based NAS  
✅ RAID01 fault tolerance  
✅ Automatic failover and recovery  
✅ Dynamic minion discovery  
✅ Scalable to 10+ minions, 1TB+ storage  
✅ >80% test coverage  
✅ Production-ready code  
✅ Complete documentation  
