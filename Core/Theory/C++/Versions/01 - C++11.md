# C++11 — The Big One

C++11 was the most transformative update to C++. It effectively created "modern C++". Almost everything written before it is considered legacy style.

---

## auto — Type Deduction

```cpp
auto x = 5;                          // int
auto s = std::string("hello");       // std::string
auto it = v.begin();                 // std::vector<int>::iterator — saves typing
auto fn = [](int x){ return x*2; }; // lambda

// auto& avoids copies in range-based for:
for (auto& item : container) { ... }
```

`auto` does not make C++ dynamically typed — the type is deduced at compile time and is fixed.

---

## Range-Based For Loop

```cpp
std::vector<int> v = {1, 2, 3};

for (int x : v) { ... }          // copy each element
for (const int& x : v) { ... }   // read-only reference — no copy
for (int& x : v) { x *= 2; }    // modify in place
for (auto& x : v) { ... }       // let compiler deduce type
```

Works on any type that has `begin()` and `end()` — arrays, vectors, maps, strings, custom containers.

---

## Lambda Expressions

Anonymous functions defined inline.

```cpp
auto square = [](int x) { return x * x; };
square(5);   // 25

// With capture:
int factor = 3;
auto multiply = [factor](int x) { return x * factor; };  // capture by value
auto multiply = [&factor](int x) { return x * factor; }; // capture by reference
auto multiply = [=](int x) { return x * factor; };       // capture all by value
auto multiply = [&](int x) { return x * factor; };       // capture all by reference

// With return type:
auto divide = [](double a, double b) -> double { return a / b; };

// Immediately invoked:
int result = [](int x){ return x * 2; }(5);   // = 10
```

Lambdas are syntactic sugar for anonymous functor objects. They replace `std::bind` and explicit functor classes in almost all cases.

---

## Move Semantics and Rvalue References

See [[../Move Semantics]] for full detail.

```cpp
std::vector<int> a(1000);
std::vector<int> b = std::move(a);   // transfers buffer — O(1), no copy
// a is now empty
```

`&&` — rvalue reference. Binds only to temporaries or `std::move`'d objects.

---

## Smart Pointers

See [[../Smart Pointers]] for full detail.

```cpp
auto p = std::make_unique<int>(42);   // sole ownership, auto-delete
auto q = std::make_shared<int>(42);   // shared ownership, ref-counted
std::weak_ptr<int> w = q;             // non-owning observer
```

---

## nullptr

Type-safe null pointer literal. Replaces `NULL` and `0`.

```cpp
int* p = nullptr;        // clearly a pointer
void f(int);
void f(int*);
f(nullptr);   // calls f(int*) — unambiguous
f(NULL);      // might call f(int) — ambiguous, depends on NULL's definition
```

---

## constexpr

Evaluate at compile time. Results can be used in array sizes, template parameters, switch cases.

```cpp
constexpr int SIZE = 1024;
constexpr int square(int x) { return x * x; }

int arr[square(4)];           // arr[16] — size known at compile time
static_assert(square(5) == 25, "math is broken");
```

---

## Initializer Lists and Uniform Initialization

```cpp
// Before C++11:
int arr[] = {1, 2, 3};                   // only for arrays
std::vector<int> v;  v.push_back(1); ... // tedious

// C++11 — uniform initialization:
std::vector<int> v = {1, 2, 3};
std::map<std::string, int> m = {{"a", 1}, {"b", 2}};
struct Point { int x, y; };
Point p = {3, 4};

// {} also prevents narrowing:
int x = 3.14;    // compiles — truncates to 3
int x{3.14};     // ERROR — narrowing conversion not allowed
```

---

## enum class — Scoped Enums

```cpp
// Old enum — pollutes namespace, implicit int conversion:
enum Color { RED, GREEN, BLUE };
int x = RED;   // implicit conversion — usually wrong

// C++11 enum class — scoped, no implicit conversion:
enum class Color { Red, Green, Blue };
Color c = Color::Red;
int x = c;              // ERROR — no implicit conversion
int x = static_cast<int>(c);  // explicit conversion only
```

---

## override and final

```cpp
struct Base {
    virtual void f(int);
};

struct Derived : Base {
    void f(int) override;   // compiler verifies Base has f(int) — catches typos
    void f(float) override; // ERROR — no such virtual in Base
};
```

---

## = delete and = default

```cpp
class NonCopyable {
    NonCopyable(const NonCopyable&) = delete;   // compile error if copied
    NonCopyable& operator=(const NonCopyable&) = delete;
};

class MyClass {
    MyClass() = default;                        // explicitly use compiler-generated
    ~MyClass() = default;
};
```

---

## Threading Library

```cpp
#include <thread>
#include <mutex>
#include <condition_variable>
#include <atomic>

std::thread t([]{ doWork(); });
t.join();

std::mutex m;
std::lock_guard<std::mutex> lock(m);

std::atomic<bool> flag{false};
flag.store(true);
bool v = flag.load();
```

First time C++ had a portable threading model in the standard library. Before C++11, you had to use pthreads directly.

---

## std::function and std::bind

```cpp
#include <functional>

std::function<int(int, int)> fn = [](int a, int b){ return a + b; };
fn(3, 4);   // 7

// std::bind — partial application:
auto add5 = std::bind(add, std::placeholders::_1, 5);
add5(3);    // 8
// Note: lambdas are almost always cleaner than std::bind
```

---

## static_assert

Compile-time assertion — error at build time, not runtime:

```cpp
static_assert(sizeof(int) == 4, "int must be 4 bytes");
static_assert(std::is_trivially_copyable<MyStruct>::value, "must be POD");
```

---

## Delegating Constructors

```cpp
class Point {
    int x, y;
public:
    Point() : Point(0, 0) {}          // delegates to Point(int, int)
    Point(int x, int y) : x(x), y(y) {}
};
```

---

## Type Traits

Compile-time type queries:

```cpp
#include <type_traits>

std::is_integral<int>::value      // true
std::is_pointer<int*>::value      // true
std::is_same<int, long>::value    // false
std::remove_pointer<int*>::type   // int
std::add_const<int>::type         // const int
```

---

## Understanding Check

> [!question]- `auto x = 5;` — does this make C++ dynamically typed? What actually happens?
> No. `auto` is compile-time type deduction — the compiler infers `int` from the literal `5` and `x` is a fixed `int` for its entire lifetime. There is no runtime type tracking. It's purely a convenience to avoid writing the type when it's obvious from context. `auto` is resolved before the program runs.

> [!question]- You store a lambda with `[&]` capture in an `std::function` and push it into the LDS ThreadPool. What can go wrong?
> Dangling reference. `[&]` captures all local variables by reference — if the lambda outlives the function where it was created (which it does, since the ThreadPool runs it asynchronously), all the captured references dangle. The stack frame is gone. Fix: capture by value `[=]` or explicitly capture only what's needed by value `[x, y]`. For large objects, move into the lambda `[p = std::move(ptr)]` (C++14).

> [!question]- `f(nullptr)` vs `f(NULL)` vs `f(0)` — when does the difference matter?
> When there are overloads `f(int)` and `f(int*)`: `f(nullptr)` unambiguously calls `f(int*)`. `f(NULL)` and `f(0)` may call `f(int)` because NULL is often defined as `0` (an integer). This is the entire reason `nullptr` exists — to give the null pointer a distinct type (`std::nullptr_t`) that only converts to pointer types.

> [!question]- What bug does `override` catch that would otherwise compile silently?
> Virtual function signature mismatch. If you write `void f(float)` intending to override `virtual void f(int)`, the compiler silently creates a new non-virtual function — polymorphism is broken and the base version is called. With `override`, the compiler verifies that the function actually overrides a virtual in the base class. The bug becomes a compile error instead of a runtime mystery.

> [!question]- Before C++11, C++ had no standard threading model. What did that mean in practice for Linux programs like LDS?
> Every platform had its own API: Linux used pthreads (`pthread_create`, `pthread_mutex_t`), Windows used `CreateThread`. Code that used threads was not portable. C++11 standardised `std::thread`, `std::mutex`, `std::condition_variable`, and `std::atomic` — the same code compiles and runs correctly on any platform. LDS uses `std::thread` and `std::mutex` instead of raw pthreads for this reason.
