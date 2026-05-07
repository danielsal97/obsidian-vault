---
name: C++ Templates — Generic Programming
type: cpp
---

# C++ Templates — Generic Programming

**[cppreference →](https://en.cppreference.com/w/cpp/language/templates)** | **[Wikipedia →](https://en.wikipedia.org/wiki/Generic_programming)**

Compile-time parameterization of classes and functions by type. The compiler generates a separate concrete implementation for each type combination used.

```cpp
template <typename T>
T max(T a, T b) { return a > b ? a : b; }

max(3, 5);          // compiler generates max<int>
max(3.0, 5.0);      // compiler generates max<double>
```

## Why LDS Uses Templates Heavily

LDS's core patterns — Factory, Dispatcher, ICommand, Singleton — all need to work with arbitrary types. Templates let one pattern implementation serve all of them with full type safety at compile time, at zero runtime cost.

## Template Usage in LDS

### Dispatcher (Observer)
```cpp
Dispatcher<FileEvent> file_events;
Dispatcher<HealthEvent> health_events;
// Completely separate instances, type-safe
// Can't accidentally send a HealthEvent to file_events
```

### Factory
```cpp
Factory<ICommand, std::string, DriverData> cmd_factory;
Factory<IPlugin, std::string, std::nullptr_t> plugin_factory;
// Separate registries per return type
```

### Singleton
```cpp
Singleton<Logger>::GetInstance();
Singleton<CommandFactory>::GetInstance();
// One instance per type, guaranteed
```

### ICommand
```cpp
ICommand<QueryArgs, QueryResult>  // typed input + output
ICommand<WriteArgs, void>         // typed input, no output
```

## vs. Virtual Functions (The Alternative)

```cpp
// Virtual function approach (runtime dispatch)
class IHandler {
    virtual void handle(void* data) = 0;  // type erased — unsafe cast needed
};

// Template approach (compile-time dispatch)
template <typename T>
class CallBack : public ICallBack<T> {
    void update(const T& msg) override;  // type-safe, no casting
};
```

Templates check types at compile time. Wrong types are caught before the program runs, not during.

→ Full reasoning: [[Why Templates not Virtual Functions]]

## Related
- [[Observer]] — Dispatcher<T> and CallBack<T, Sub>
- [[Factory]] — Factory<Base, Key, Args>
- [[Singleton]] — Singleton<T>
- [[Command]] — ICommand<Args, Return>
