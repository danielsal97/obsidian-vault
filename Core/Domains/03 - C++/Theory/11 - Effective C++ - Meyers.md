# Effective C++ — Scott Meyers

Key guidelines from *Effective C++* (3rd ed.), *Effective Modern C++*, and *More Effective C++*. Each item states the rule, why it exists, and when it applies.

---

## Prefer const / enum / inline to #define

```cpp
// Bad — #define has no type, no scope, no debugger visibility:
#define MAX 100
#define SQUARE(x) x*x   // SQUARE(1+1) → 1+1*1+1 = 3, not 4

// Good:
constexpr int MAX = 100;
inline int square(int x) { return x * x; }
```

`#define` is replaced before the compiler sees it — no type checking, no scoping, doesn't appear in the symbol table.

See [[01 - Preprocessor]] — macros are a preprocessor-only tool.

---

## Use const Whenever Possible

```cpp
const int* p      // pointer to const int — can't modify *p
int* const p      // const pointer to int — can't change p itself
const int* const p// both

// Member function const:
class Buffer {
    size_t size() const { return m_size; }  // promises not to modify this
};
```

`const` on member functions enables calling them on const objects and expresses intent. Const correctness prevents bugs at compile time.

---

## Make Sure Objects Are Initialized Before Use

```cpp
// Always use the member initializer list — not assignment in body:
class Foo {
    int m_x;
    std::string m_name;
public:
    Foo(int x, std::string name)
        : m_x(x)                // initialization — calls constructor once
        , m_name(std::move(name))
    {}
    // NOT: Foo(...) { m_x = x; m_name = name; }  — assignment, not init
};
```

Non-POD members assigned in body are default-constructed first, then assigned — wastes a construction. Order in the initializer list should match order of declaration.

**Static initialization order fiasco:** the order that global objects in different `.cpp` files initialize is undefined. Fix: use the local-static singleton pattern instead of globals.

See [[Singleton]] — local static is the safe pattern.

---

## Know What Functions C++ Silently Writes

If you don't declare them, the compiler may generate:
- Default constructor
- Copy constructor
- Copy assignment operator
- Destructor
- (C++11) Move constructor, move assignment operator

```cpp
class Buffer {
    char* m_data;
    size_t m_size;
    // Compiler generates: shallow copy constructor that copies the pointer
    // → two Buffers pointing to same memory → double free
};
```

**Rule of Three / Five:** if you define any of destructor, copy constructor, copy assignment — define all of them. In C++11, add move constructor and move assignment.

See [[Move Semantics]] — Rule of Five.

---

## Explicitly Disallow Functions You Don't Want

```cpp
// C++11 — use = delete:
class NonCopyable {
public:
    NonCopyable(const NonCopyable&) = delete;
    NonCopyable& operator=(const NonCopyable&) = delete;
};

// Pre-C++11 — declare private and don't define:
class NonCopyable {
private:
    NonCopyable(const NonCopyable&);
    NonCopyable& operator=(const NonCopyable&);
};
```

`= delete` gives a clear compile error. The private trick gives a link error (worse).

---

## Declare Destructors virtual in Polymorphic Base Classes

```cpp
class IStorage {
public:
    virtual ~IStorage() = default;  // REQUIRED if deleting via base pointer
};

IStorage* s = new LocalStorage();
delete s;   // without virtual destructor: only ~IStorage() called → leak of LocalStorage's resources
```

Any class with a virtual function should have a virtual destructor. Classes not meant for inheritance (no virtual functions) should NOT have virtual destructor — adds vtable overhead.

See [[Virtual Functions]] — vtable, override, virtual destructor.

---

## Never Call Virtual Functions During Construction or Destruction

```cpp
class Base {
public:
    Base() { init(); }          // calls Base::init(), not Derived::init()
    virtual void init() {}
};

class Derived : public Base {
    int* m_data;
public:
    Derived() : m_data(new int[100]) {}
    void init() override { use(m_data); }  // m_data not yet constructed when Base() runs!
};
```

During construction, the object's type is the class being constructed. Virtual dispatch doesn't reach the derived class. During `Base()`, `init()` calls `Base::init()`, not `Derived::init()`.

---

## Have operator= Return Reference to *this

```cpp
Widget& operator=(const Widget& rhs) {
    // ...
    return *this;   // enables: a = b = c = d;
}

Widget& operator+=(const Widget& rhs) {
    // ...
    return *this;
}
```

This is a convention — the standard library types and all built-in types follow it. Break it and your type won't work with chained assignment.

---

## Handle Self-Assignment in operator=

```cpp
Widget& operator=(const Widget& rhs) {
    if (this == &rhs) return *this;   // identity check

    delete[] m_data;
    m_data = new char[rhs.m_size];    // safe now — rhs is different object
    std::copy(rhs.m_data, rhs.m_data + rhs.m_size, m_data);
    return *this;
}

// Better — copy-and-swap idiom (strong exception safety + handles self-assignment):
Widget& operator=(Widget rhs) {     // rhs is a copy
    swap(*this, rhs);
    return *this;
}
```

See [[Exception Handling]] — copy-and-swap for strong exception safety guarantee.

---

## Use RAII to Manage Resources

```cpp
// Bad — leak if exception thrown between new and delete:
void f() {
    Widget* w = new Widget();
    risky_call();   // throws → w leaked
    delete w;
}

// Good — RAII:
void f() {
    auto w = std::make_unique<Widget>();
    risky_call();   // throws → ~unique_ptr runs, Widget deleted
}
```

Every resource (memory, fd, mutex, socket) should be owned by an RAII object. Destructors always run on scope exit, even during exception unwinding.

See [[RAII]], [[Smart Pointers]].

---

## Prefer Pass-by-Reference-to-const over Pass-by-Value

```cpp
// Bad — copies the whole string:
void print(std::string s);

// Good — no copy, const guarantees no modification:
void print(const std::string& s);

// Exception: pass by value for cheap types (int, char, double, iterators):
void set(int x);   // value is fine — copy is cheap
```

Pass-by-value for user-defined types calls copy constructor + destructor. For large objects this is expensive. Also avoids object slicing (passing derived as base by value loses the derived part).

See [[Inheritance]] — object slicing.

---

## Don't Try to Return a Reference When You Must Return an Object

```cpp
// WRONG — returning reference to local:
const Rational& operator*(const Rational& lhs, const Rational& rhs) {
    Rational result(lhs.n * rhs.n, lhs.d * rhs.d);
    return result;   // dangling reference — result destroyed on return
}

// CORRECT — return by value (NRVO optimizes away the copy):
Rational operator*(const Rational& lhs, const Rational& rhs) {
    return Rational(lhs.n * rhs.n, lhs.d * rhs.d);
}
```

---

## Minimize Casting

```cpp
// Prefer named casts to C-style:
(int)x                         // C-style — ambiguous, hard to find in code
static_cast<int>(x)            // explicit intent, searchable

// Avoid dynamic_cast in tight loops — RTTI has cost
// Redesign interface to not need it:
```

See [[Type Casting]] — full cast guide.

---

## Strive for Exception-Safe Code

A function is exception-safe if, when an exception is thrown, it:
- **Basic guarantee:** objects remain valid (no leaks, consistent state)
- **Strong guarantee:** operation is all-or-nothing (commit-or-rollback)
- **Nothrow guarantee:** never throws (marked `noexcept`)

```cpp
// Strong guarantee via copy-and-swap:
void Container::add(const Item& item) {
    auto copy = m_data;
    copy.push_back(item);   // may throw — copy is modified, not m_data
    std::swap(m_data, copy);// noexcept — commit
}
```

See [[Exception Handling]] — exception safety levels.

---

## Make Interfaces Easy to Use Correctly, Hard to Use Incorrectly

```cpp
// Bad — caller must remember to pass month 1-12, day 1-31 in right order:
Date(int month, int day, int year);
Date d(30, 3, 1995);   // March 30? Day 30?

// Good — use types that encode constraints:
Date(Month month, Day day, Year year);
Date d(Month::March, Day(30), Year(1995));  // unambiguous
```

Types, `const`, `explicit`, `= delete` are your tools for making the wrong usage not compile.

---

## Prefer nullptr to 0 and NULL (C++11)

```cpp
void f(int);
void f(void*);

f(0);       // calls f(int) — surprising
f(NULL);    // may call f(int) — implementation-defined
f(nullptr); // calls f(void*) — correct and clear

std::shared_ptr<int> p = nullptr;   // clearly a null pointer, not integer 0
```

See [[../C++11/Overview]].

---

## Prefer alias declarations to typedefs (C++11)

```cpp
// typedef — doesn't work with templates:
typedef std::vector<int> IntVec;

// using — works with templates:
using IntVec = std::vector<int>;

template<typename T>
using Vec = std::vector<T>;   // template alias — typedef can't do this
```

---

## Prefer scoped enums to unscoped enums (C++11)

```cpp
// Unscoped — leaks names into enclosing scope:
enum Color { Red, Green, Blue };  // Red is global
int Red = 5;  // error: redefinition

// Scoped — no name leakage, no implicit int conversion:
enum class Color { Red, Green, Blue };
Color c = Color::Red;   // explicit scope
int x = Color::Red;     // ERROR — no implicit conversion, intentional
```

---

## Prefer deleted Functions to private Undefined Ones (C++11)

```cpp
// Old way — private + undefined:
class Foo {
private:
    Foo(const Foo&);   // link error if called (even from member functions)
};

// New way — = delete:
class Foo {
public:
    Foo(const Foo&) = delete;   // clear compile error with good message
};

// Can delete any function, not just constructors:
void process(double d);
void process(int) = delete;   // prevent process(42) from converting 42 to double
```

---

## Declare Overriding Functions override (C++11)

```cpp
class Base {
    virtual void f(int);
};

class Derived : public Base {
    void f(int) override;   // compiler checks this actually overrides something
    // void f(float) override;  → ERROR — no matching virtual in Base
};
```

Without `override`, a typo silently creates a new virtual function instead of overriding the base one.

See [[Virtual Functions]].

---

## Declare Functions noexcept If They Won't Throw (C++11)

```cpp
int add(int a, int b) noexcept { return a + b; }

// Move operations should be noexcept:
class Buffer {
public:
    Buffer(Buffer&&) noexcept;            // required for std::vector reallocation
    Buffer& operator=(Buffer&&) noexcept;
};
```

`std::vector` only uses move during reallocation if the move is `noexcept`. Otherwise it copies — safe but slow.

See [[Exception Handling]] — noexcept and exception safety.

---

## Use make_unique and make_shared (C++14/11)

```cpp
// Bad — two separate expressions, leak if exception between new and constructor:
std::shared_ptr<Widget> sp(new Widget(arg));

// Good — single expression, no leak:
auto sp = std::make_shared<Widget>(arg);
auto up = std::make_unique<Widget>(arg);   // C++14
```

Also: `make_shared` allocates the control block and the object in one allocation — faster than `shared_ptr(new T)`.

See [[Smart Pointers]].

---

## Use std::move on Rvalue References, std::forward on Universal References

```cpp
// Move constructor — rvalue reference, always move:
Buffer(Buffer&& other) noexcept : m_data(std::move(other.m_data)) {}

// Forwarding function — universal reference, forward (preserves value category):
template<typename T>
void wrapper(T&& arg) {
    target(std::forward<T>(arg));   // forwards as lvalue or rvalue depending on what was passed
}
```

`std::move` unconditionally casts to rvalue. `std::forward` conditionally casts — only if the original argument was an rvalue.

See [[Move Semantics]].

---

## Avoid Default Lambda Capture Modes

```cpp
// [=] — captures everything by copy. What exactly? Hard to tell.
// [&] — captures everything by reference. Dangling reference risk.

// Bad:
auto f = [=]() { return m_value * factor; };   // captures 'this' by copy? No — copies *this pointer
auto f = [&]() { return x; };                  // x may be destroyed before lambda runs

// Good — capture explicitly:
auto f = [value = m_value, factor]() { return value * factor; };
auto f = [this]() { return m_value; };   // explicit this capture
```

---

## Prefer Task-Based to Thread-Based Programming

```cpp
// Thread-based — you manage everything:
std::thread t(compute);
t.join();

// Task-based — runtime manages thread pool, exceptions propagate:
auto fut = std::async(std::launch::async, compute);
auto result = fut.get();   // gets return value or re-throws exception
```

`std::async` returns a `std::future` that carries the result or exception. Manual threads don't propagate exceptions.

---

## Use std::atomic for Concurrency, volatile for Special Memory

```cpp
// atomic — thread-safe read/modify/write, prevents data races:
std::atomic<int> counter{0};
counter++;   // atomic increment — visible to all threads

// volatile — tells compiler "don't optimize this away":
volatile int* mmio_reg = (int*)0x1234;  // memory-mapped I/O register
*mmio_reg = 1;   // compiler must actually write, even if value is unused
```

`volatile` does NOT make operations atomic or thread-safe. `std::atomic` is for threads; `volatile` is for hardware registers.

See [[02 - Memory Ordering]].

---

## Summary Table — Most Important Items

| Item | Rule |
|---|---|
| Initialization | Initializer list > body assignment |
| Resources | RAII — every resource in a wrapper |
| Polymorphism | Virtual destructor in base classes |
| Construction | Never call virtual during ctor/dtor |
| Copy/Move | Rule of Five — define all five or none |
| Self-assignment | Check or use copy-and-swap |
| Passing | const& for objects, value for primitives |
| Exceptions | noexcept moves, strong guarantee via copy-swap |
| Interfaces | Make wrong use fail to compile |
| nullptr | nullptr not 0 or NULL |
| override | Always mark overrides |
| Enums | enum class not enum |
| Smart ptrs | make_unique / make_shared |
| Lambdas | Explicit captures, not [=] or [&] |
| Concurrency | atomic not volatile for threads |

---

## Related Notes

- [[RAII]] — resource management
- [[Smart Pointers]] — unique_ptr, shared_ptr
- [[Move Semantics]] — Rule of Five, std::move, std::forward
- [[Virtual Functions]] — vtable, override, virtual destructor
- [[Exception Handling]] — exception safety levels, noexcept
- [[Inheritance]] — polymorphism, slicing
- [[Type Casting]] — named casts
- [[02 - Memory Ordering]] — atomic vs volatile

---

## Understanding Check

> [!question]- Meyers says "never call virtual functions during construction or destruction." What exactly happens in LDS if `InputMediator`'s base class called a virtual `onInit()` in its constructor, and why is the derived override never reached?
> During execution of the base constructor, the object's dynamic type is the base — the derived subobject does not yet exist. The `vptr` is set to the base's vtable, so the virtual call dispatches to the base version. In LDS terms: if `InputMediator` inherited from some `MediatorBase` that called `virtual onInit()` in `MediatorBase()`, `InputMediator::onInit()` would never be called during construction — the mediator's setup logic would silently be skipped, leaving it in an uninitialized state when `run()` is called. The fix is to call initialization logic explicitly after construction (e.g., via a separate `init()` call or factory function).

> [!question]- Meyers recommends the member initializer list over body assignment. What is the concrete performance difference for a `std::string` member, and why does order in the list matter?
> A `std::string` member is default-constructed (empty string allocated) before the constructor body runs, then assigned in the body — two operations. The initializer list directly constructs it with the given value — one operation. For large strings this avoids an unnecessary allocation and copy. Order matters because members are *initialized in the order they are declared in the class*, not the order they appear in the initializer list. If the list order differs from declaration order, the compiler may warn and, more importantly, a member that appears later in declaration order but earlier in the list may be initialized before a member it depends on — causing use of an uninitialized value.

> [!question]- What goes wrong if you forget to handle self-assignment in `operator=`, and why does copy-and-swap solve both the self-assignment and exception safety problems simultaneously?
> Without a self-assignment check, `delete[] m_data` destroys the buffer, and then `m_data = new char[rhs.m_size]` followed by `memcpy(... rhs.m_data ...)` reads from the just-freed memory — undefined behavior. Copy-and-swap takes `rhs` by value (a copy is made before the function body), so by definition `rhs` is always a distinct object. Even if `a = a` is called, the copy is made first (now a separate object), and the swap exchanges `this`'s state with that copy. Self-assignment is safe, and if the copy constructor throws, `this` is unchanged (strong guarantee).

> [!question]- Meyers says to prefer `nullptr` over `0` or `NULL`. What real overload resolution bug does this prevent, and is there an equivalent pitfall in LDS?
> `0` is an integer literal; `NULL` is typically `0` or `0L`. When two overloads exist — `f(int)` and `f(void*)` — passing `0` or `NULL` calls `f(int)`, which is almost certainly wrong when the intent is a null pointer. `nullptr` has type `std::nullptr_t`, which converts to any pointer type but not to integral types, so `f(nullptr)` unambiguously calls `f(void*)`. In LDS: if `InputMediator` has overloads for `Register(IStorage*)` and a hypothetical `Register(int id)`, passing `0` to mean "no storage" would call the integer overload silently. Using `nullptr` catches this at compile time.

> [!question]- Meyers warns against default lambda capture `[=]` and `[&]`. What dangling reference bug could appear in LDS if a lambda capturing `[&]` is stored in the thread pool's work queue?
> `[&]` captures variables by reference — the lambda holds a reference to a stack-allocated local. If the lambda is created in a function, stored in the thread pool queue, and that function returns before the thread executes the lambda, all captured references dangle. In LDS a command-creation lambda like `[&data]{ process(data); }` where `data` is a local `DriverData` on the caller's stack would result in the worker thread accessing freed stack memory. The correct approach is explicit capture by value `[data]` or capture of a `shared_ptr` to heap-allocated data.
