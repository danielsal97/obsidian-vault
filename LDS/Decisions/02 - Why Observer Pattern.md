# Decision: Why Observer Pattern for Events

## Decision

Use the **Observer pattern** (Dispatcher + ICallBack) for event notification instead of direct method calls.

---

## The Problem with Direct Calls

```cpp
// BAD — tight coupling
class DirMonitor {
    void onFileCreated(const std::string& path) {
        pnp_.LoadPlugin(path);     // DirMonitor must know about PNP
        logger_.Log("file: " + path);   // DirMonitor must know about Logger
        audit_.Record(path);       // Adding audit = modifying DirMonitor
    }
private:
    PNP& pnp_;
    Logger& logger_;
    Audit& audit_;  // dependency grows every time we add a listener
};
```

Every new listener = a new dependency injected into DirMonitor. Adding a third listener means modifying DirMonitor's constructor, header, and implementation.

---

## Observer Solution

```cpp
// GOOD — DirMonitor knows only about Dispatcher
class DirMonitor {
    void onFileCreated(const std::string& path) {
        dispatcher_.NotifyAll(DirEvent{path, "CREATE"});
        // DirMonitor doesn't know who receives this
    }
private:
    Dispatcher<DirEvent>& dispatcher_;  // only one dependency
};

// Adding a new listener = zero changes to DirMonitor
CallBack<DirEvent, AuditLogger> audit_cb(&dispatcher, &audit, &AuditLogger::OnFile);
```

---

## Benefits

| Benefit | Detail |
|---|---|
| **Open/Closed** | Add observers without changing the publisher |
| **Testability** | Test DirMonitor by checking dispatcher calls, not PNP |
| **Multiple listeners** | N observers for one event, trivially |
| **Loose coupling** | DirMonitor doesn't import or know about PNP |
| **RAII cleanup** | `CallBack` auto-registers/unregisters |

---

## When Not to Use Observer

- When there is exactly one listener that will never change → direct call is simpler
- When order of notification matters and Observer doesn't guarantee it
- When the callback must return a value → Observer is fire-and-forget

---

## In LDS

The Observer pattern is used for:
1. `DirMonitor` → `PNP` (file system events)
2. `Watchdog` → `RAID01Manager` (minion health state changes) — planned
3. `AutoDiscovery` → `RAID01Manager` (new minion detected) — planned

---

## Related Notes
- [[Observer]]
- [[DirMonitor]]
- [[Why Templates not Virtual Functions]]
