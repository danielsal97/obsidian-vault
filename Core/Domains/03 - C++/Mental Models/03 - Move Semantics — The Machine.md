# Move Semantics — The Machine

## The Model
Stealing resources instead of copying them. A filing cabinet: copy = photocopy every document (expensive, O(n)); move = pick up the entire cabinet and hand it over — the original cabinet is left empty. `std::move` is just a label that says "this cabinet can be stolen from." The move constructor does the actual theft.

## How It Moves

```
std::vector<char> a(1000000);   // a owns 1MB heap buffer

// COPY:
std::vector<char> b = a;   // copies 1MB byte by byte → O(n)
// Both a and b own their own 1MB buffer. Two heap allocations.

// MOVE:
std::vector<char> c = std::move(a);   // steals a's internal pointer
// c owns the 1MB buffer. a is now empty (size=0, ptr=nullptr).
// O(1) — only 3 pointer assignments.
```

**What `std::move` actually does:** Nothing. It is a cast to an rvalue reference. It does not move anything. It gives permission to move. The move constructor/assignment is what actually moves.

**Lvalue vs rvalue:**
- lvalue: has a name, has an address, can appear on left of `=`. Example: `x`, `m_data`, `local_var`
- rvalue: temporary, no name, cannot appear on left of `=`. Example: `x + 1`, `func()`, `std::move(x)`

## The Blueprint

**Rule of Five:** if you define any one of these, define all five:
```cpp
class LocalStorage {
    char* m_buf;
    size_t m_size;
public:
    ~LocalStorage()                                      { delete[] m_buf; }
    LocalStorage(const LocalStorage& o)                  { /* deep copy */ }
    LocalStorage& operator=(const LocalStorage& o)       { /* deep copy */ }
    LocalStorage(LocalStorage&& o) noexcept              
        : m_buf(o.m_buf), m_size(o.m_size)               
        { o.m_buf = nullptr; o.m_size = 0; }             // steal + zero out source
    LocalStorage& operator=(LocalStorage&& o) noexcept  
        { delete[] m_buf; m_buf = o.m_buf; o.m_buf = nullptr; return *this; }
};
```

**`noexcept` on move:** critical for STL containers. `std::vector` only uses your move constructor instead of copy during realloc if it's marked `noexcept`. Without it, vector falls back to the slower copy.

## Where It Breaks

- **Using `std::move(x)` and then using `x`**: `x` is in a valid but unspecified state — usually empty/null. Don't use it after moving from it.
- **Move constructor leaves source in inconsistent state**: if you steal the pointer but don't null it out in source, both objects think they own the buffer → double-free.
- **Missing `noexcept`**: vector's realloc silently falls back to copy — 100x slower for large vectors.

## In LDS

`utilities/threading/thread_pool/src/thread_pool.cpp`

Tasks submitted to the WPQ are `std::function<void()>` objects. When pushing to the queue, they are moved (not copied) into the queue's internal storage. This avoids copying potentially large captured lambdas. The move happens implicitly when pushing an rvalue (temporary lambda) or explicitly when using `std::move(task)`.

`LocalStorage` uses `std::vector<char>` for storage. The vector's internal move constructor is O(1) — if `LocalStorage` itself needs to be moved (e.g., stored in a container that reallocates), the vector is stolen, not copied.

## Validate

1. `std::move(driver)` is called when injecting `IDriverComm` into `InputMediator`. After the call, is `driver` still usable? What is its state?
2. A worker task is a lambda capturing a `std::vector<char> data(1MB)`. You push it to the WPQ with `std::move(task)`. How much data is copied during the push?
3. `LocalStorage` is stored in a `std::vector<LocalStorage>`. The vector resizes (doubles capacity). Does it copy or move each `LocalStorage`? What determines which one it uses?

## Connections

**Theory:** [[03 - Move Semantics]]  
**Mental Models:** [[RAII — The Machine]], [[Smart Pointers — The Machine]], [[STL Containers — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Utilities Framework]] — lambda moves into WPQ
