# Object Layout — The Machine

## The Model

Every C++ object occupies a contiguous region of memory. The compiler decides the exact byte layout at compile time, following ABI rules. Fields are placed in declaration order, but padding bytes are inserted between fields (and after the last field) to satisfy alignment requirements. The layout is fixed — changing it without recompiling all dependent code breaks the ABI.

---

## Alignment Rules

Every type has an alignment requirement: it must start at a memory address divisible by its alignment.

| Type | Size | Alignment |
|---|---|---|
| char | 1 | 1 |
| short | 2 | 2 |
| int | 4 | 4 |
| float | 4 | 4 |
| double | 8 | 8 |
| pointer | 8 (64-bit) | 8 |

A struct's alignment = its most-aligned member.

---

## How It Moves — Struct Layout

```cpp
struct Bad {
    char  a;     // offset 0, size 1
    // 7 bytes padding here (double needs 8-byte alignment)
    double b;    // offset 8, size 8
    char  c;     // offset 16, size 1
    // 7 bytes padding here (struct alignment = 8)
};
// sizeof(Bad) = 24
```

```cpp
struct Good {
    double b;    // offset 0, size 8
    char   a;    // offset 8, size 1
    char   c;    // offset 9, size 1
    // 6 bytes padding (struct alignment = 8)
};
// sizeof(Good) = 16
```

Same fields, different order, 33% smaller. The CPU can read `Good` in 2 cache lines where `Bad` might need 3.

---

## Struct with Virtual Functions

```cpp
class Foo {
    virtual void f();     // adds vptr
    int x;
    double y;
};
```

```
Memory layout:
Offset 0: vptr (8 bytes) → points to Foo's vtable
Offset 8: x (4 bytes, int)
Offset 12: 4 bytes padding (double needs 8-byte alignment)
Offset 16: y (8 bytes, double)
Total: 24 bytes
```

The `vptr` is always first (on most ABIs). It's invisible in the source code but costs 8 bytes per object, regardless of how many virtual functions exist.

---

## Inheritance Layout

```cpp
class Base {
    int base_field;    // 4 bytes
};

class Derived : public Base {
    double derived_field;   // 8 bytes
};
```

```
Derived memory layout:
Offset 0: base_field (4 bytes, from Base)
Offset 4: 4 bytes padding (double alignment)
Offset 8: derived_field (8 bytes)
Total: 16 bytes

Derived* == Base*  (same address, no adjustment needed for single inheritance)
```

A `Base*` pointing to a `Derived` object points at the SAME address. The Base subobject is at offset 0.

---

## Multiple Inheritance Layout

```cpp
class A { int a; };
class B { int b; };
class C : public A, public B { int c; };
```

```
C memory layout:
Offset 0: a (from A subobject)
Offset 4: b (from B subobject)
Offset 8: c (C's own field)
Total: 12 bytes

C* == A* (both point to offset 0 of C)
C* as B* requires POINTER ADJUSTMENT: add 4 (offset of B subobject)
```

`static_cast<B*>(ptr_to_C)` compiles to `ptr_to_C + 4`. The resulting pointer addresses the B subobject, not the C object start. This is why pointer comparison across multiple inheritance bases can be surprising.

---

## Empty Base Optimization (EBO)

```cpp
struct Empty {};
struct WithEmpty {
    Empty e;    // 0 bytes of data
    int x;
};
// sizeof(WithEmpty) = 4  (without EBO: would be 8, e gets 1 byte)
```

Empty structs get 1 byte minimum (so distinct objects have distinct addresses). But when used as a base class, the compiler applies EBO: the base takes zero space if it has no data members.

```cpp
struct Derived : Empty {
    int x;
};
// sizeof(Derived) = 4  (EBO eliminates Empty's byte)
```

This is why policy-based design and allocator-aware types inherit from their allocator/policy: EBO eliminates the overhead when the policy is stateless.

---

## Bit Fields

```cpp
struct Flags {
    unsigned int ready : 1;     // 1 bit at offset 0
    unsigned int error : 1;     // 1 bit at offset 1
    unsigned int mode  : 4;     // 4 bits at offset 2
    // 26 bits padding to fill the 32-bit int
};
// sizeof(Flags) = 4  (packed into one int)
```

Bit fields pack multiple boolean flags into one word. But: individual bit fields cannot be atomically read/written on most architectures — atomic operations work on full bytes/words. Also: layout is implementation-defined, not portable across compilers.

---

## Checking Layouts

```cpp
static_assert(sizeof(Foo) == 24);
static_assert(offsetof(Foo, y) == 16);
```

Use `pahole` (Linux tool) to dump the full layout of structs from a compiled binary, including padding holes — useful for finding structs that waste cache line space.

---

## Hidden Costs

- Padding wastes cache lines: `Bad` struct above wastes 14 bytes out of 24 — only 42% data density
- vptr costs 8 bytes per object: a vector of 1M small objects with one virtual function wastes 8MB on vptrs alone
- Cache line straddling: if a frequently-accessed field lands across a 64-byte cache line boundary, every access loads two cache lines

---

## Related Machines

→ [[18 - VTables — The Machine]]
→ [[../Domains/01 - Memory/Mental Models/01 - Process Memory Layout — The Machine]]
→ [[../Domains/01 - Memory/Mental Models/08 - Cache Hierarchy — The Machine]]
→ [[../Domains/02 - C/Mental Models/04 - Structs and Unions — The Machine]]
→ [[../Domains/03 - C++/Theory/06 - Virtual Functions]]
