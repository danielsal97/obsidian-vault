# Compiler Generated Behavior

C++ generates up to five special member functions automatically: default constructor, copy constructor, copy assignment, move constructor, and move assignment. The rules for when each is generated — and suppressed — determine correctness, performance, and subtle double-free bugs.

---

## The Rule of 0/3/5

**Rule of 0:** if every member is an RAII type (`unique_ptr`, `string`, `vector`), define none of the five. The compiler generates correct versions that delegate to each member's own special members. This is the default for modern C++.

**Rule of 3 (C++03):** if you define a destructor, copy constructor, or copy assignment, define all three. The compiler's generated copy does a shallow memberwise copy — wrong for any class that owns a raw pointer.

**Rule of 5 (C++11+):** if you define any of the five special members, consider defining all five. Defining a destructor suppresses the implicit move constructor and move assignment operator — the class silently falls back to copying.

---

## What the Compiler Generates (and When It Doesn't)

| Special member | Generated when |
|---|---|
| Default constructor | No constructors are declared |
| Copy constructor | No user-declared copy ctor and no user-declared move operation |
| Copy assignment | Same conditions as copy constructor |
| Move constructor | No user-declared destructor, copy ctor, copy=, move ctor, or move= |
| Move assignment | Same conditions as move constructor |
| Destructor | Always, if not user-declared |

The suppression rules are the dangerous part. Declaring a destructor kills both move constructor and move assignment. The class becomes copy-only — silently, with no compiler warning.

---

## The Most Common Bug

```cpp
class Buffer {
    char* m_data;
public:
    ~Buffer() { delete[] m_data; }
    // Move constructor is NOT generated.
    // Buffer b2 = std::move(b1); calls the copy constructor.
    // Both b1 and b2 point to the same memory.
    // Double-free when either destructs.
};
```

The fix is either to explicitly define the move constructor and move assignment, or to replace the raw pointer with `unique_ptr` and apply Rule of 0.

---

## Hidden Temporaries and Costs

**Pass by value:** each call invokes a copy or move constructor, depending on the argument's value category.

**Return by value:** copy or move unless RVO applies. See [[12 - Constructor Internals]] for the full RVO rules.

**`push_back` vs `emplace_back`:** `push_back(obj)` copies or moves an existing object into the container. `emplace_back(args...)` constructs the object directly in place — no temporary, no copy.

```cpp
v.push_back(Foo(1, 2));    // Foo constructed, then moved into vector
v.emplace_back(1, 2);      // Foo constructed in place — one operation
```

**Range-for:** `for (auto x : v)` copies each element. Use `for (const auto& x : v)` to avoid copies over non-trivial types.

---

## = default and = delete

`= default` explicitly requests the compiler-generated version. It also makes a special member **trivial** if all conditions for triviality are met — relevant for `memcpy` safety and performance.

`= delete` removes the overload entirely. Any attempt to call it is a compile error with a clear message, which is better than making a function private (private gives a confusing access error; deleted gives "deleted function" at the call site).

**Standard pattern for non-copyable classes:**
```cpp
Foo(const Foo&) = delete;
Foo& operator=(const Foo&) = delete;
```

**Restore move after declaring destructor:**
```cpp
Buffer(Buffer&&) noexcept = default;
Buffer& operator=(Buffer&&) noexcept = default;
```

---

## Trivial Types

**Trivially copyable:** safe to copy with `memcpy`. Requires no user-defined copy constructor, copy assignment, move constructor, move assignment, or destructor — and the same for all non-static data members.

**Standard layout:** memory layout is compatible with C structs. No virtual functions, no mixed access specifiers in non-static data, base classes follow the same rules. Safe for `reinterpret_cast` and `offsetof`.

**POD (plain old data):** trivially copyable + standard layout. Satisfies both sets of constraints simultaneously.

These properties matter for serialization, inter-process shared memory, and interfacing with C APIs. Use `std::is_trivially_copyable<T>` and `std::is_standard_layout<T>` to check.

---

## Related

→ [[03 - Move Semantics]] — rvalue refs, moved-from state
→ [[02 - Smart Pointers]] — `unique_ptr` as the canonical Rule of 0 wrapper
→ [[01 - RAII]] — why destructors must be defined when managing resources
→ [[21 - Move Semantics — The Machine (deep)]] (Mental Models)
→ [[12 - Constructor Internals]]

---

## Understanding Check

> [!question]- A class has a user-declared destructor and nothing else. What special members does the compiler generate, and what is the risk?
> The compiler generates the default constructor, copy constructor, and copy assignment. It does NOT generate a move constructor or move assignment — the presence of a user-declared destructor suppresses both. Any attempt to move an instance of this class will silently call the copy constructor instead. If the class owns a raw pointer, both the source and destination will hold the same pointer after the "move", causing a double-free when either is destroyed.

> [!question]- What is the difference between `= default` and omitting a special member declaration entirely?
> Both produce a compiler-generated implementation, but `= default` is explicit and has additional effects. It makes the special member part of the class's declared interface, which matters for triviality: a copy constructor declared `= default` can still be trivial if all other triviality conditions hold, whereas a user-provided body (even an identical one) is never trivial. `= default` also re-enables a special member that would otherwise be suppressed — for example, explicitly defaulting a move constructor in a class that declares a destructor restores move semantics.

> [!question]- Why does `emplace_back` avoid a copy where `push_back` does not, and when does the difference actually matter?
> `push_back` takes an already-constructed object and copies or moves it into the container's storage. Even if you pass a temporary, there is still a construction step (the temporary) and then a move into the container. `emplace_back` forwards its arguments directly to the element's constructor and constructs the element in place — no intermediate object. The difference matters most for types that are expensive to move (e.g., types with many members that do not have move constructors) or for types that are non-movable entirely.

> [!question]- When is a type "trivially copyable" and why does it matter for low-level code?
> A type is trivially copyable if it has no user-provided copy constructor, copy assignment, move constructor, move assignment, or destructor, and all its non-static data members are themselves trivially copyable. The practical consequence: `memcpy` is a correct way to copy instances of such a type. This matters for serialization (writing objects directly to a buffer), shared memory (copying data across process boundaries), and SIMD/vectorized operations. The standard guarantees that `memcpy` between two live trivially-copyable objects of the same type produces a valid copy.
