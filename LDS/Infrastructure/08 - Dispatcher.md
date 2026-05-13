# Dispatcher

**Location:** `design_patterns/observer/include/Dispatcher.hpp`  
**Status:** ✅ Implemented  
**Layer:** Tier 2 — Framework

---

## What It Does

The event broadcast hub. Holds a list of subscribers (`ICallBack*`). When `NotifyAll(msg)` is called, every subscriber gets the message. Completely decouples the event source from the handlers.

Used by `DirMonitor` to broadcast new plugin paths to `SoLoader`.

---

## Interface

```cpp
template <typename Msg>
class Dispatcher {
public:
    void Register(ICallBack<Msg>* sub);    // add subscriber
    void UnRegister(ICallBack<Msg>* sub);  // remove subscriber
    void NotifyAll(const Msg& msg);        // broadcast to all
};
```

Subscribers **auto-register** in their constructor (via `ICallBack`) and **auto-unregister** in their destructor. You never call `Register`/`UnRegister` manually.

---

## How It's Wired

```
DirMonitor          SoLoader
    │                   │
    │  Dispatcher<string>  │
    │◄──────────────────►│
    │  NotifyAll(path)   │
    │──────────────────►│
                    OnLoad(path)
                    dlopen(path)
```

---

## Internals

```cpp
std::vector<ICallBack<Msg>*> m_subs;   // raw pointers, not owned
```

`NotifyAll` iterates the vector and calls `sub->Notify(msg)` on each.  
`~Dispatcher` calls `sub->NotifyEnd()` on all remaining subscribers.

---

## Known Bug #8 — Not Thread-Safe

```cpp
// Thread 1: NotifyAll() → iterating m_subs
// Thread 2: Register() → push_back → vector reallocates → Thread 1 crashes

// Fix:
mutable std::shared_mutex m_mutex;
// shared_lock for NotifyAll, unique_lock for Register/UnRegister
```

**Must fix before Phase 2** — concurrent command execution means Register/NotifyAll can be called from different threads.

---

## Related Notes
- [[Design Patterns/Observer]] — pattern overview
- [[Engineering/Observer Pattern Internals]] — ICallBack/CallBack mechanics
- [[Components/DirMonitor]] — main user of Dispatcher
- [[Engineering/Known Bugs]] — Bug #8
