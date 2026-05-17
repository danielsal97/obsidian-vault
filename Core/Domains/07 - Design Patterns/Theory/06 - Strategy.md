# Strategy Pattern

Defines a family of algorithms, encapsulates each one, and makes them interchangeable at runtime. The caller doesn't know which algorithm is executing.

---

## Structure

```
Context ──── uses ────► IStrategy (interface)
                              │
                   ┌──────────┼──────────┐
                   ▼          ▼          ▼
             StrategyA   StrategyB   StrategyC
```

The context holds a pointer to the strategy and delegates the algorithm to it.

---

## Implementation

```cpp
// Strategy interface:
class ISortStrategy {
public:
    virtual void sort(std::vector<int>& data) = 0;
    virtual ~ISortStrategy() = default;
};

// Concrete strategies:
class QuickSort : public ISortStrategy {
    void sort(std::vector<int>& data) override {
        std::sort(data.begin(), data.end());
    }
};

class BubbleSort : public ISortStrategy {
    void sort(std::vector<int>& data) override {
        for (size_t i = 0; i < data.size(); ++i)
            for (size_t j = 0; j < data.size() - 1 - i; ++j)
                if (data[j] > data[j+1]) std::swap(data[j], data[j+1]);
    }
};

// Context:
class Sorter {
    std::unique_ptr<ISortStrategy> m_strategy;
public:
    explicit Sorter(std::unique_ptr<ISortStrategy> s) : m_strategy(std::move(s)) {}
    
    void set_strategy(std::unique_ptr<ISortStrategy> s) {
        m_strategy = std::move(s);
    }
    
    void sort(std::vector<int>& data) {
        m_strategy->sort(data);
    }
};

// Usage:
Sorter sorter(std::make_unique<QuickSort>());
sorter.sort(data);

sorter.set_strategy(std::make_unique<BubbleSort>());
sorter.sort(data);   // now uses bubble sort
```

---

## Strategy with std::function (Modern C++)

For simple strategies, a function is enough — no class hierarchy needed:

```cpp
class Sorter {
    std::function<void(std::vector<int>&)> m_sort;
public:
    explicit Sorter(std::function<void(std::vector<int>&)> fn) : m_sort(fn) {}
    void sort(std::vector<int>& data) { m_sort(data); }
};

// Usage:
Sorter s([](auto& v) { std::sort(v.begin(), v.end()); });
```

---

## Strategy vs Template Method

| | Strategy | Template Method |
|---|---|---|
| Mechanism | Runtime polymorphism (virtual) | Compile-time (template) or inheritance |
| Switch algorithm | At runtime | At compile time |
| Code reuse | In the interface | In the base class |

Strategy: "which algorithm to use" decided at runtime (config, user input).  
Template method: the skeleton is fixed, subclasses fill in specific steps.

---

## LDS Context

**Storage strategy** — the same read/write interface allows swapping LocalStorage for a remote storage:

```cpp
class InputMediator {
    IStorage* m_storage;   // strategy — injected
public:
    void handle(DriverData* d) {
        if (d->m_type == READ) m_storage->Read(d);
        else                    m_storage->Write(d);
    }
};
```

`IStorage` is the strategy interface. `LocalStorage` and (future) `RAIDStorage` are concrete strategies.

**Retry strategy** — exponential backoff vs fixed interval vs no retry:
```cpp
class IRetryStrategy {
public:
    virtual std::chrono::milliseconds next_delay(int attempt) = 0;
};

class ExponentialBackoff : public IRetryStrategy {
    std::chrono::milliseconds next_delay(int attempt) override {
        return std::chrono::milliseconds(1000 << attempt);  // 1s, 2s, 4s
    }
};
```

---

## When to Use

- You have multiple algorithms that can be swapped at runtime
- You want to eliminate conditionals that select algorithm variants
- You need to unit test algorithms independently from the context

---

## Related Notes

- [[Factory]] — factory often selects which strategy to create
- [[06 - Virtual Functions]] — strategy uses virtual dispatch
- [[04 - Templates]] — policy-based design is compile-time strategy
- [[02 - Smart Pointers]] — own strategy with unique_ptr

---

## Understanding Check

> [!question]- Why does IStorage in LDS qualify as a Strategy interface rather than just a base class for inheritance, and what design principle does this embody?
> A plain base class with virtual methods enables polymorphism but doesn't by itself indicate intent. IStorage is a Strategy because the concrete implementation is chosen externally (injected into InputMediator) and can be swapped at any time — LocalStorage in production, MockStorage in tests, a future NetworkStorage with no change to the mediator. The design principle is that the behavior (which storage algorithm to use) is separated from the context that uses it (InputMediator). This is Strategy: the context delegates to a replaceable algorithm object rather than hard-coding the behavior.

> [!question]- What goes wrong if InputMediator stores IStorage by value instead of by pointer, and you try to swap the strategy at runtime?
> Storing by value would require knowing the concrete type at compile time — you'd have to template InputMediator on the storage type, making runtime swapping impossible. More critically, if you store a base class by value and assign a derived object, object slicing occurs: only the IStorage base portion is copied, the derived class's data members are discarded, and the virtual function table pointer still points to IStorage's vtable (or undefined behavior if IStorage has pure virtual methods). The concrete override is lost. Storing as a pointer (or unique_ptr) keeps the full derived object alive and preserves virtual dispatch.

> [!question]- What is the difference between a Strategy and a Template Method pattern, and why does the choice between them matter for LDS's retry logic?
> Strategy selects the full algorithm at runtime via a pointer to a replaceable object. Template Method fixes the algorithm's skeleton in a base class and delegates specific steps to virtual methods in subclasses — the skeleton is invariant, only the details change. For LDS retry logic: with Strategy, ExponentialBackoff and FixedIntervalBackoff are separate classes implementing IRetryStrategy::next_delay() — the entire delay calculation is swappable. With Template Method, a RetryPolicy base class defines the retry loop structure (try, check deadline, call next_delay(), sleep) and subclasses override only next_delay(). Strategy is better here if retry policies need to be configured or changed at runtime (e.g., loaded from config); Template Method is better if the loop structure varies between strategies.

> [!question]- Why is std::function a valid Strategy implementation for simple cases, and when does the class hierarchy version become necessary?
> std::function holds any callable — lambda, function pointer, or functor — with a consistent call interface. It works as a Strategy when the algorithm has no state beyond what's captured in the closure and no interface beyond a single call signature. The class hierarchy becomes necessary when: the strategy has multiple methods (e.g., both next_delay() and reset()), strategies need to be queried for metadata (can_retry(), get_name() for logging), strategies carry significant internal state that benefits from a proper class, or you need polymorphic copying (a std::function wrapping a lambda can't be cloned without knowing its type).

> [!question]- In LDS, if the retry strategy is changed from ExponentialBackoff to FixedInterval while a request is mid-flight (already in the retry queue), what should happen and what could go wrong?
> Ideally, in-flight requests should complete with the strategy that was active when they were submitted — changing mid-flight is unpredictable. If the Scheduler stores a reference to the current IRetryStrategy and the strategy object is replaced (old one deleted), any in-flight request that fires its next retry will call next_delay() through a dangling pointer — undefined behavior. The safe design is either to capture the strategy by shared_ptr at submission time (so each request holds its own reference that keeps the strategy alive), or to only change strategy between requests, never during an active retry sequence.
