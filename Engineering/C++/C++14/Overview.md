# C++14 — Polishing C++11

C++14 is a small refinement of C++11. No major new concepts — mostly fixing rough edges and adding convenience.

---

## Generic Lambdas — auto Parameters

```cpp
// C++11 — must specify types:
auto add = [](int a, int b) { return a + b; };

// C++14 — auto parameters, works for any type:
auto add = [](auto a, auto b) { return a + b; };
add(1, 2);       // int
add(1.5, 2.5);   // double
add(std::string("a"), std::string("b"));  // string
```

Essentially a templated lambda. The compiler generates a separate function for each type combination.

---

## Lambda Capture with Initializers

```cpp
// C++11 — capture an existing variable:
int x = 5;
auto f = [x]{ return x; };

// C++14 — create a new variable in the capture:
auto f = [y = x * 2]{ return y; };   // y = 10, independent of x

// Move capture (impossible in C++11):
auto ptr = std::make_unique<int>(42);
auto f = [p = std::move(ptr)]{ return *p; };
// ptr is now null, f owns the unique_ptr
```

---

## Return Type Deduction for Functions

```cpp
// C++11 — trailing return type needed for complex cases:
auto f(int x) -> int { return x * 2; }

// C++14 — auto return type deduced from return statement:
auto f(int x) { return x * 2; }   // returns int

// Multiple returns must all have the same deduced type:
auto g(bool b) {
    if (b) return 1;     // int
    return 2;            // int — OK
    // return 2.0;       // ERROR — different types
}
```

---

## std::make_unique

The most practically important C++14 addition:

```cpp
// C++11 — had to write:
std::unique_ptr<int> p(new int(42));

// C++14:
auto p = std::make_unique<int>(42);         // single object
auto arr = std::make_unique<int[]>(100);    // array
```

`make_unique` is preferred over `new` for exception safety and clarity. (Note: `make_shared` was already in C++11.)

---

## Binary Literals and Digit Separators

```cpp
// Binary literals:
int flags = 0b10110001;   // binary — much clearer for bitmasks

// Digit separators ('):
int million = 1'000'000;         // easier to read
double pi   = 3.141'592'653;
int mask    = 0b1111'0000'1111'0000;
```

---

## Relaxed constexpr

C++11 constexpr functions could only contain a single return statement. C++14 allows loops and local variables:

```cpp
// C++11 — only single expression:
constexpr int square(int x) { return x * x; }

// C++14 — can have loops, local vars, if:
constexpr int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) result *= i;
    return result;
}

constexpr int f120 = factorial(5);   // 120, computed at compile time
```

---

## std::exchange

```cpp
#include <utility>

// Assigns new_value to obj, returns the old value:
int old = std::exchange(x, new_value);

// Useful in move operations:
Buffer(Buffer&& other) noexcept
    : m_data(std::exchange(other.m_data, nullptr))
    , m_size(std::exchange(other.m_size, 0)) {}
```

Cleaner than the manual `temp = old; old = new; return temp` pattern.

---

## [[deprecated]] Attribute

```cpp
[[deprecated("use NewFunction instead")]]
void OldFunction() { ... }

OldFunction();   // compiler warning: 'OldFunction' is deprecated
```

---

## std::integer_sequence (compile-time index sequences)

```cpp
// Used for unpacking tuples and parameter packs:
template<std::size_t... I>
void print_tuple(const auto& t, std::index_sequence<I...>) {
    ((std::cout << std::get<I>(t) << " "), ...);
}

auto t = std::make_tuple(1, "hello", 3.14);
print_tuple(t, std::make_index_sequence<3>{});
```

---

## Summary — What to Actually Use from C++14

| Feature | Usage |
|---|---|
| `std::make_unique` | Always — replace `new` for unique_ptr |
| Generic lambdas | When the lambda needs to work on multiple types |
| Lambda move capture | When moving a unique_ptr into a lambda |
| `std::exchange` | In move constructors |
| Digit separators | For readability in large literals and bitmasks |
| Return type deduction | Short functions where type is obvious |
