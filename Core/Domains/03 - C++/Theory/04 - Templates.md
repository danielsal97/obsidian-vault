# Templates

Templates are compile-time parameterization. The compiler generates a separate class or function for each type used. Zero runtime overhead — no vtable, no indirection.

---

## Function Templates

```cpp
template<typename T>
T max(T a, T b) {
    return a > b ? a : b;
}

max(3, 5);       // compiler generates max<int>
max(3.0, 5.0);   // compiler generates max<double>
max("a", "b");   // compiler generates max<const char*> — probably wrong
```

The compiler deduces `T` from the arguments. You can also specify explicitly:
```cpp
max<int>(3, 5);
```

---

## Class Templates

```cpp
template<typename T>
class Stack {
    std::vector<T> m_data;
public:
    void push(const T& val) { m_data.push_back(val); }
    T pop() { T v = m_data.back(); m_data.pop_back(); return v; }
    bool empty() const { return m_data.empty(); }
};

Stack<int> si;
Stack<std::string> ss;
// Two separate classes generated — Stack<int> and Stack<std::string>
```

---

## Template Specialization

Override the template for a specific type:

```cpp
template<typename T>
void print(T val) { std::cout << val; }

// Specialization for bool:
template<>
void print<bool>(bool val) { std::cout << (val ? "true" : "false"); }
```

**Partial specialization** (class templates only):
```cpp
template<typename T>
class Container { ... };

template<typename T>
class Container<T*> { ... };   // different implementation for pointer types
```

---

## Non-Type Template Parameters

Templates can be parameterized by values, not just types:

```cpp
template<typename T, size_t N>
class FixedArray {
    T m_data[N];
public:
    T& operator[](size_t i) { return m_data[i]; }
    size_t size() const { return N; }
};

FixedArray<int, 10> arr;   // stack-allocated, size known at compile time
```

---

## Variadic Templates

Accept any number of template arguments (C++11):

```cpp
template<typename... Args>
void log(Args&&... args) {
    (std::cout << ... << args);   // fold expression (C++17)
}

log("x=", x, " y=", y);
```

Used in `std::make_unique`, `std::make_shared`, `std::tuple`, `std::function`.

---

## SFINAE — Substitution Failure Is Not An Error

When template substitution fails, the compiler silently removes that overload from consideration rather than erroring. Enables compile-time conditional function selection:

```cpp
template<typename T>
typename std::enable_if<std::is_integral<T>::value, void>::type
print(T val) { std::cout << "int: " << val; }

template<typename T>
typename std::enable_if<std::is_floating_point<T>::value, void>::type
print(T val) { std::cout << "float: " << val; }

print(5);     // calls int version
print(3.14);  // calls float version
```

C++20 concepts provide a cleaner syntax for the same idea.

---

## Templates vs Virtual Functions

| | Templates (static polymorphism) | Virtual functions (runtime polymorphism) |
|---|---|---|
| Type resolution | Compile time | Runtime (vtable) |
| Overhead | Zero | One indirect call per dispatch |
| Code size | One copy per type | One implementation shared |
| Heterogeneous container | No | Yes (`vector<Base*>`) |
| Use when | Type known at compile time | Type chosen at runtime |

**LDS uses both:**
- `Dispatcher<Msg>` — template. Message type is fixed at compile time. Zero overhead. One `Dispatcher<DriverData>`, one `Dispatcher<std::string>`, etc.
- `ICommand` — virtual. Commands are created by Factory at runtime. Type not known at compile time.

---

## Common Template Pitfalls

**Template code lives in headers:**
```cpp
// Stack.hpp — entire implementation must be here
template<typename T>
void Stack<T>::push(const T& val) { ... }

// Stack.cpp — only explicit instantiations can go here
template class Stack<int>;   // explicit instantiation
```

**Long error messages:** template errors show the full instantiation chain. Read from the bottom up — the deepest error is usually the real problem.

**Implicit instantiation:** the compiler generates code for every `T` you use. 10 types = 10 copies of the class. Can bloat binary size.

---

## Type Traits

Compile-time queries about types (`<type_traits>`):

```cpp
std::is_integral<int>::value      // true
std::is_pointer<int*>::value      // true
std::is_same<int, int>::value     // true
std::is_same<int, long>::value    // false

// C++17 shorthand:
std::is_integral_v<int>           // true
```

Used with `if constexpr` to conditionally compile code:
```cpp
template<typename T>
void serialize(T val) {
    if constexpr (std::is_integral_v<T>) {
        write_int(val);
    } else {
        write_float(val);
    }
}
```

---

## Understanding Check

> [!question]- Why must template implementations live in header files rather than `.cpp` files, and what goes wrong if you put them in a `.cpp`?
> The compiler instantiates a template — generates concrete code — at the point where it is *used*, not where it is *defined*. That point is in the caller's translation unit. If the implementation is in a `.cpp`, it is not visible to the caller's translation unit at compile time: the compiler sees only the declaration and generates no code. The linker then finds no instantiation to link against and reports an undefined reference. The fix is either to put the full implementation in the header, or use explicit instantiation in the `.cpp` for each type you want to support.

> [!question]- What goes wrong if you instantiate a template with a type that doesn't satisfy the operations the template body uses?
> The compiler attempts to substitute the type and generates code for the template body. If the type lacks a required operator or method (e.g., `operator>` for a `max<T>` template), the compiler emits a cryptic error deep inside the template instantiation chain. The error message shows the full expansion, making it hard to read. C++20 Concepts address this by letting you declare preconditions (`requires`), so the error appears at the call site with a clear message about which constraint was violated.

> [!question]- In LDS, `Dispatcher<Msg>` is a template while `ICommand` uses virtual functions. What would go wrong if you tried to store different `Dispatcher<X>` specializations in a single container?
> `Dispatcher<DriverData>` and `Dispatcher<std::string>` are completely unrelated types — the template generates separate classes with no common base. A `std::vector<Dispatcher<?>>` has no valid element type without a common base or a type-erasing wrapper like `std::any` or a virtual interface. The design in LDS deliberately keeps each `Dispatcher` specialization separate because each subscriber type is known at registration time, so no runtime heterogeneous container is needed — templates give zero overhead here.

> [!question]- What is SFINAE and what goes wrong if the compiler encounters a hard error (not a substitution failure) inside a template?
> SFINAE (Substitution Failure Is Not An Error) means that if a template's type substitution produces an ill-formed expression *in the immediate context* (e.g., the return type), that candidate is silently dropped from overload resolution instead of causing an error. A hard error — a failure *inside the function body* after substitution succeeds — is not covered by SFINAE and does cause a compile error. This distinction matters when writing SFINAE-based dispatch: you must move the constraint into the function signature (return type, parameter type, or `enable_if` default template argument), not the body.

> [!question]- What goes wrong at runtime if a `max<const char*>` is instantiated and used to compare C-string literals?
> `operator>` on `const char*` compares pointer addresses, not string content. Two string literals with the same content may have different addresses depending on the compiler's string pooling. `max("abc", "xyz")` returns whichever pointer is numerically larger — this is neither the lexicographically greater string nor deterministic. The function compiles without error because `const char*` has `operator>`, making this a silent logic bug. The fix is a specialization for `const char*` using `strcmp`, or a constraint requiring a proper ordering type.
