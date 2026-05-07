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

See [[../C++/Smart Pointers]] — `weak_ptr` for non-owning references.

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
- [[../C++/Virtual Functions]] — observer interface uses virtual functions
- [[../C++/Smart Pointers]] — weak_ptr for safe observer references
- [[../C++/STL Containers]] — vector of observers
