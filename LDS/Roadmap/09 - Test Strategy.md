# Test Strategy — LDS Testing Pyramid

**Principle:** Tests should catch real bugs, not test mocks of themselves. A test that passes because it only tests fake components gives false confidence.

---

## Test Pyramid

```
                    ┌───────────────────┐
                    │   System Tests    │  (Phase 5)
                    │  Full NBD + RAID  │  ~10 tests, slow, need hardware
                    └───────────────────┘
               ┌─────────────────────────────┐
               │    Integration Tests         │  (Phase 2-4)
               │  FakeMinion + real network   │  ~20 tests, medium speed
               └─────────────────────────────┘
          ┌─────────────────────────────────────────┐
          │           Unit Tests                     │  (Phase 1 - done)
          │  Isolated components, no I/O             │  9 test binaries, fast
          └─────────────────────────────────────────┘
```

---

## Current Test Coverage (Phase 1)

| Test Binary | What It Tests | How |
|---|---|---|
| `test_plugin_load` | `dlopen` + `__attribute__((constructor))` | Drops `.so`, verifies Factory registration |
| `test_pnp_main` | PNP orchestration: DirMonitor + SoLoader + Dispatcher | Creates temp dir, copies `.so`, checks callback |
| `test_dir_monitor` | `inotify` event detection | Creates/deletes files, verifies event types |
| `test_logger` | Logger thread safety + levels | Multiple threads writing, checks no interleaving |
| `test_thread_pool` | Worker execution + priority ordering + Stop | Pushes commands, verifies execution order |
| `test_wpq` | WPQ blocking Pop + concurrent Push | Multiple producer/consumer threads |
| `test_singelton` | Double-checked locking, thread safety | Multiple threads calling GetInstance concurrently |
| `test_command_demo` | ICommand priority + Execute | Queues commands, checks order |
| `test_msg_broker` | Message routing end-to-end | Sends messages through Dispatcher chain |

**What is NOT tested yet:**
- NBD protocol (requires `/dev/nbd0` kernel module)
- `LocalStorage` correctness (no test binary)
- `Reactor` event loop (no test binary)
- Concurrent `Read` + `Write` to `LocalStorage`
- RAID01 block mapping
- UDP networking

---

## Phase 2 Test Requirements

### Mock Strategy — What to Mock, What NOT to Mock

**DO mock:**
- Network I/O (real UDP = flaky in CI, depends on timing)
- Minion hardware (use `FakeMinion` in-process)
- Time (for testing Scheduler timeouts without sleeping)

**DO NOT mock:**
- `std::vector` / `std::unordered_map` (they work)
- `LocalStorage` (test against real file descriptor)
- `RAID01Manager` block arithmetic (test the actual algorithm)
- Thread synchronization (test with real threads — mock mutexes hide real bugs)

### FakeMinion

```cpp
class FakeMinion {
public:
    FakeMinion(int port);  // binds UDP socket

    // Configured responses (for testing)
    void WillRespondWith(uint32_t msg_id, Status status, Buffer data);
    void WillTimeout(uint32_t msg_id);  // never respond
    void WillDelayResponse(uint32_t msg_id, ms delay);

    // Inspection
    std::vector<ReceivedPacket> GetReceivedPackets();
};
```

FakeMinion is a real UDP server running in a background thread. MinionProxy talks to it just like a real minion. This tests the actual serialization, deserialization, and async response handling.

**Why not mock the UDP socket?** Because the real bug surface is in the serialization code (byte order, struct packing) and the async matching (ResponseManager). Mocking the socket lets those bugs through.

---

## Phase 2 Test Plan

### RAID01Manager Tests

```cpp
TEST(RAID01, BlockMapping_3Minions) {
    RAID01Manager raid;
    raid.AddMinion(0, "192.168.1.10", 7701);
    raid.AddMinion(1, "192.168.1.11", 7701);
    raid.AddMinion(2, "192.168.1.12", 7701);

    auto [primary, replica] = raid.GetBlockLocation(0);
    ASSERT_EQ(primary, 0);   // 0 % 3 = 0
    ASSERT_EQ(replica, 1);   // (0+1) % 3 = 1

    auto [p2, r2] = raid.GetBlockLocation(5);
    ASSERT_EQ(p2, 2);        // 5 % 3 = 2
    ASSERT_EQ(r2, 0);        // (5+1) % 3 = 0
}

TEST(RAID01, FailMinion_SkipsInMapping) {
    RAID01Manager raid;
    // ... add 3 minions, fail minion 0
    raid.FailMinion(0);
    auto [p, r] = raid.GetBlockLocation(0);
    ASSERT_NE(p, 0);   // should not route to failed minion
    ASSERT_NE(r, 0);
}

TEST(RAID01, PersistenceRoundTrip) {
    RAID01Manager raid;
    // ... configure
    raid.SaveMapping("/tmp/test_mapping.json");
    RAID01Manager raid2;
    raid2.LoadMapping("/tmp/test_mapping.json");
    ASSERT_EQ(raid.GetBlockLocation(42), raid2.GetBlockLocation(42));
}
```

### MinionProxy + ResponseManager Tests

```cpp
TEST(MinionProxy, PutBlock_SerializationCorrect) {
    FakeMinion fake(7701);
    MinionProxy proxy;
    proxy.AddMinion(0, "127.0.0.1", 7701);

    uint32_t msg_id = proxy.SendPutBlock(0, 4096, testData);

    auto packets = fake.GetReceivedPackets();
    ASSERT_EQ(packets.size(), 1);
    ASSERT_EQ(ntohl(packets[0].header.msg_id), msg_id);
    ASSERT_EQ(packets[0].header.op, 0x01);         // PUT
    ASSERT_EQ(be64toh(packets[0].header.offset), 4096);
    ASSERT_EQ(packets[0].data, testData);
}

TEST(ResponseManager, CallbackFired_OnResponse) {
    FakeMinion fake(7701);
    ResponseManager rm;
    rm.Start(7700);

    bool called = false;
    rm.RegisterCallback(42, [&](Status s, Buffer b) { called = true; });
    fake.SendResponseTo("127.0.0.1", 7700, {.msg_id=42, .status=OK});

    std::this_thread::sleep_for(10ms);
    ASSERT_TRUE(called);
}
```

### Scheduler Timeout Tests

```cpp
TEST(Scheduler, RetryOnTimeout) {
    MockClock clock;
    Scheduler sched(clock);
    int retry_count = 0;

    sched.Track(42, 1s, [&]{ retry_count++; sched.Track(42, 2s, [&]{ retry_count++; }); });

    clock.Advance(1500ms);  // past first deadline
    ASSERT_EQ(retry_count, 1);

    clock.Advance(2500ms);  // past second deadline
    ASSERT_EQ(retry_count, 2);
}
```

**Note:** Use a MockClock (injectable) so tests don't actually sleep. `std::chrono::steady_clock` should be injectable via template or interface.

---

## Phase 3-4 Test Plan (Preview)

### Watchdog Tests
- [ ] Minion stops responding → marked FAILED after 15s
- [ ] Minion recovers → marked HEALTHY, re-added to RAID mapping
- [ ] Multiple minion failures handled simultaneously

### AutoDiscovery Tests
- [ ] Broadcast received → new minion added to RAID
- [ ] Duplicate broadcast ignored
- [ ] Discovery works on subnet broadcast (255.255.255.255)

### Minion Server Tests (Phase 4)
- [ ] PUT block → stored correctly in LocalStorage
- [ ] GET block → returns correct data
- [ ] GET after PUT returns same data (round-trip)
- [ ] Out-of-range offset → STATUS=OUT_OF_RANGE

---

## Phase 5 — Integration & System Tests

### Smoke Test (Minimum Viable)
```bash
# Start master with 2 fake minions
./LDS /dev/nbd0 1G &
./fake_minion 7701 &
./fake_minion 7702 &

# Write and read back
dd if=/dev/zero of=/dev/nbd0 bs=4096 count=256
dd if=/dev/nbd0 of=/tmp/readback bs=4096 count=256
cmp /dev/zero /tmp/readback
```

### Fault Injection Test
```bash
# Write, kill minion 1, read back (should succeed via replica)
echo "hello" > /mnt/nbd/testfile
kill $MINION1_PID
cat /mnt/nbd/testfile   # must still return "hello"
```

### Concurrent Load Test
```bash
fio --rw=randrw --bs=4k --numjobs=8 --iodepth=32 \
    --filename=/dev/nbd0 --size=512M --time_based --runtime=30
```
Expected: no crashes, no data corruption (`fio` has built-in verify mode).

---

## Test Infrastructure Requirements

| Need | Tool | Phase |
|---|---|---|
| Unit tests | Custom test framework (current) or Catch2 | Now |
| Mock network | FakeMinion class (build in Phase 2) | Phase 2 |
| Mock clock | Inject via template/interface | Phase 2 |
| Valgrind clean | `valgrind --tool=memcheck` | Ongoing |
| Thread sanitizer | `g++ -fsanitize=thread` | Fix bugs 8,9,10 first |
| Address sanitizer | `g++ -fsanitize=address` | Fix bug 1 first |
| CI | Docker container (already set up) | Phase 6 |

**ThreadSanitizer** — the most valuable tool for this project. It catches races that only manifest under specific scheduling. Run `make run_tests` with `-fsanitize=thread` regularly.

---

## Definition of "Test Passing"

A test passes only when:
- ✅ The binary runs without segfault
- ✅ All assertions succeed
- ✅ Valgrind reports 0 leaks, 0 errors
- ✅ ThreadSanitizer reports 0 data races (after fixing bugs 8, 9, 10)

---

## Related Notes
- [[Known Bugs]]
- [[Risk Register]]
- [[Phase 5 - Integration & Testing]]
