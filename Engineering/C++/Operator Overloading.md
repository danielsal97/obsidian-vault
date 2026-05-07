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
```
