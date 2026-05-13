# Effective C++ — The Non-Obvious Rules

## The Model
A collection of traps where C++ lets you do something that looks correct but silently breaks. Each rule is a case where the language's defaults work against you. Knowing these is the difference between "can write C++" and "writes correct C++."

## The Rules (LDS-anchored)

**Rule: Prefer `const`, `enum`, `inline` over `#define`**
`#define MAX 100` — the preprocessor replaces MAX with 100 before the compiler runs. MAX doesn't exist in the symbol table. Debugger shows `100`, not `MAX`. Type checking: none. Use `constexpr int MAX = 100;` — typed, scoped, debuggable.

**Rule: Use `const` wherever possible**
A `const` reference parameter tells the compiler "I won't modify this" — enables optimizations and catches bugs at compile time. `void Send(const Request& req)` — the compiler enforces that Send doesn't modify `req`. Without `const`, every call site must wonder if Send has side effects on the request.

**Rule: Make sure objects are initialized before use**
```cpp
// This is NOT zero-initialized in C++:
int x;         // x is whatever bits were in that stack slot — UB to read
int y = 0;     // this is initialized

// Member initialization list vs assignment body:
NBDDriverComm::NBDDriverComm(int fd) : m_fd(fd) { }   // initializes
// NOT: NBDDriverComm::NBDDriverComm(int fd) { m_fd = fd; }  // assigns (default-constructs first)
```
For non-trivial types, the assignment body default-constructs then assigns — two operations where one suffices.

**Rule: Know what functions C++ silently writes**
If you don't declare them, the compiler generates: default constructor, copy constructor, copy assignment, destructor. In C++11: also move constructor and move assignment. These generated versions do member-wise copy/move — fine for value types, wrong for types owning resources (will copy the pointer, not the resource).

**Rule: Explicitly disallow copying when it doesn't make sense**
```cpp
// Singletons, handles, RAII wrappers:
LocalStorage(const LocalStorage&) = delete;
LocalStorage& operator=(const LocalStorage&) = delete;
```
Without `= delete`, the compiler silently generates a copy that shallow-copies `m_data` — two `LocalStorage` objects pointing to the same buffer → double-free.

**Rule: Declare destructors `virtual` in polymorphic base classes**
Covered in Virtual Functions. Always. No exceptions for classes with virtual methods.

**Rule: Never call virtual functions in constructors or destructors**
During `IDriverComm` construction, the vtable points to `IDriverComm`'s version (not the derived class's) — the derived class hasn't been constructed yet. Calling a virtual function in a base constructor always calls the base version.

**Rule: Have `operator=` return a reference to `*this`**
```cpp
LocalStorage& operator=(const LocalStorage& rhs) {
    // ...
    return *this;   // enables: a = b = c = d;
}
```

## In LDS

`services/local_storage/include/LocalStorage.hpp`

`LocalStorage` owns a `std::vector<char>` and a `std::shared_mutex`. Both cannot be safely copied (mutex is not copyable). `= delete` on copy constructor and copy assignment prevents accidental copying. `std::shared_mutex` is also move-constructible with care — `LocalStorage`'s move constructor must transfer ownership carefully.

## Validate

1. `LocalStorage copy = existing_storage;` — if copy constructor is not `= delete`, what does the compiler-generated copy do to `m_mutex`?
2. `NBDDriverComm::NBDDriverComm(int fd) : m_fd(fd), m_buf()` vs body assignment `m_fd = fd`. For `m_buf` (a `std::vector`), which is faster and why?
3. You add a virtual method to `IDriverComm`. You have existing code that creates `IDriverComm` objects (not derived) and stores them by value in a vector. What breaks and why?

## Connections

**Theory:** [[Core/Theory/C++/Effective C++ Meyers]]  
**Mental Models:** [[RAII — The Machine]], [[Smart Pointers — The Machine]], [[Virtual Functions — The Machine]], [[Undefined Behavior — The Machine]], [[Preprocessor — The Machine]], [[Move Semantics — The Machine]]  
**Tradeoffs:** [[Why RAII over manual cleanup]]  
**LDS Implementation:** [[LDS/Application/LocalStorage]] — = delete on copy constructor/assignment; [[LDS/Linux Integration/NBDDriverComm]] — member initialization list over assignment body  
**Glossary:** [[RAII]], [[shared_ptr]]
