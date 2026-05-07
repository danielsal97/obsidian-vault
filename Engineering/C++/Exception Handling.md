# Exception Handling

---

## Basics

```cpp
try {
    int result = divide(a, b);   // may throw
} catch (const std::invalid_argument& e) {
    std::cerr << "Invalid: " << e.what() << "\n";
} catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << "\n";
} catch (...) {
    std::cerr << "Unknown error\n";
}
```

`throw` — throw any type (usually derived from `std::exception`).  
`catch` — handlers checked top to bottom, first match wins.  
`catch (...)` — catches anything, including non-exception types.

---

## Standard Exception Hierarchy

```
std::exception
├── std::logic_error       — bugs in the program (should not happen at runtime)
│   ├── std::invalid_argument
│   ├── std::out_of_range
│   ├── std::length_error
│   └── std::domain_error
├── std::runtime_error     — errors that can only be detected at runtime
│   ├── std::overflow_error
│   ├── std::underflow_error
│   └── std::range_error
├── std::bad_alloc         — new/malloc failed
├── std::bad_cast          — dynamic_cast failed on reference
└── std::bad_optional_access
```

```cpp
throw std::invalid_argument("offset cannot be negative");
throw std::runtime_error("socket connection failed");
throw std::out_of_range("index " + std::to_string(i) + " out of range");
```

---

## Custom Exceptions

```cpp
class StorageError : public std::runtime_error {
    int m_error_code;
public:
    explicit StorageError(const std::string& msg, int code)
        : std::runtime_error(msg), m_error_code(code) {}
    
    int error_code() const { return m_error_code; }
};

throw StorageError("write failed at offset " + std::to_string(offset), EIO);

try { ... }
catch (const StorageError& e) {
    log(e.what(), e.error_code());
}
```

---

## Stack Unwinding

When an exception is thrown, C++ destroys all local objects in reverse construction order as it unwinds the call stack — this is guaranteed, even if no `catch` exists.

```cpp
void f() {
    FileGuard guard("file.txt");    // constructor opens file
    throw std::runtime_error("oops");
    // guard's destructor runs here — file is closed automatically
}
```

This is why RAII + exceptions work together perfectly. No try/finally needed (Java/Python) — destructors are the cleanup.

---

## noexcept

Declares a function will not throw. The compiler can optimize call sites.

```cpp
int safe_get(int i) noexcept { return arr[i]; }

// Move operations should be noexcept:
Buffer(Buffer&&) noexcept;
Buffer& operator=(Buffer&&) noexcept;
```

If a `noexcept` function does throw, `std::terminate()` is called — program aborts. Do not use `noexcept` unless you're certain.

`std::vector` only uses move operations during reallocation if they are `noexcept`. Otherwise it falls back to copying for exception safety.

---

## Exception Safety Levels

| Level | Guarantee |
|---|---|
| **No-throw** | Function never throws. Marked `noexcept`. |
| **Strong** | If exception thrown, state is unchanged (commit-or-rollback). |
| **Basic** | If exception thrown, object is in a valid but unspecified state. No leaks. |
| **None** | No guarantees — resource leaks possible. |

**Strong guarantee pattern — copy-and-swap:**
```cpp
void Container::add(const Item& item) {
    auto copy = m_data;          // copy current state
    copy.push_back(item);        // modify the copy — may throw
    std::swap(m_data, copy);     // swap is noexcept — commit
}
// If push_back throws, m_data is unchanged — strong guarantee
```

---

## Re-throwing

```cpp
try {
    risky_operation();
} catch (const std::exception& e) {
    log(e.what());
    throw;        // re-throw same exception — preserves type and stack trace
    // NOT: throw e;  — that creates a copy, loses derived type
}
```

---

## Exception vs Error Code — When to Use Each

| Situation | Use |
|---|---|
| Programmer error (wrong argument, invariant violation) | Exception (`logic_error`) |
| Runtime failure (network down, file not found) | Exception OR error code |
| Performance-critical path, frequent failures | Error code / `std::optional` |
| C API boundary | Error code (`errno`) |
| Destructors | Never throw — mark `noexcept` |

**LDS context:** constructors throw (e.g., `NBDDriverComm` constructor throws if `socketpair` fails — better than returning a half-initialized object). Destructors never throw.

---

## Common Mistakes

**Throwing in a destructor:**
```cpp
~MyClass() {
    close(m_fd);
    if (error) throw std::runtime_error("close failed");  // NEVER DO THIS
    // If already unwinding from another exception → std::terminate()
}
```

**Catching by value (slices):**
```cpp
catch (std::exception e) { ... }   // slices — loses derived type
catch (const std::exception& e) { ... }  // correct — reference
```

**Empty catch block:**
```cpp
catch (...) {}   // silently swallows all exceptions — very hard to debug
```

**Overusing exceptions for flow control:**
```cpp
// Bad — exceptions are expensive:
try { return map.at(key); }
catch (std::out_of_range&) { return default_value; }

// Better:
auto it = map.find(key);
return it != map.end() ? it->second : default_value;
```
