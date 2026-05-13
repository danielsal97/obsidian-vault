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

---

## Understanding Check

> [!question]- Why is `catch (std::exception e)` by value wrong, and what exactly is lost compared to `catch (const std::exception& e)`?
> Catching by value invokes the copy constructor of `std::exception`, not the derived type — the derived object is sliced. You lose any extra fields (like `error_code()` in a custom `StorageError`) and the dynamic type is gone. `what()` may still return the right message (if stored in the base), but any derived-specific data is inaccessible, and a re-throw of the sliced copy loses the original type entirely. Always catch exceptions by `const` reference.

> [!question]- What goes wrong if a `noexcept` function calls another function that does throw?
> If execution reaches a `throw` inside (or called from) a `noexcept` function, the runtime calls `std::terminate()` immediately — the program aborts with no stack unwinding, no destructors running for objects in scope above the throw point. This is intentional: `noexcept` is a guarantee to the optimizer and to callers (like `std::vector` reallocation) that the operation is atomic from an exception perspective. Accidentally marking a function `noexcept` that can indirectly throw is therefore very dangerous — it can cause abrupt termination that bypasses all RAII cleanup.

> [!question]- What is the difference between `throw;` and `throw e;` inside a catch block, and which should you always prefer when re-throwing?
> `throw;` re-throws the *current active exception object* — the same object, same derived type, same stack information. `throw e;` constructs a *new exception* by copy-constructing from `e`, which is typed as the catch parameter (e.g., `std::exception`) — the derived type is sliced off and the original propagation context is lost. Always use bare `throw;` when logging and re-throwing, so the outermost handler sees the full original exception.

> [!question]- In LDS, the `NBDDriverComm` constructor throws if `socketpair` fails. Why is throwing from a constructor better than returning a "half-initialized" object and checking a flag?
> A constructor that throws on failure ensures the object either fully exists or does not exist at all — there is no in-between state for callers to check or forget to check. A half-initialized object with an `is_valid()` flag requires every caller to guard every use with a check; missing one check means using an invalid object with undefined behavior. With the throwing constructor, the object is always valid after construction or it never reaches a caller. RAII destructors are also only called for fully-constructed objects, so there is no risk of the destructor trying to `close(-1)` an fd that was never opened.

> [!question]- What is the strong exception safety guarantee, why is copy-and-swap the standard way to achieve it in `operator=`, and what makes the swap step safe to use as a commit point?
> Strong guarantee: if the operation throws, the object's state is completely unchanged — it's all-or-nothing. Copy-and-swap works by making all fallible work on a *copy* of the data; only if that succeeds does a `noexcept` swap replace the live state. The swap is safe as a commit point because swapping two well-formed objects (just exchanging pointers/sizes) cannot fail — there is no allocation, no copy, nothing that can throw. If the copy step throws, the original is untouched; if it succeeds, the swap is unconditional.
```
