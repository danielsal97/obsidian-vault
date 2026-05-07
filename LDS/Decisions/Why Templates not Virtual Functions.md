# Decision: Why Templates (not `void*` virtual functions) for Observer

## Decision

Use **`template <typename T>`** for `Dispatcher` and `ICallBack` rather than a non-typed virtual interface.

---

## The Problem with `void*`

```cpp
// BAD — loses type information
class IObserver {
    virtual void update(void* event) = 0;
};

void DirMonitor::onEvent(void* event) {
    dispatcher.notify(event);  // what type is this? unknown at compile time
}

class PNP : public IObserver {
    void update(void* event) override {
        // Must cast blindly — undefined behavior if wrong
        auto* file_event = static_cast<FileEvent*>(event);
    }
};
```

Problems:
- `static_cast` can be wrong silently
- No compile-time check that you're sending the right event type
- Runtime bugs are hard to find

---

## Templates Solve This

```cpp
// GOOD — type preserved through the chain
template <typename T>
class ICallBack {
    virtual void Notify(const T& msg) = 0;
};

template <typename T>
class Dispatcher {
    void NotifyAll(const T& msg);   // T is known at compile time
};

// Usage:
Dispatcher<FileEvent>     file_dispatcher;  // can ONLY send FileEvent
Dispatcher<NetworkEvent>  net_dispatcher;   // can ONLY send NetworkEvent

// Compile error — type mismatch caught at compile time:
// file_dispatcher.NotifyAll(NetworkEvent{});  ❌ error
```

---

## Trade-offs

| | Templates | `void*` virtual |
|---|---|---|
| Type safety | ✅ Compile-time | ❌ Runtime only |
| Performance | ✅ Zero overhead | ❌ Virtual dispatch |
| Flexibility | ⚠️ One dispatcher per T | ✅ One dispatcher for all |
| Code size | ⚠️ Instantiated per T | ✅ Single implementation |
| Debugging | ✅ Errors at compile time | ❌ Errors at runtime |

For LDS, the number of event types is small and known at compile time — templates are the clear winner.

---

## Related Notes
- [[Observer]]
- [[DirMonitor]]
