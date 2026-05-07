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
- [[../C++/Virtual Functions]] — strategy uses virtual dispatch
- [[../C++/Templates]] — policy-based design is compile-time strategy
- [[../C++/Smart Pointers]] — own strategy with unique_ptr
