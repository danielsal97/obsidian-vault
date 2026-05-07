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
