# Operator Overloading

Define custom behavior for operators on user-defined types.

---

## Syntax

```cpp
class Vector2 {
    float x, y;
public:
    Vector2(float x, float y) : x(x), y(y) {}
    
    // Member function — left operand is this:
    Vector2 operator+(const Vector2& rhs) const {
        return {x + rhs.x, y + rhs.y};
    }
    
    // Compound assignment:
    Vector2& operator+=(const Vector2& rhs) {
        x += rhs.x; y += rhs.y;
        return *this;
    }
    
    // Friend — both operands are parameters (needed when left operand isn't your type):
    friend std::ostream& operator<<(std::ostream& os, const Vector2& v) {
        return os << "(" << v.x << ", " << v.y << ")";
    }
};

Vector2 a{1, 2}, b{3, 4};
Vector2 c = a + b;    // calls a.operator+(b)
a += b;
std::cout << a;       // calls operator<<(cout, a)
```

---

## Operators You Can Overload

| Category | Operators |
|---|---|
| Arithmetic | `+` `-` `*` `/` `%` |
| Compound assignment | `+=` `-=` `*=` `/=` `%=` |
| Comparison | `==` `!=` `<` `>` `<=` `>=` |
| Logical | `!` `&&` `\|\|` |
| Bitwise | `&` `\|` `^` `~` `<<` `>>` |
| Increment/decrement | `++` `--` (prefix and postfix) |
| Stream | `<<` `>>` |
| Subscript | `[]` |
| Function call | `()` |
| Dereference | `*` `->` |
| Conversion | `operator T()` |
| Memory | `new` `delete` |

**Cannot overload:** `::` `.` `.*` `?:` `sizeof` `typeid`

---

## Comparison Operators

```cpp
// C++17 and earlier — define each:
bool operator==(const MyClass& rhs) const { return m_val == rhs.m_val; }
bool operator!=(const MyClass& rhs) const { return !(*this == rhs); }
bool operator< (const MyClass& rhs) const { return m_val < rhs.m_val; }
bool operator> (const MyClass& rhs) const { return rhs < *this; }
bool operator<=(const MyClass& rhs) const { return !(rhs < *this); }
bool operator>=(const MyClass& rhs) const { return !(*this < rhs); }

// C++20 — one operator generates all six:
auto operator<=>(const MyClass& rhs) const = default;
```

---

## Subscript Operator

```cpp
class Array {
    int m_data[100];
public:
    int& operator[](size_t i)             { return m_data[i]; }
    const int& operator[](size_t i) const { return m_data[i]; }
    // const version for const objects
};

Array a;
a[5] = 99;
const Array& ca = a;
int x = ca[5];   // calls const version
```

---

## Increment / Decrement

```cpp
class Counter {
    int m_val = 0;
public:
    Counter& operator++() {       // prefix ++c — returns reference to modified object
        ++m_val;
        return *this;
    }
    Counter operator++(int) {     // postfix c++ — returns copy of old value
        Counter old = *this;
        ++m_val;
        return old;
    }
};
```

Prefer prefix `++` — postfix requires a copy.

---

## Function Call Operator — Functors

```cpp
class Multiplier {
    int m_factor;
public:
    Multiplier(int f) : m_factor(f) {}
    int operator()(int x) const { return x * m_factor; }
};

Multiplier triple(3);
triple(5);    // 15 — called like a function

// Use with STL:
std::transform(v.begin(), v.end(), v.begin(), Multiplier(2));
```

Lambdas are syntactic sugar for anonymous functor classes.

---

## Conversion Operators

```cpp
class Rational {
    int num, den;
public:
    explicit operator double() const { return (double)num / den; }
    explicit operator bool()   const { return den != 0; }
};

Rational r{3, 4};
double d = static_cast<double>(r);   // explicit conversion
if (r) { ... }   // calls operator bool() — safe because explicit
```

`explicit` prevents implicit conversions — almost always use it.

---

## Smart Pointer Operators

```cpp
class UniquePtr {
    T* m_ptr;
public:
    T& operator*()  const { return *m_ptr; }  // dereference
    T* operator->() const { return m_ptr; }   // member access
    explicit operator bool() const { return m_ptr != nullptr; }
};

UniquePtr<int> p = ...;
*p = 5;
p->method();
if (p) { ... }
```

---

## Rules and Conventions

**Member vs non-member:**
- `=`, `[]`, `()`, `->` must be member functions
- `<<`, `>>` (stream) should be non-member `friend` functions (left operand is `ostream`)
- Arithmetic `+`, `-` etc. should be non-member to allow `a + b` when `a` is a different type

**Consistency:**
- If you define `==`, define `!=` too
- If you define `<`, define `>`, `<=`, `>=` too (or use `<=>`)
- If you define `+`, define `+=` too; implement `+` using `+=`

**Don't overload:**
- `&&`, `||` — overloading loses short-circuit evaluation
- `,` — confusing
- `&` (address-of) — breaks generic code

---

## rcstring Example — String with Reference Counting

A typical exercise: custom string class with copy-on-write via operator overloading:

```cpp
class RCString {
    char* m_data;
    int*  m_refcount;
    
    void release() {
        if (--(*m_refcount) == 0) {
            delete[] m_data;
            delete m_refcount;
        }
    }
public:
    RCString(const char* s) : m_refcount(new int(1)) {
        m_data = new char[strlen(s)+1];
        strcpy(m_data, s);
    }
    
    RCString(const RCString& other)           // copy — share
        : m_data(other.m_data)
        , m_refcount(other.m_refcount) {
        ++(*m_refcount);
    }
    
    RCString& operator=(const RCString& rhs) {
        if (this != &rhs) {
            release();
            m_data = rhs.m_data;
            m_refcount = rhs.m_refcount;
            ++(*m_refcount);
        }
        return *this;
    }
    
    char& operator[](size_t i) {
        // Copy-on-write: detach if shared before modifying
        if (*m_refcount > 1) {
            --(*m_refcount);
            m_refcount = new int(1);
            char* new_data = new char[strlen(m_data)+1];
            strcpy(new_data, m_data);
            m_data = new_data;
        }
        return m_data[i];
    }
    
    ~RCString() { release(); }
};

---

## Understanding Check

> [!question]- Why must `operator=` return `*this` by reference instead of by value, and what breaks if it returns void?
> Returning by reference enables chained assignment: `a = b = c` is parsed as `a = (b = c)`. If `operator=` returns void, `b = c` produces nothing and the outer `a = ...` has no right-hand operand — compile error. If it returns by value, `a = (b = c)` copies the result of `b = c` into `a`, which is an extra (potentially expensive) copy and also fails for types that are non-copyable. The convention of returning `T&` matches all built-in types and the standard library, ensuring your type works in any generic context that chains assignments.

> [!question]- Why should `operator&&` and `operator||` generally not be overloaded, and what important behavior is lost if you do?
> The built-in `&&` and `||` have short-circuit evaluation: if the left operand fully determines the result, the right operand is *not evaluated at all*. An overloaded operator is a regular function call — both arguments are evaluated before the function is invoked. Code relying on short-circuit behavior to avoid side effects or null dereferences (e.g., `ptr && ptr->isValid()`) would silently break: `ptr->isValid()` is called even when `ptr` is null, causing a crash.

> [!question]- What goes wrong if you implement `operator+` as a member function and then try to write `2 + myObj`?
> A member `operator+` takes `this` as the left operand. `2 + myObj` means `(2).operator+(myObj)` — but `2` is an `int` and has no such overload. The compiler cannot convert `int` to your type (unless an implicit conversion exists) to make it the left operand. A non-member `friend operator+(const T& lhs, const T& rhs)` handles both `myObj + 2` and `2 + myObj` symmetrically, because both sides are regular parameters subject to implicit conversion.

> [!question]- In the `RCString` copy-on-write `operator[]`, what subtle bug occurs in a multithreaded environment where two threads both read the refcount and both decide to detach?
> Both threads read `*m_refcount > 1` as true and each proceeds to decrement and allocate a private copy. The refcount is a plain `int*` — no atomic operations. Thread A decrements it to 1 and sets `m_refcount` to a new counter; Thread B also decrements what it thinks is the original counter (now 1, not 2) to 0, then `release()` is called on the original data prematurely — the shared buffer is freed while Thread A may still be writing into its "private" copy. The fix is to use atomic operations or a mutex around the detach logic, or to abandon copy-on-write in favor of `std::string` which handles this internally.

> [!question]- Why is it better to implement `operator+` in terms of `operator+=` rather than the other way around?
> `operator+=` modifies `*this` in-place — it is the primitive operation that does the real work with no extra copies. `operator+` must return a new object (cannot modify either operand since both are `const`). The natural implementation is: `T operator+(T lhs, const T& rhs) { lhs += rhs; return lhs; }` — take the left operand by value (copy), modify it with `+=`, return it. If you implement `+=` in terms of `+`, you create a temporary and then copy-assign, doing an extra allocation and copy every time. The `+=`-first approach also ensures both operators stay consistent: there is only one implementation of the actual arithmetic.
```
