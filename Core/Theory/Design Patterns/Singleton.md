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

---

## Understanding Check

> [!question]- Why is the local-static Singleton pattern (C++11) thread-safe for construction but NOT thread-safe for the object's methods?
> The C++11 standard specifically mandates that static local variable initialization is performed exactly once, with concurrent threads blocked until it completes — the compiler emits an internal lock around the first-time initialization. This guarantees only one Logger object is ever constructed, even if multiple threads call instance() simultaneously. However, the standard says nothing about thread safety of the object's own operations. Once the singleton exists, Logger::log() accesses std::cout and potentially shared internal state; two threads calling log() concurrently can interleave their output or corrupt state without a mutex guarding the method body.

> [!question]- What goes wrong if you rely on a Singleton's destructor to flush a log file, and the program uses other global objects whose destructors also run at exit?
> Global and static-local objects are destroyed in reverse order of construction after main() returns. If the Logger singleton is destroyed before another global object that still wants to log in its destructor, the Logger's underlying file or buffer is gone — the log call hits a destroyed object, causing undefined behavior or a silent drop. This is a manifestation of the static destruction order fiasco. The safe fix is to either ensure the logger outlives all users (by controlling initialization order), or use an explicit shutdown method called from main() before any destructors fire.

> [!question]- Why does LDS choose dependency injection over a Singleton for IStorage, and what specific test scenario becomes possible because of this choice?
> A Singleton makes the concrete class globally reachable but impossible to swap out — unit tests would write to the real file on disk, making tests slow, order-dependent, and destructive. Dependency injection passes IStorage* as a constructor argument to InputMediator. A test can construct InputMediator with a MockStorage that records calls, returns canned data, and simulates errors without touching the filesystem. This means you can test LDS's read/write dispatch logic, error handling, and retry paths entirely in memory, in milliseconds, with no setup or teardown of real files.

> [!question]- What is the "static initialization order fiasco" and why does the local-static pattern not suffer from it even though an eager global-variable singleton does?
> The fiasco occurs because the order in which global objects across different .cpp files are initialized before main() is unspecified by the C++ standard. If Singleton A's constructor uses Singleton B, B might not be initialized yet, reading garbage. The local-static pattern defers initialization to the first call to instance(), which happens inside main() — after all global constructors have completed. There is no ordering dependency because the trigger is explicit (the function call) rather than implicit (translation unit load order). The eager global-variable singleton is susceptible because its constructor runs at program startup in an uncontrolled order relative to other globals.

> [!question]- If two threads call Logger::instance() simultaneously for the very first time on a C++11 compiler, walk through exactly what happens to ensure only one Logger is constructed.
> The compiler emits a flag variable alongside the static Logger inst. Thread A enters instance() first and checks the flag (not initialized). Before it completes construction, Thread B also enters instance() and checks the same flag. The C++11 runtime uses an internal lock (often a compare-and-swap on the flag) to ensure Thread B blocks at this point while Thread A runs the Logger constructor and sets the flag to "initialized." Thread B then wakes, checks the flag (now initialized), and returns the already-constructed inst without calling the constructor again. Both threads receive references to the same single Logger object.
