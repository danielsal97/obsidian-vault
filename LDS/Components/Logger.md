# Logger

**Phase:** 1 (complete) | **Status:** ✅ Implemented

**Files:**
- `utilities/logger/include/logger.hpp`
- `utilities/logger/src/logger.cpp`

---

## Responsibility

Centralized, thread-safe logging for the entire system. Every component uses the same Logger instance (via Singleton). Supports log levels to filter output at runtime.

---

## Interface

```cpp
class Logger {
public:
    enum LogLevel { DEBUG = 0, INFO = 1, WARN = 2, ERROR = 3 };

    void Write(const std::string& msg, LogLevel level = INFO);
    void SetLevel(LogLevel min_level);  // suppress below this level

private:
    LogLevel    m_level;
    std::mutex  m_mutex;   // thread-safe output
};

// Usage:
Singleton<Logger>::GetInstance()->Write("Plugin loaded", Logger::INFO);
```

---

## Test Status

`bin/test_logger` ✅ Passes — output format, level filtering, thread safety verified

---

## Related Notes
- [[Singleton]]
