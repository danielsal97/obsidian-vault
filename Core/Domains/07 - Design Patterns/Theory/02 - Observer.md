# Observer Pattern

One object (subject/publisher) notifies a list of dependents (observers/subscribers) when its state changes, without knowing who they are.

---

## Structure

```
Subject ──── notifies ────► Observer1
                       ────► Observer2
                       ────► Observer3
```

Subject holds a list of observers. When something changes, it calls `notify()` on each. Observers implement a common interface.

---

## Implementation

```cpp
// Observer interface:
class IObserver {
public:
    virtual void on_event(const std::string& event) = 0;
    virtual ~IObserver() = default;
};

// Subject (publisher):
class EventSource {
    std::vector<IObserver*> m_observers;
public:
    void subscribe(IObserver* obs) { m_observers.push_back(obs); }
    
    void unsubscribe(IObserver* obs) {
        m_observers.erase(
            std::remove(m_observers.begin(), m_observers.end(), obs),
            m_observers.end()
        );
    }
    
    void trigger(const std::string& event) {
        for (auto* obs : m_observers) {
            obs->on_event(event);
        }
    }
};

// Concrete observer:
class Logger : public IObserver {
    void on_event(const std::string& event) override {
        std::cout << "LOG: " << event << "\n";
    }
};

// Usage:
EventSource src;
Logger logger;
src.subscribe(&logger);
src.trigger("block_written");   // Logger::on_event called
```

---

## Thread Safety

If observers are added/removed while notifications are happening (from another thread), the `m_observers` vector needs protection:

```cpp
std::mutex m_mutex;
std::vector<IObserver*> m_observers;

void trigger(const std::string& event) {
    std::vector<IObserver*> copy;
    {
        std::lock_guard<std::mutex> lk(m_mutex);
        copy = m_observers;   // snapshot — don't hold lock during notification
    }
    for (auto* obs : copy) {
        obs->on_event(event);
    }
}
```

Holding the lock during `on_event` causes deadlocks if the observer tries to subscribe/unsubscribe in its callback.

---

## Modern C++ — Function Callbacks

Instead of a full interface hierarchy, accept `std::function`:

```cpp
class EventSource {
    std::vector<std::function<void(const std::string&)>> m_handlers;
public:
    void subscribe(std::function<void(const std::string&)> handler) {
        m_handlers.push_back(std::move(handler));
    }
    
    void trigger(const std::string& event) {
        for (auto& fn : m_handlers) fn(event);
    }
};

// Subscribe a lambda:
src.subscribe([](const std::string& e) {
    std::cout << "received: " << e << "\n";
});
```

This is simpler but unsubscribing is harder (you lose the identity of the lambda).

---

## Weak Pointer Observers

If observers can be destroyed before the subject, dangling pointer risk:

```cpp
std::vector<std::weak_ptr<IObserver>> m_observers;

void trigger(const std::string& event) {
    m_observers.erase(
        std::remove_if(m_observers.begin(), m_observers.end(),
            [](const auto& wp) { return wp.expired(); }),
        m_observers.end()
    );
    for (auto& wp : m_observers) {
        if (auto obs = wp.lock()) {
            obs->on_event(event);
        }
    }
}
```

See [[02 - Smart Pointers]] — `weak_ptr` for non-owning references.

---

## When to Use

- One-to-many notification without coupling sender to receivers
- GUI events (button click → multiple listeners)
- Logging/monitoring hooks (new block written → log, metrics, replication)
- Pub/sub systems

---

## LDS Context

LDS `ResponseManager` observes incoming UDP packets from minions. The `Scheduler` observes deadline timers. Each UDP response triggers an observer chain:

```
UDP recv → ResponseManager::on_response() 
         → match MSG_ID to pending request
         → notify Scheduler (remove from retry queue)
         → notify caller callback (wake waiting thread)
```

---

## Related Notes

- [[Factory]] — subjects often created via factory
- [[06 - Virtual Functions]] — observer interface uses virtual functions
- [[02 - Smart Pointers]] — weak_ptr for safe observer references
- [[08 - STL Containers]] — vector of observers

---

## Understanding Check

> [!question]- Why does the thread-safe trigger() implementation copy the observer list before iterating, rather than holding the mutex during on_event() calls?
> Holding the mutex during on_event() creates a potential deadlock: if an observer's callback calls subscribe() or unsubscribe() on the same subject, it will try to acquire the mutex that the calling thread already holds — a classic self-deadlock. Copying the list under the lock and then releasing it before iterating means the lock is held only long enough to snapshot the state. The tradeoff is that an observer added or removed while notifications are in flight may not see the current event (missed notification) or may receive a final notification after removal — acceptable in most cases and far better than deadlock.

> [!question]- What goes wrong if an observer is destroyed while the subject still holds a raw IObserver* to it in m_observers?
> The raw pointer becomes dangling. The next time trigger() is called, it iterates m_observers and calls obs->on_event() on a pointer to freed memory — undefined behavior that typically manifests as a crash or silent data corruption. The weak_ptr<IObserver> pattern solves this: expired() returns true once the observer's owning shared_ptr is destroyed, and lock() returns nullptr. The trigger() loop can safely skip expired observers and optionally prune them from the list, without ever dereferencing a dangling pointer.

> [!question]- In LDS, the ResponseManager matches incoming UDP responses to pending requests by MSG_ID. Is this observer pattern, and where does the analogy hold or break?
> It is a form of observer pattern, but more targeted. A generic observer pattern broadcasts to all subscribers regardless of content. LDS's ResponseManager is closer to a promise/callback model: when a request is submitted with MSG_ID=42, a specific callback is registered for that MSG_ID only, not for all events. When the UDP response with MSG_ID=42 arrives, only that one callback fires. The analogy holds in that the UDP socket is the "subject" emitting events, and pending-request callbacks are "observers" — but the subject selects the specific observer by MSG_ID rather than broadcasting to all, which is a key design difference from classic Observer.

> [!question]- Why is unsubscribing a lambda harder than unsubscribing a pointer-based IObserver, and what are the practical implications?
> std::function objects have no identity — you cannot compare two functions for equality or store a "handle" that uniquely identifies a lambda after registration. To unsubscribe a raw IObserver*, you search m_observers for the matching pointer and erase it. To unsubscribe a lambda, you have no comparable search key. The practical workaround is to return an integer "subscription ID" at subscribe time and store a map<int, std::function> instead of a vector — unsubscribing by ID. In LDS, if ResponseManager used lambdas per MSG_ID stored in a map<MSG_ID, callback>, cancellation (e.g., on timeout) would erase by MSG_ID, which is clean and efficient.

> [!question]- What is the "lapsed listener" problem and when would it affect LDS's observer chain?
> The lapsed listener problem occurs when an observer forgets to unsubscribe before being destroyed, leaving a dangling reference in the subject's list. In LDS, if a pending-request callback captures a reference to a Scheduler object that has been shut down and destroyed, the ResponseManager's trigger will call into freed memory when the next UDP response arrives — even for an in-flight request from before shutdown. The fix is a strict shutdown order (ResponseManager stopped before Scheduler) and/or using weak_ptr callbacks so that expired observers are silently skipped rather than called.
