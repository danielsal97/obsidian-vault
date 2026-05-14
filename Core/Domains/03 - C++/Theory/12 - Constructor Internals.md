# Constructor Internals

Constructors have more moving parts than they appear. Initialization order, implicit conversions, static lifetimes, copy elision, and brace initialization all have rules that are easy to get wrong — and the compiler will not always warn you.

---

## Initialization Order

Members are initialized in the order they are **declared in the class**, not the order they appear in the initializer list. If the list order differs from the declaration order, a member can be initialized using another member that has not been initialized yet.

```cpp
class Foo {
    int m_size;
    int* m_data;
public:
    Foo(int n) : m_data(new int[n]), m_size(n) {}
    // Bug: m_size is declared first, so it's initialized first.
    // m_data(new int[n]) runs second — fine here.
    // But if m_data(new int[m_size]) were written, m_size is garbage.
};
```

Write the initializer list in the same order as the declarations to make the intent obvious.

**Delegating constructors (C++11):** one constructor can call another in the initializer list. Eliminates duplication without needing a private `init()` function.

```cpp
Foo() : Foo(0) {}          // delegates to Foo(int)
Foo(int n) : m_size(n) {}  // base constructor
```

**Default member initializers:** `int x = 0;` or `int x{0};` in the class body. The constructor initializer list overrides them if present. Useful for giving members safe defaults without repeating them in every constructor.

---

## explicit Keyword

A single-argument constructor that is not marked `explicit` acts as an implicit conversion. This allows silent, unintended conversions.

```cpp
struct Wrapper { Wrapper(int n) {} };
void take(Wrapper w) {}

take(42);   // compiles — 42 implicitly converted to Wrapper
```

Mark any single-argument constructor `explicit` unless the conversion is intentional and obvious (e.g., `std::string` from string literals is a deliberate design choice).

The same applies to conversion operators:

```cpp
explicit operator bool() const { return m_fd >= 0; }
```

`std::fstream` uses `explicit operator bool()` so that `if (file)` works but `int x = file;` does not compile. Without `explicit`, any arithmetic context would silently convert a stream to an integer.

---

## Static Initialization Order Fiasco

Non-local static objects (globals, static data members, function-static objects in different translation units) have an **undefined initialization order** across translation units. If object A depends on object B and they live in different `.cpp` files, B may not be initialized when A's constructor runs.

The fix is the **Meyers singleton** — a function-local static:

```cpp
Foo& get_foo() {
    static Foo instance;  // initialized on first call
    return instance;
}
```

C++11 guarantees that function-local statics are initialized exactly once and that initialization is thread-safe. Replacing global statics with this pattern eliminates the fiasco entirely. LDS uses this pattern for singletons rather than relying on global construction order.

---

## RVO and NRVO (Copy Elision)

**Return Value Optimization (RVO):** when a function returns a temporary (a prvalue), the compiler constructs the object directly in the caller's storage. The constructor runs once, not three times.

**Named Return Value Optimization (NRVO):** the same optimization applied when a function returns a named local variable by name. Not guaranteed before C++17, but applied by all major compilers.

**C++17 mandatory elision:** for prvalue returns, copy elision is no longer an optimization — it is required by the standard.

```cpp
Foo makeFoo() {
    return Foo(42);   // C++17: Foo constructed once, directly at call site
}
Foo f = makeFoo();   // no copy, no move — one constructor call
```

RVO cannot apply when a function returns different named variables in different branches, or when returning a function parameter. In those cases a move constructor is used if available.

---

## Aggregate Initialization and Brace Init

An **aggregate** is a class with no user-declared constructors, no private or protected non-static data members, no base classes with constructors (C++11 rules), and no virtual functions. Aggregates can be initialized with `{}` without a constructor call.

The `{}` syntax rejects narrowing conversions at compile time — `int x{3.14}` is ill-formed. The `()` syntax silently truncates.

When a class has an `std::initializer_list` constructor, `{}` syntax prefers it over other constructors:

```cpp
std::vector<int> v{5};   // 1-element vector containing 5
std::vector<int> v(5);   // 5-element vector of zeros
```

This is the most common brace-init trap. When in doubt, use `()` for constructors that take a count or size, and `{}` for element lists.

---

## Temporary Objects and Lifetime Extension

Temporaries are destroyed at the end of the **full-expression** — the outermost expression in a statement. Binding a `const` lvalue reference or an rvalue reference to a temporary extends its lifetime to match the reference's scope.

```cpp
const std::string& s = make_string();   // temporary's lifetime extended to s's scope
```

The trap: lifetime extension applies only when the temporary is bound **directly** to the reference. If you bind a reference to a member of a temporary, or to the result of a member function call on a temporary, the temporary is still destroyed at the end of the expression.

```cpp
const std::string& s = get_obj().name;  // get_obj() temporary destroyed immediately
                                        // s is a dangling reference
```

---

## Related

→ [[03 - Move Semantics]] — lvalue/rvalue, forwarding references
→ [[01 - RAII]] — destructor timing and stack unwinding
→ [[09 - Exception Handling]] — exception-safe constructors
→ [[23 - Copy Elision — The Machine]] (Mental Models)

---

## Understanding Check

> [!question]- A class declares `int m_len` before `int* m_buf`. The constructor initializer list is written as `: m_buf(new int[10]), m_len(10)`. Is there a bug?
> No — in this case both initializers use the constant `10`, so the order does not matter. But if `m_buf` were written as `new int[m_len]`, there would be a bug: `m_len` is declared first, so it is initialized first, but the initializer list would have `m_buf` listed first. `m_len` would be initialized to `10` in its own line, then `m_buf(new int[m_len])` runs second — actually fine here too. The real danger is the reverse: if `m_len` were initialized from `m_buf`'s size, `m_buf` would be garbage at that point. The rule: list order in the initializer list is irrelevant; declaration order is all that matters.

> [!question]- Why does `std::vector<int> v{5}` create a one-element vector when `std::vector<int> v(5)` creates a five-element vector?
> `std::vector` has an `initializer_list<int>` constructor. When `{}` is used, the compiler prefers the `initializer_list` constructor over all others, so `{5}` is treated as a one-element list containing `5`. The `(5)` syntax uses the count constructor that takes a `size_t`, creating five default-initialized elements. This priority rule for `initializer_list` constructors applies to any class that has one — always use `()` when passing a size or count.

> [!question]- What is the static initialization order fiasco, and why does the Meyers singleton pattern fix it?
> Non-local statics across translation units are initialized in an order that is not defined by the standard — only the order within a single TU is guaranteed. If static `A` in `a.cpp` calls a function that uses static `B` in `b.cpp` during `A`'s construction, `B` may not exist yet. The Meyers singleton replaces the global with a function-local static: local statics are initialized on first call, which happens at a known, controlled point in program execution. C++11 also guarantees that this initialization is thread-safe, removing the need for explicit locks around first-use initialization.

> [!question]- Under what conditions does RVO not apply, and what happens instead?
> RVO does not apply when a function has multiple return statements returning different named local variables, or when it returns a function parameter. The compiler cannot know at the start of the function which object to construct directly in the caller's storage. In these cases the compiler falls back to calling the move constructor (if available) or the copy constructor. C++17 mandatory elision only covers prvalue returns — returning a freshly constructed unnamed temporary — not named variables.
