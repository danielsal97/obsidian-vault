# Templates — The Machine

## The Model
A code stamping machine. You design a stamp (the template). The compiler uses the stamp to generate actual code for each type you use. `vector<int>` and `vector<string>` are two separate classes — the compiler stamped them both from one template. The stamp must live in the header because the compiler needs it at the point of stamping.

## How It Moves

```
Template definition (in header):
  template<typename T>
  T max(T a, T b) { return a > b ? a : b; }

Usage in .cpp:
  max(3, 5)           → compiler stamps out: int max(int a, int b) { return a > b ? a : b; }
  max(3.0, 5.0)       → compiler stamps out: double max(double a, double b) { ... }
  max("a", "b")       → compiler stamps out: const char* max(...) — compiles but wrong (pointer comparison)

Each stamp is a separate compiled function. Two instantiations = two functions in the binary.
```

**WHY templates must be in headers:** The compiler needs the full template definition to generate the stamped code. If the template is in a `.cpp` and you use it in another `.cpp`, the compiler has already finished the template's `.cpp` — it can't go back to generate a new stamp. Headers are included at the point of use — definition always available.

## The Blueprint

**Function template:**
```cpp
template<typename T>
void swap(T& a, T& b) { T tmp = std::move(a); a = std::move(b); b = std::move(tmp); }
```

**Class template:**
```cpp
template<typename T>
class Stack {
    std::vector<T> m_data;
public:
    void push(T val) { m_data.push_back(std::move(val)); }
    T pop() { T v = std::move(m_data.back()); m_data.pop_back(); return v; }
};
```

**SFINAE (Substitution Failure Is Not An Error):** the compiler tries to stamp a template; if the substitution fails (e.g., type T doesn't have `operator<`), it silently skips that overload instead of erroring. Used to conditionally enable overloads.

**C++20 Concepts:** readable filter on which stamps are valid:
```cpp
template<typename T>
requires std::totally_ordered<T>
T max(T a, T b) { return a > b ? a : b; }
max("a", 1);   // clear error: types don't satisfy totally_ordered
```

## Where It Breaks

- **Missing template definition in header**: `undefined reference` at link time — the stamp was never made
- **Code bloat**: each instantiation is a separate stamped function — 10 different types = 10 copies of the function in the binary
- **SFINAE error messages**: pre-C++20, template errors produce pages of instantiation noise. Use Concepts for readable errors.

## In LDS

`design_patterns/observer/include/CallBack.hpp`

`CallBack<T>` is a template that wraps a callable into the `ICallBack<T>` interface. One template, stamped for each event type: `CallBack<Request>`, `CallBack<int>`, etc. The stamp is generated when the template is used — the compiler creates a concrete class from the template definition in the header.

`utilities/thread_safe_data_structures/priority_queue/include/wpq.hpp` — `WorkPriorityQueue` is a template over the task type, allowing it to hold any callable without runtime overhead of virtual dispatch.

## Validate

1. You define `template<typename T> T add(T a, T b)` in a `.cpp` file and instantiate it in a different `.cpp`. What error appears and at which build station?
2. `CallBack<Request>` and `CallBack<Response>` are two instantiations of the same template. Do they share any code in the final binary?
3. A template function calls `a.size()`. You instantiate it with `int`. What happens and why doesn't it produce an error at template definition time?

## Connections

**Theory:** [[Core/Theory/C++/Templates]]  
**Mental Models:** [[Observer Pattern — The Machine]], [[Factory Pattern — The Machine]], [[Strategy Pattern — The Machine]], [[STL Containers — The Machine]]  
**Tradeoffs:** [[LDS/Decisions/Why Templates not Virtual Functions]]  
**LDS Implementation:** [[LDS/Infrastructure/Observer Pattern Internals]] — CallBack<T>; [[LDS/Infrastructure/Utilities Framework]] — WPQ template  
**Glossary:** [[Templates]]
