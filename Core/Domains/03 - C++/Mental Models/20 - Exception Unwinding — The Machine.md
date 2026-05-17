# Exception Unwinding — The Machine

## The Model

When an exception is thrown, the C++ runtime walks backwards up the call stack, calling the destructor of every local object in every stack frame, until it finds a matching `catch` block. This is stack unwinding. It is deterministic and guaranteed — every RAII object that was constructed will be destroyed, even if the exception propagates through 20 frames.

The unwind tables are pre-computed at compile time. The runtime does NOT inspect the stack at throw-time — it consults `.eh_frame` (or `.gcc_except_table`) metadata embedded in the binary.

---

## How It Moves — Throw and Catch

```cpp
void third() {
    FileHandle fh("log.txt");   // RAII: fd opened
    throw std::runtime_error("disk full");
}

void second() {
    std::string s = "buffer";   // RAII: heap allocation
    third();                     // exception propagates up
}

void first() {
    try {
        second();
    } catch (const std::runtime_error& e) {
        // handle
    }
}
```

```
[1] throw std::runtime_error("disk full") in third()
      │
      ▼
C++ runtime: __cxa_throw()
  → allocates exception object on exception heap
    (separate from stack — must survive stack unwinding)
  → stores exception type info + value
  → begins unwinding

[2] Unwind third()'s frame:
  → runtime consults .eh_frame for third()'s return address
  → .eh_frame encodes: "FileHandle fh was constructed, destroy it on unwind"
  → calls FileHandle::~FileHandle()   ← fd closed here, even under exception
  → pops third()'s frame

[3] Unwind second()'s frame:
  → consults .eh_frame for second()
  → "std::string s was constructed, destroy it on unwind"
  → calls std::string::~string()      ← heap buffer freed
  → checks: does second() have a matching catch? No.
  → pops second()'s frame

[4] Enter first()'s frame:
  → checks: does first() have a matching catch? Yes: catch(runtime_error)
  → does thrown type match? runtime_error IS-A runtime_error: yes
  → stack unwinding STOPS here
  → catch block executes with reference to exception object
  → after catch block: __cxa_end_catch() frees exception object
```

---

## The .eh_frame Table

Every function that has local objects with destructors gets entries in the `.eh_frame` section (DWARF unwind info). The entry records:

- Register save/restore instructions for each PC range in the function
- Which objects need destructors and at which stack offsets
- Which stack frame to clean up

At throw time, the runtime walks the call stack using this metadata — NO overhead during normal execution. This is the "zero-cost exception" model: exceptions have zero runtime cost until they're thrown.

---

## Exception Safety Levels

**Basic guarantee**: if an exception is thrown, the program remains in a valid (but possibly modified) state. No resources are leaked. Example: `std::vector::push_back` that fails during copy — the vector may have been resized or not, but it's not corrupted.

**Strong guarantee**: if an exception is thrown, the operation has no effect — the program state is exactly as before. Example: `std::vector::push_back` with noexcept move constructor — either fully succeeds or fully fails with vector unchanged.

**No-throw guarantee**: the operation never throws. Marked `noexcept`. Example: destructors, `std::swap`, most move operations. Required for some operations (e.g. vector reallocation MUST use noexcept moves, or it falls back to copies).

---

## What Happens When a Destructor Throws

If a destructor throws while another exception is already propagating (during stack unwinding): `std::terminate()` is called immediately. The program dies.

This is why destructors MUST be `noexcept` (they are by default in C++11). Any resource cleanup in a destructor must complete without throwing — use error codes, log and ignore, or abort.

---

## noexcept — Not Just Documentation

```cpp
void f() noexcept { ... }
```

`noexcept` tells the compiler: "if anything inside f throws, call `std::terminate()`." 

This has real consequences:
- Stack unwinding is NOT needed for `noexcept` functions: compiler can eliminate `.eh_frame` entries
- Enables move-if-noexcept optimization in containers
- Generates smaller code (no landing pads for exception dispatch)

Test with: `noexcept(expression)` — evaluates to `true` if expression is noexcept.

---

## Cost of Exceptions

**Zero cost when not thrown**: `.eh_frame` tables are read-only metadata; they don't execute. The `try` block has no runtime overhead.

**Expensive when thrown**:
- `__cxa_throw`: heap allocation for exception object
- Unwinding each frame: linear walk through `.eh_frame` (cannot be cached)
- Destructor calls: proportional to number of objects in unwound frames
- Typical cost: 1μs to 100μs per thrown exception depending on stack depth

This is why exceptions are appropriate for truly exceptional conditions, not for normal control flow.

---

## Related Machines

→ [[01 - RAII — The Machine]]
→ [[02 - Smart Pointers — The Machine]]
→ [[09 - Exception Handling]]
→ [[05 - Linker — The Machine]]
