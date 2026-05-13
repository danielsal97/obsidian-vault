# Lessons Learned

## Phase 1 — What Worked, What Was Hard

### What Worked Well

| Practice | Result |
|---|---|
| **RAII everywhere** | Zero memory leaks. Valgrind clean. Deterministic cleanup under exceptions |
| **Template-based Observer** | Type errors caught at compile time. No accidental wrong-event-type bugs |
| **Observer pattern for events** | DirMonitor completely decoupled from PNP. Adding observers = zero changes to DirMonitor |
| **Modular approach** | Each component testable in isolation. 9 test suites, all passing independently |
| **`IN_CLOSE_WRITE` instead of `IN_CREATE`** | Plugin loading reliable. No partial-file load failures |
| **Singleton lazy init** | No SIOF. Works across all TUs regardless of static init order |

---

### Challenges Overcome

#### 1. Race Condition in DirMonitor
**Problem:** Filesystem monitoring would occasionally emit duplicate events or miss events under load.
**Root cause:** Background inotify thread was accessing shared state without a lock.
**Fix:** Added mutex around the event queue. Lesson: any background thread touching shared state needs synchronization.

#### 2. Static Constructor Ordering (SIOF)
**Problem:** Plugin loading would crash on startup if Logger initialized after Factory.
**Root cause:** Static global variables have undefined initialization order across TUs.
**Fix:** Singleton lazy initialization — instance created on first call, not at program start. Lesson: never use raw static globals for shared services.

#### 3. Memory Management with Shared Libraries
**Problem:** `dlclose()` was being called while plugin code was still executing (from callback).
**Root cause:** SoLoader destructor called `dlclose` before ensuring no threads were in plugin code.
**Fix:** RAII Loader with careful lifetime management. Lesson: lifetime of `dlopen` handle must outlive all code executing from that library.

#### 4. Thread Safety in Global Singleton State
**Problem:** Factory and Logger accessed concurrently by multiple threads crashed occasionally.
**Root cause:** Registry map and log output had no mutex.
**Fix:** Mutex in Logger. Double-checked locking in Singleton. Lesson: any global state accessed from multiple threads needs explicit synchronization.

---

### Technical Debt Carried Into Phase 2

| Item | Description | Fix When |
|---|---|---|
| Dispatcher not thread-safe | `m_subs` vector unprotected | Before Phase 2 (concurrency) |
| LocalStorage not thread-safe | `m_storage` unprotected | Before Phase 2 (concurrency) |
| NBDDriverComm signal race | Disconnect() / signal thread race | Phase 3 (reliability work) |
| Static ThreadPool mutex/cv | All instances share CV | Before using multiple ThreadPools |

---

### Process Lessons

1. **Write tests while coding, not after.** Components written with tests-first had fewer integration surprises.

2. **Document the WHY, not just the WHAT.** When a design decision (e.g., `IN_CLOSE_WRITE`) wasn't documented, we wasted time re-discovering the reason later.

3. **The hardest bugs are timing bugs.** Race conditions in DirMonitor only appeared under load. Add concurrency stress tests early, not at the end.

4. **Phases build on each other.** Starting Phase 2 before Phase 1 was solid would have caused rework. Complete each phase before moving on.

---

## What Phase 2 Should Do Differently

Based on Phase 1 experience:

1. **Write mock objects first.** Before implementing MinionProxy, write `FakeMinionProxy` for testing. Don't wait until real network is needed.

2. **Fix the 6 critical bugs** from Phase 1 before adding concurrency.

3. **Define the wire protocol on paper** before writing any serialization code. Agree on the byte layout, then implement it.

4. **Integration test early.** Don't wait for Phase 5 to test master ↔ minion communication. Wire a simple smoke test in Phase 2.

---

## Related Notes
- [[Known Bugs]]
- [[Risk Register]]
- [[Project Status & Metrics]]
