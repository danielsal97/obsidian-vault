2# Known Bugs — Senior Engineering Analysis

These are real bugs in the current Phase 1 implementation. Understanding them deeply is what separates junior from senior level. Each one has a root cause, consequence, and correct fix.

---

## Bug 1 — Bounds Check Too Narrow
**Location:** `services/local_storage/src/LocalStorage.cpp`
**Severity:** 🔴 Critical — silent memory corruption

```cpp
// CURRENT (wrong):
if (data->m_offset > m_storage.size()) { /* error */ }

// The bug: doesn't account for length
// A WRITE at offset=size-100 with length=200 passes the check
// but writes 100 bytes past the end of the vector → undefined behavior

// CORRECT:
if (data->m_offset + data->m_buffer.size() > m_storage.size()) { /* error */ }
```

**Why it matters:** Integer overflow is possible if offset+size wraps around. Use `size_t` carefully and check for overflow before adding.

---

## Bug 2 — m_len Never Initialized
**Location:** `services/communication_protocols/nbd/include/DriverData.hpp`
**Severity:** 🟡 Medium — latent, masked by correct usage

```cpp
// m_len is declared in DriverData but never set in constructor
// LDS.cpp correctly uses m_buffer.size() instead — which IS correct
// But any code that reads m_len directly gets garbage

// Fix: either initialize m_len in constructor, or remove the field
// and use m_buffer.size() everywhere
```

---

## Bug 3 — No Per-Request Error Reply
**Location:** `app/LDS.cpp`
**Severity:** 🔴 Critical — kernel I/O hangs

```cpp
// CURRENT:
try {
    storage.Read(request);
    driver.SendReplay(request);
} // if Read() throws → no SendReplay → kernel never gets reply → hung I/O

// CORRECT:
try {
    storage.Read(request);
} catch (...) {
    request->m_status = DriverData::ERROR;  // mark failure
}
driver.SendReplay(request);  // always reply to kernel
```

**Consequence:** User process issuing read() on /dev/nbd0 hangs forever. Filesystem becomes unresponsive.

---

## Bug 4 — Disconnect() Race Condition
**Location:** `services/communication_protocols/nbd/src/NBDDriverComm.cpp`
**Severity:** 🔴 Critical — TOCTOU race

```cpp
// Disconnect() accesses m_nbdFd (plain int)
// m_signal_thread can call Disconnect() at same time as destructor
// Two threads: close(fd) from destructor + close(fd) from signal thread
// = double-close = undefined behavior (fd may have been reused)

// Fix: use atomic_int for m_nbdFd or protect with mutex
// Or use std::once_flag to ensure Disconnect() runs exactly once
```

---

## Bug 5 — Signal Thread Self-Join Deadlock
**Location:** `services/communication_protocols/nbd/src/NBDDriverComm.cpp`
**Severity:** 🔴 Critical — program hangs on shutdown

```cpp
// m_signal_thread receives SIGINT/SIGTERM
// Its handler calls Disconnect() which eventually calls the destructor
// Destructor calls m_signal_thread.join()
// A thread cannot join itself → deadlock

// Fix: signal thread should set a flag and return
// Let the main thread call join() from the destructor
```

---

## Bug 6 — Constructor Thread Leak
**Location:** `services/communication_protocols/nbd/src/NBDDriverComm.cpp`
**Severity:** 🟡 Medium — resource leak

```cpp
// Constructor sequence:
// 1. SetUpSignals() → starts m_signal_thread
// 2. ioctl(NBD_SET_SOCK) → can throw

// If step 2 throws:
// - Constructor propagates exception
// - Destructor is NEVER called (C++ rule: destroyed objects only)
// - m_signal_thread is running forever in sigwait loop
// - No way to stop it or join it

// Fix: use a guard object or flag before starting thread
// Or: start thread last, after all operations that can throw
```

---

## Bug 7 — Conflicting Signal Handling
**Location:** `app/LDS.cpp` + `NBDDriverComm.cpp`
**Severity:** 🟡 Medium — undefined signal delivery

```cpp
// Reactor sets up signalfd for SIGINT/SIGTERM (epoll-monitored)
// NBDDriverComm has m_signal_thread doing sigwait for same signals
// Both systems compete to receive the same signal
// Result: signal goes to one unpredictably — behavior undefined

// Fix: pick ONE signal handling strategy for the whole process
// signalfd + epoll is the modern correct approach
// Remove NBDDriverComm's signal thread
```

---

## Bug 8 — Dispatcher Not Thread-Safe
**Location:** `design_patterns/observer/include/Dispatcher.hpp`
**Severity:** 🔴 Critical — use-after-free

```cpp
// Dispatcher::m_subs is a std::vector with no mutex

// Thread 1: NotifyAll() → iterates m_subs
// Thread 2: Register() → push_back → vector reallocates

// Thread 1 now has an iterator into freed memory
// Any access = use-after-free = crash

// Fix: protect m_subs with std::shared_mutex
// (shared_lock for NotifyAll, unique_lock for Register/UnRegister)
```

---

## Bug 9 — LocalStorage Not Thread-Safe
**Location:** `services/local_storage/src/LocalStorage.cpp`
**Severity:** 🔴 Critical — data corruption under concurrency

```cpp
// std::vector<char> m_storage has no mutex
// Concurrent Read + Write at overlapping offsets = data race
// Data race on non-atomic type = undefined behavior

// In Phase 1 this is fine (single-threaded request handling)
// In Phase 2+ with ThreadPool executing commands concurrently:
// two WriteCommands to adjacent blocks = UB

// Fix: std::shared_mutex — shared_lock for reads, unique_lock for writes
```

---

## Bug 10 — Static mutex/cv in ThreadPool
**Location:** `utilities/threading/thread_pool/src/thread_pool.cpp`
**Severity:** 🔴 Critical — cross-pool interference

```cpp
// m_mutex and m_cv are static members
// All ThreadPool instances SHARE the same condition_variable

// Calling tp2.Resume() → cv.notify_all() wakes ALL threads
// from ALL ThreadPool instances, including tp1's suspended threads

// Fix: make m_mutex and m_cv instance members (not static)
```

---

## Bug 11 — CallBack Double UnRegister
**Location:** `design_patterns/observer/include/CallBack.hpp`
**Severity:** 🟢 Low — harmless but messy

```cpp
// ICallBack stores m_disp and calls UnRegister in its destructor
// CallBack ALSO stores m_disp (because ICallBack::m_disp is private)
// and calls UnRegister in ITS destructor

// Result: UnRegister called twice
// Harmless (std::remove on missing element is a no-op)
// but wasteful and architecturally wrong

// Fix: make ICallBack::m_disp protected so CallBack can access it
```

---

## Bug 12 — assert Instead of Exception for socketpair
**Location:** `services/communication_protocols/nbd/src/NBDDriverComm.cpp`
**Severity:** 🟡 Medium — release build silent failure

```cpp
// assert(socketpair(...) == 0)
// In debug builds: crashes on failure with helpful message ✅
// In release builds (-DNDEBUG): assert removed → code continues
//   with uninitialized file descriptors → silent UB

// Fix: if (socketpair(...) != 0) throw std::runtime_error(strerror(errno));
```

---

## Summary Table

| # | Bug | Severity | Status |
|---|---|---|---|
| 1 | Bounds check missing length | 🔴 Critical | Known |
| 2 | m_len uninitialized | 🟡 Medium | Known |
| 3 | No error reply to kernel | 🔴 Critical | Known |
| 4 | Disconnect() race | 🔴 Critical | Known |
| 5 | Signal thread self-join | 🔴 Critical | Known |
| 6 | Constructor thread leak | 🟡 Medium | Known |
| 7 | Conflicting signal handling | 🟡 Medium | Known |
| 8 | Dispatcher not thread-safe | 🔴 Critical | Known |
| 9 | LocalStorage not thread-safe | 🔴 Critical | Known |
| 10 | Static mutex/cv shared | 🔴 Critical | Known |
| 11 | Double UnRegister | 🟢 Low | Known |
| 12 | assert in production | 🟡 Medium | Known |

---

## What This Tells You as a Senior Engineer

The architecture is correct — the patterns are well-chosen and the design is clean. The bugs are all implementation details, not structural problems. A senior engineer would:

1. Prioritize bugs 3, 4, 5 (they cause hangs/crashes under normal use)
2. Fix 8 and 9 before adding concurrency in Phase 2
3. Fix 10 before using multiple ThreadPools
4. Accept 11 as tech debt

---

## Related Notes
- [[NBDDriverComm]]
- [[LocalStorage]]
- [[Observer]]
- [[Threading Deep Dive]]
