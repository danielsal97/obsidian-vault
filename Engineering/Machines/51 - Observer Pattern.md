# Observer Pattern — The Machine

## The Model
A subscription service. The Subject (publisher) holds a list of Observers (subscribers). When something changes, the Subject rings every subscriber's doorbell without knowing who they are — only that they all have a doorbell (implement the callback interface). Subscribers register themselves; the Subject never imports subscriber headers.

## How It Moves

```
Subject (Dispatcher<T>):                Observers (callbacks):
───────────────────────                 ──────────────────────
  m_callbacks = [cb0, cb1, cb2]         cb0: lambda → log the event
                                         cb1: lambda → store to LocalStorage
  Notify(event):                         cb2: lambda → forward to TCP client
    for each cb in m_callbacks:
      cb(event)                         ← all called with same event
```

**The decoupling:** the Subject doesn't know what the callbacks do. Adding a new Observer (new reaction to an event) requires no change to the Subject. Adding a new event type requires no change to existing Observers.

**Template vs virtual in LDS:**
- Virtual: `class IObserver { virtual void onEvent(Event) = 0; }` — runtime dispatch, all observers must share the same interface
- Template (`Dispatcher<T>`): callbacks are `std::function<void(T)>` — any callable (lambda, function pointer, method), type-erased, no base class needed, slightly faster (no virtual dispatch overhead)

## The Blueprint

```cpp
template<typename T>
class Dispatcher {
    std::vector<std::function<void(T)>> m_callbacks;
public:
    void Register(std::function<void(T)> cb) {
        m_callbacks.push_back(std::move(cb));
    }
    void Notify(const T& event) {
        for (auto& cb : m_callbacks) cb(event);
    }
};

// Usage:
Dispatcher<Request> dispatcher;
dispatcher.Register([&storage](const Request& r) { storage.Write(r); });
dispatcher.Register([&logger](const Request& r) { logger.Log(r); });

dispatcher.Notify(incoming_request);   // both callbacks fire
```

## Where It Breaks

- **Callback throws**: exception in one callback skips remaining callbacks. Wrap each callback in try/catch in `Notify`.
- **Callback modifies the callback list**: adding/removing observers during `Notify` invalidates the vector iterator. Copy the list before iterating, or defer modifications.
- **Dangling reference in lambda**: `[&storage]` captures `storage` by reference. If `storage` is destroyed before the dispatcher, the lambda holds a dangling reference.

## In LDS

`design_patterns/observer/include/ICallBack.hpp` + `CallBack.hpp`

LDS uses `ICallBack<T>` (virtual interface) and `CallBack<T>` (template concrete implementation). `InputMediator` acts as both the Subject and the dispatcher — when it receives a request via `RecvRequest`, it calls `Notify` on all registered handlers. Handlers are registered at startup: the Read handler, Write handler, and Flush handler each subscribe to their respective request types.

## Validate

1. Three handlers are registered with `InputMediator`. A WRITE request arrives. All three are called. Handler 2 throws. Does Handler 3 execute?
2. A handler lambda captures `[&storage]`. `storage` is a local variable that goes out of scope while the dispatcher still exists. The next `Notify` call invokes the lambda. What happens?
3. Why does LDS use `std::function<void(T)>` instead of a virtual `IObserver` base class? What specific capability does this enable that virtual dispatch does not?
