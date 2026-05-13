# Singleton Pattern — The Machine

## The Model
A building with exactly one room of its type — and the blueprint enforces this. The `getInstance()` function is the door: the first time you open it, the room is built. Every subsequent time, the same room is returned. The blueprint physically prevents a second room from being constructed.

## How It Moves

```
First call:
  Logger::getInstance()
    ↓ static local variable not yet initialized
    ↓ Logger() constructor runs — opens log file, sets up format
    ↓ returns reference to the single Logger object

All subsequent calls:
  Logger::getInstance()
    ↓ static local variable already initialized
    ↓ returns same reference immediately (no construction)

Destructor:
  When the process exits → static local destroyed → log file flushed and closed
```

**Thread safety in C++11:** static local variable initialization is guaranteed thread-safe by the C++11 standard. The first thread to reach the initialization runs it; other threads block until initialization completes.

## The Blueprint

```cpp
class Logger {
public:
    static Logger& getInstance() {
        static Logger instance;   // C++11: thread-safe, constructed once
        return instance;
    }
    
    void log(const std::string& msg) {
        std::lock_guard<std::mutex> lock(m_mtx);
        m_file << msg << "\n";
        m_file.flush();
    }
    
private:
    Logger() : m_file("/var/log/lds.log", std::ios::app) {}
    ~Logger() { m_file.close(); }
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;
    
    std::ofstream m_file;
    std::mutex m_mtx;
};

// Usage anywhere:
Logger::getInstance().log("NBD request received");
```

**Why Singleton is often a smell:**
- Hidden global state — callers don't know they depend on it (no parameter)
- Hard to test — can't inject a mock Logger in tests
- Initialization order problems — if two singletons depend on each other

**When it's legitimate:**
- Logger: genuinely one per process, not worth injecting everywhere
- Configuration: read-once at startup, read-many at runtime
- Hardware interface: one physical device, one handle

## Where It Breaks

- **Destruction order**: if singleton A's destructor uses singleton B, and B is destroyed first → crash. The order of static destruction is reverse of construction order — fragile.
- **Multiple translation units**: in some scenarios, the linker creates multiple copies of a singleton if the `getInstance` is in a header and linked into multiple shared libraries.
- **Testing**: you cannot easily reset a Singleton between tests. Use dependency injection for testable components.

## In LDS

`design_patterns/singleton/include/singelton.hpp`

LDS's `Logger` is a Singleton. Every component calls `Logger::getInstance().log(...)` without needing a Logger parameter threaded through. The Logger holds an `std::mutex` to serialize concurrent log writes from multiple ThreadPool workers. The Singleton ensures there is exactly one mutex protecting one file handle — if each component created its own Logger, log entries would interleave and the file might be opened multiple times.

## Validate

1. Two ThreadPool workers call `Logger::getInstance().log(msg)` simultaneously. Does the logger need a mutex? Why isn't the Singleton guarantee (one instance) sufficient?
2. You want to test `InputMediator` with a mock Logger. The Logger is a Singleton. What is the problem, and how would you redesign to fix it?
3. `Logger::getInstance()` is called from a static initializer in another translation unit. The Logger's static local hasn't been initialized yet. What happens? (hint: static initialization order fiasco)

## Connections

**Theory:** [[Core/Theory/Design Patterns/03 - Singleton]]  
**Mental Models:** [[Threads and pthreads — The Machine]], [[Smart Pointers — The Machine]], [[Memory Ordering — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Singleton]], [[LDS/Infrastructure/Singleton Memory Model]]  
**Glossary:** [[pthreads]]
