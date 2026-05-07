# Phase 2 Execution Plan — Data Management & Network

**Dates:** 2026-05-01 → 2026-05-28  
**Budget:** 46 hours  
**Prerequisite:** Fix bugs 8, 9, 10 before writing any Phase 2 code

---

## Pre-Phase 2 Gate (2 hrs — must do first)

These bugs will cause crashes the moment Phase 2 runs concurrent commands. Fix them before writing a single new class.

| Bug | File | Fix |
|---|---|---|
| #8 Dispatcher not thread-safe | `Dispatcher.hpp` | Add `std::shared_mutex` to `m_subs` |
| #9 LocalStorage not thread-safe | `LocalStorage.cpp` | Add `std::shared_mutex` to `m_storage` |
| #10 Static mutex/cv in ThreadPool | `thread_pool.hpp/cpp` | Remove `static` from `m_mutex` + `m_cv` |

**Verify:** Run `make run_tests` under ThreadSanitizer (`-fsanitize=thread`) with no races before proceeding.

---

## Week 1 (May 1–7): Bug Fixes + RAID01Manager (14 hrs)

### Day 1-2: Fix Critical Bugs (4 hrs)
- [ ] Fix Bug #8 — `Dispatcher::m_subs` → add `shared_mutex`
- [ ] Fix Bug #9 — `LocalStorage::m_storage` → add `shared_mutex`
- [ ] Fix Bug #10 — `ThreadPool` → remove `static` from mutex/cv
- [ ] Verify all 9 test binaries still pass
- [ ] Verify ThreadSanitizer clean

### Day 3-5: RAID01Manager (10 hrs)

**New files:**
```
services/storage/include/RAID01Manager.hpp
services/storage/src/RAID01Manager.cpp
test/unit/test_raid01.cpp
```

**Implementation order:**
1. `Minion` struct (id, ip, port, status, last_seen)
2. `AddMinion(id, ip, port)` — register a minion
3. `GetBlockLocation(block_num)` → `{primary_id, replica_id}`
   - primary = `block_num % active_minion_count`
   - replica = `(block_num + 1) % active_minion_count`
4. `FailMinion(id)` — marks FAILED, remaps affected blocks
5. `SaveMapping(path)` / `LoadMapping(path)` — JSON or binary
6. Thread-safety: `std::shared_mutex` for concurrent read/FailMinion

**Tests:**
- [ ] Mapping correct for 2, 3, 4, 5 minions
- [ ] FailMinion skips failed in GetBlockLocation
- [ ] SaveMapping + LoadMapping round-trip

---

## Week 2 (May 8–14): MinionProxy + Wire Protocol (14 hrs)

**New files:**
```
services/network/include/MinionProxy.hpp
services/network/src/MinionProxy.cpp
services/network/include/FakeMinion.hpp   ← test helper
services/network/src/FakeMinion.cpp
test/unit/test_minion_proxy.cpp
```

### MinionProxy (10 hrs)

**Implementation order:**
1. `RequestHeader` / `ResponseHeader` structs with `#pragma pack(1)`
2. Byte-order conversion helpers (`htonl`, `htobe64`, etc.)
3. `AddMinion(id, ip, port)` — create UDP socket per minion
4. `SendPutBlock(minion_id, offset, data)` → `MSG_ID`
5. `SendGetBlock(minion_id, offset, length)` → `MSG_ID`
6. `atomic<uint32_t>` MSG_ID counter

Wire format: see [[Wire Protocol Spec]]

### FakeMinion (4 hrs)

```cpp
class FakeMinion {
    // Background thread: recvfrom() loop
    // Config: WillRespondWith, WillTimeout, WillDelayResponse
    // Inspection: GetReceivedPackets()
};
```

**Tests:**
- [ ] PUT serializes header fields correctly (byte-by-byte check)
- [ ] GET serializes correctly
- [ ] MSG_IDs are unique across calls
- [ ] Multiple minions can be added

---

## Week 3 (May 15–21): ResponseManager + Scheduler (14 hrs)

**New files:**
```
services/network/include/ResponseManager.hpp
services/network/src/ResponseManager.cpp
services/execution/include/Scheduler.hpp
services/execution/src/Scheduler.cpp
test/unit/test_response_manager.cpp
test/unit/test_scheduler.cpp
```

### ResponseManager (8 hrs)

**Implementation order:**
1. UDP listen socket on port 7700
2. Background recv thread
3. `RegisterCallback(msg_id, fn)` — `unordered_map` + `mutex`
4. Parse incoming packets — extract MSG_ID, dispatch callback
5. `UnregisterCallback(msg_id)` — cleanup after response or timeout
6. Graceful `Stop()` — closes socket, joins thread

**Tests:**
- [ ] Callback fires when response arrives
- [ ] Unknown MSG_ID → silently ignored
- [ ] Multiple concurrent callbacks (thread-safe)
- [ ] Stop() doesn't deadlock

### Scheduler (6 hrs)

**Implementation order:**
1. `MockClock` interface (injectable) — for deterministic tests
2. `Track(msg_id, deadline, retry_fn)` — adds to pending map
3. `OnResponse(msg_id)` — removes from pending
4. Poll loop (background thread): check expired entries
5. Exponential backoff: 1s → 2s → 4s → mark failed
6. `GiveUp(msg_id)` callback — called after 3 retries

**Tests:**
- [ ] Response before timeout → no retry
- [ ] Timeout → retry with doubled interval
- [ ] 3 retries → give up callback fires
- [ ] Concurrent: 100 requests tracked simultaneously

---

## Week 4 (May 22–28): InputMediator + Commands + Integration (4 hrs)

**New files:**
```
services/commands/include/ReadCommand.hpp
services/commands/include/WriteCommand.hpp
services/commands/src/ReadCommand.cpp
services/commands/src/WriteCommand.cpp
services/input/include/InputMediator.hpp
services/input/src/InputMediator.cpp
test/integration/test_smoke.cpp
```

### InputMediator (2 hrs)

```cpp
class InputMediator {
    InputMediator(IDriverComm& driver, ThreadPool& tp,
                  RAID01Manager& raid, MinionProxy& proxy,
                  ResponseManager& rm);

    void HandleEvent(int fd);  // called by Reactor
    // → ReceiveRequest → create Command → tp.AddCommand
};
```

### ReadCommand / WriteCommand (1 hr)

Thin wrappers that call RAID → Proxy → wait for callbacks.

### Integration Smoke Test (1 hr)

```
Start master + FakeMinion(s)
Write 100 blocks
Read them all back
Assert data matches
```

---

## Done Criteria for Phase 2

- [ ] All 6 pre-existing critical bugs fixed (8, 9, 10 before start; 3, 4, 5 before integration)
- [ ] `test_raid01` passing — all mapping tests green
- [ ] `test_minion_proxy` passing — serialization correct
- [ ] `test_response_manager` passing — async dispatch correct
- [ ] `test_scheduler` passing — timeout + retry logic correct
- [ ] Integration smoke test: write → read → verify for 100 blocks
- [ ] ThreadSanitizer: 0 data races
- [ ] Valgrind: 0 leaks

---

## Risk Flags

| Risk | Likelihood | Mitigation |
|---|---|---|
| UDP async timing in CI | High | Use FakeMinion with deterministic response, not real network |
| Scheduler timing flakiness | Medium | Injectable clock, never `sleep` in tests |
| RAID block formula off-by-one | Low | Test boundary cases: block 0, last block, wrap-around |
| Phase 2 scope creep | Medium | Stop at smoke test passing — Phase 3 adds reliability |

---

## Related Notes
- [[Phase 2 - Data Management & Network]]
- [[Test Strategy]]
- [[Known Bugs]]
- [[Wire Protocol Spec]]
- [[Risk Register]]
