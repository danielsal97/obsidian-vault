# Move Semantics

Move semantics allow transferring resources from one object to another without copying. Introduced in C++11. Critical for performance and for classes that own non-copyable resources.

---

## The Problem Move Solves

Before C++11, returning a vector from a function copied all its elements:

```cpp
std::vector<int> make_big() {
    std::vector<int> v(1000000);
    return v;   // C++03: copies 1M ints — O(n)
}

auto v = make_big();   // another copy
```

With move semantics, the return transfers ownership of the buffer — O(1):
```cpp
auto v = make_big();   // C++11: moves the buffer, no copy
```

---

## lvalue vs rvalue

**lvalue** — has a name, has an address, persists beyond the expression.
```cpp
int x = 5;    // x is an lvalue
int& r = x;   // lvalue reference
```

**rvalue** — temporary, no name, about to be destroyed.
```cpp
int y = x + 1;   // (x+1) is an rvalue — temporary
```

**rvalue reference (`&&`)** — binds only to rvalues (temporaries):
```cpp
int&& rr = 5;          // rvalue reference to temporary
int&& rr = x + 1;      // fine — x+1 is temporary
int&& rr = x;          // error — x is an lvalue
```

---

## Move Constructor

Takes ownership of another object's resources. Leaves the source in a valid but unspecified (usually empty) state.

```cpp
class Buffer {
    char* m_data;
    size_t m_size;
public:
    // Copy constructor — allocates new memory, copies bytes:
    Buffer(const Buffer& other)
        : m_size(other.m_size), m_data(new char[other.m_size]) {
        memcpy(m_data, other.m_data, m_size);
    }
    
    // Move constructor — steals the pointer, no allocation:
    Buffer(Buffer&& other) noexcept
        : m_data(other.m_data), m_size(other.m_size) {
        other.m_data = nullptr;   // source no longer owns it
        other.m_size = 0;
    }
    
    ~Buffer() { delete[] m_data; }
};

Buffer a(1000);
Buffer b = std::move(a);   // move — O(1), a is now empty
Buffer c = a;              // copy — O(n), c has its own buffer
```

---

## std::move

`std::move` doesn't move anything — it's a cast from lvalue to rvalue reference. It says "I'm done with this, you may move from it."

```cpp
std::vector<int> a = {1, 2, 3};
std::vector<int> b = std::move(a);   // cast a to rvalue → move constructor called
// a is now empty (valid but unspecified)
// b owns the buffer
```

After `std::move(a)`, `a` is in a valid but unspecified state. You can reassign it or destroy it, but you shouldn't read from it.

---

## Move Assignment

```cpp
Buffer& operator=(Buffer&& other) noexcept {
    if (this != &other) {
        delete[] m_data;          // release our current resource
        m_data = other.m_data;    // steal other's resource
        m_size = other.m_size;
        other.m_data = nullptr;   // source no longer owns it
        other.m_size = 0;
    }
    return *this;
}
```

---

## When Move is Called Automatically

The compiler automatically uses the move constructor/assignment when:
1. Returning a local variable from a function (NRVO — Named Return Value Optimization, or move if NRVO not applicable)
2. Inserting into a container when the source is a temporary
3. `std::move` is used explicitly

```cpp
std::vector<std::string> v;
std::string s = "hello";
v.push_back(std::move(s));   // s moved into vector — no copy
// s is now empty
```

---

## Rule of Five

If a class needs a custom destructor (because it manages a resource), it likely needs all five:

| Special member | When needed |
|---|---|
| Destructor | Release the resource |
| Copy constructor | Deep copy for new owner |
| Copy assignment | Deep copy + release old resource |
| Move constructor | Transfer ownership — O(1) |
| Move assignment | Transfer ownership + release old |

```cpp
class Resource {
public:
    ~Resource();                              // must have
    Resource(const Resource&);                // deep copy
    Resource& operator=(const Resource&);    // deep copy
    Resource(Resource&&) noexcept;           // move
    Resource& operator=(Resource&&) noexcept; // move
};
```

If you want to **prevent copying** (e.g., for objects owning OS resources like fds):
```cpp
Resource(const Resource&) = delete;
Resource& operator=(const Resource&) = delete;
```

`= delete` causes a compile error if anyone tries to copy — much better than silently double-closing an fd.

**LDS:** `Reactor`, `NBDDriverComm`, `InputMediator` all have `= delete` on copy — they own OS resources that can't be duplicated.

---

## Perfect Forwarding

Forwarding a value while preserving its value category (lvalue or rvalue):

```cpp
template<typename T>
void wrapper(T&& arg) {
    actual_function(std::forward<T>(arg));
    // forward preserves: lvalue → lvalue, rvalue → rvalue
}
```

Used in factory functions and variadic templates like `make_unique`:
```cpp
template<typename T, typename... Args>
std::unique_ptr<T> make_unique(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}
```

---

## noexcept on Move Operations

Mark move constructor and move assignment `noexcept`. `std::vector` uses move only if the move constructor is `noexcept` — otherwise it falls back to copying (to preserve exception safety during reallocation).

```cpp
Buffer(Buffer&&) noexcept { ... }    // vector will move, not copy
```
