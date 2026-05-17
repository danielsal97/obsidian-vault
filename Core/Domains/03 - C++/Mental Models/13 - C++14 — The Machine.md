# C++14 — The Gap Filler

## The Model
C++14 is not a revolution — it's an errata and polish release for C++11. Three things that were missing or awkward in C++11 are fixed. Worth knowing because interviewers sometimes ask "why wasn't make_unique in C++11?"

## The Three Fixes

**`std::make_unique` — exception-safe heap allocation**

C++11 had `make_shared` but not `make_unique`. The reason: it was accidentally omitted. C++14 adds it.

Why `make_unique` not `new unique_ptr(new T())`:
```cpp
// C++11:
func(std::unique_ptr<T>(new T()), std::unique_ptr<U>(new U()));
// Execution order of arguments is unspecified:
// Could be: new T() → new U() → construct unique_ptr<T> → construct unique_ptr<U>
// If new U() throws before unique_ptr<T> is constructed → T leaks

// C++14:
func(std::make_unique<T>(), std::make_unique<U>());
// Each make_unique is a single indivisible operation — no leak possible
```

**Generic lambdas — `auto` parameters**
```cpp
// C++11: lambda parameters must have explicit types
auto add = [](int a, int b) { return a + b; };

// C++14: auto parameters — lambda becomes a template
auto add = [](auto a, auto b) { return a + b; };
add(1, 2);       // works
add(1.0, 2.0);   // also works
```

**Return type deduction — no `-> type` needed**
```cpp
// C++11:
auto getDriver() -> std::shared_ptr<IDriverComm> { return m_driver; }

// C++14:
auto getDriver() { return m_driver; }   // compiler deduces return type
```

## In LDS

`utilities/threading/thread_pool/src/thread_pool.cpp`

Any `std::make_unique<ThreadPool>(...)` in LDS requires C++14. The LDS `CMakeLists.txt` (or Makefile) sets `-std=c++20`, which includes all C++11, C++14, C++17, and C++20 features. The fact that LDS compiles at all requires at least C++11; `make_unique` requires C++14; C++20 features (`std::jthread`, `concepts`) require C++20.

## Validate

1. C++11 has `make_shared` but not `make_unique`. What was the actual reason? (hint: it's embarrassing)
2. Generic lambda `[](auto x) { return x * 2; }` — is this a function template? How does the compiler implement it?
3. LDS uses `-std=c++20`. Does this mean it cannot use C++11 features? What does the standard version flag actually control?

## Connections

**Theory:** [[02 - C++14]]  
**Mental Models:** [[Smart Pointers — The Machine]], [[RAII — The Machine]], [[Templates — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Utilities Framework]] — make_unique for ThreadPool construction; [[LDS/DevOps/Build System]] — -std=c++20 enables all C++11–C++20 features
