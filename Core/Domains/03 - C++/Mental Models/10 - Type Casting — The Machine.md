# Type Casting — The Machine

## The Model
Four tools for reinterpreting objects, each with different safety guarantees. From safest to most dangerous: `static_cast` (compile-time check) → `dynamic_cast` (runtime check) → `const_cast` (removes protection) → `reinterpret_cast` (raw bit reinterpretation, no checks). C-style cast `(T)x` silently picks any of the four — the dangerous one.

## How It Moves

```
STATIC_CAST — compile-time check:
  IDriverComm* base = new NBDDriverComm();
  NBDDriverComm* nbd = static_cast<NBDDriverComm*>(base);
  // compiler verifies: IDriverComm and NBDDriverComm are related
  // no runtime check — if base actually points to TCPDriverComm → UB (wrong vtable)

DYNAMIC_CAST — runtime check (requires virtual functions):
  NBDDriverComm* nbd = dynamic_cast<NBDDriverComm*>(base);
  // walks the vtable at runtime to verify actual type
  if (nbd == nullptr) { /* base is not actually NBDDriverComm */ }
  // returns nullptr (pointer) or throws std::bad_cast (reference)

CONST_CAST — remove const qualifier:
  const int* cp = &x;
  int* p = const_cast<int*>(cp);   // removes const — only safe if original was non-const

REINTERPRET_CAST — raw bits, no interpretation:
  uint32_t* ip = reinterpret_cast<uint32_t*>(char_buffer);
  // treats char_buffer's bytes AS a uint32_t — violates strict aliasing, use memcpy instead
```

## The Blueprint

**When to use each:**
| Cast | Use when |
|---|---|
| `static_cast` | Converting between related types, numeric conversions, `void*` |
| `dynamic_cast` | Downcasting with runtime type verification (rare — prefer design) |
| `const_cast` | Passing a const object to a legacy API that takes non-const (read-only) |
| `reinterpret_cast` | Memory layout inspection, byte manipulation — with explicit care |

**The C-style cast problem:**
```cpp
IDriverComm* base = new TCPDriverComm();
NBDDriverComm* nbd = (NBDDriverComm*)base;   // compiles — picks static_cast
                                              // UB: base actually points to TCPDriverComm
// vs:
NBDDriverComm* nbd = dynamic_cast<NBDDriverComm*>(base);   // returns nullptr safely
```

## Where It Breaks

- **`static_cast` for wrong downcast**: no runtime check → accesses wrong memory → UB
- **`reinterpret_cast` instead of `memcpy`**: strict aliasing violation → compiler assumes the pointer types never alias → optimizes away reads/writes → UB
- **`const_cast` and then writing**: if the original object was declared `const`, writing to it via `const_cast` is UB

## In LDS

`services/communication_protocols/nbd/src/NBDDriverComm.cpp`

NBD protocol parsing reads raw bytes into a `char*` buffer. To interpret bytes as a `uint32_t` (e.g., the request length field), the correct approach is `memcpy` (not `reinterpret_cast`) to avoid strict aliasing UB:
```cpp
uint32_t len;
memcpy(&len, buf + 20, sizeof(uint32_t));   // safe
len = ntohl(len);
```
`reinterpret_cast<uint32_t*>(buf + 20)` would compile but produces UB — the compiler can assume the `char*` and `uint32_t*` don't alias and may optimize the read away.

## Validate

1. `InputMediator` holds `IDriverComm* m_driver`. You want to call `NBDDriverComm::SetBlockDevice()`, which is not in `IDriverComm`. When should you use `dynamic_cast` vs `static_cast` here?
2. A function takes `const Request& req` but you need to pass it to a legacy C API that takes `Request*`. Is `const_cast` safe here? What is the one condition where it's UB?
3. Why is `*(uint32_t*)(char_buffer)` UB but `memcpy(&val, char_buffer, 4)` is not — they read the same 4 bytes?

## Connections

**Theory:** [[10 - Type Casting]]  
**Mental Models:** [[Inheritance — The Machine]], [[Virtual Functions — The Machine]], [[Undefined Behavior — The Machine]], [[Serialization — The Machine]]  
**LDS Implementation:** [[LDS/Linux Integration/NBDDriverComm]] — memcpy over reinterpret_cast for protocol parsing
