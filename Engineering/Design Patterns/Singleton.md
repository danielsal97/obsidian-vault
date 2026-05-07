# Singleton Pattern

Ensures only one instance of a class exists, and provides a global access point to it.

---

## Basic Implementation (C++11 — thread-safe)

```cpp
class Logger {
public:
    static Logger& instance() {
        static Logger inst;   // constructed once, on first call; thread-safe in C++11
        return inst;
    }

    void log(const std::string& msg) {
        std::cout << msg << "\n";
    }

    // Delete copy/move so no second instance can be made:
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;

private:
    Logger() {}    // private constructor
};

// Usage:
Logger::instance().log("started");
```

The `static` local variable is initialized the first time `instance()` is called. C++11 guarantees this initialization is thread-safe (magic statics).

---

## Why Magic Statics Are Thread-Safe (C++11+)

The standard requires that if two threads simultaneously reach the initialization of a `static` local variable, one waits while the other initializes it. The compiler emits a lock around the first-time initialization.

---

## Thread Safety for the Object Itself

The singleton itself is NOT automatically thread-safe — only its construction is. If multiple threads call `log()` simultaneously, you need a mutex inside:

```cpp
void log(const std::string& msg) {
    std::lock_guard<std::mutex> lk(m_mutex);
    std::cout << msg << "\n";
}
private:
    std::mutex m_mutex;
```

---

## Lazy vs Eager Initialization

**Lazy** (above — initialized on first use): good if initialization is expensive and may not be needed.

**Eager** (global variable — initialized at program start):
```cpp
// In .cpp file:
Logger g_logger;   // initialized before main()
```

Risk of "static initialization order fiasco" — the order global objects across different `.cpp` files initialize is undefined.

The local-static pattern (above) avoids this because initialization is triggered by the first call, which happens after main() starts.

---

## Singleton vs Global Variable

A global variable is essentially an unprotected singleton. The singleton pattern adds:
- Lazy initialization
- Thread-safe first-time construction
- Prevention of additional copies

---

## When to Use (and Not)

**Use when:** there's a true single resource — a configuration object, a logger, a hardware interface.

**Avoid when:**
- You're using it just to avoid passing objects around (that's global state abuse)
- You need testability — singletons make unit testing hard (you can't inject a mock)
- You want multiple instances in tests

**Better alternative:** dependency injection — pass the shared object as a constructor parameter. Classes don't need to know it's a singleton.

---

## LDS Context

`LocalStorage` could have been a singleton (there's only one file on disk), but LDS injects it:
```cpp
class InputMediator {
    IStorage* m_storage;   // injected — testable
public:
    InputMediator(IStorage* s) : m_storage(s) {}
};
```

This allows unit tests to pass a mock `IStorage` instead of the real file-backed one.

---

## Related Notes

- [[Factory]] — creates objects without the caller knowing the concrete type
- [[../C++/RAII]] — singleton destructor should clean up resources
- [[../C++/Smart Pointers]] — `shared_ptr` for reference-counted shared objects (not singleton, but related)
