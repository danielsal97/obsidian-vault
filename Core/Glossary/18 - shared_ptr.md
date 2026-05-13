---
name: shared_ptr — Shared Ownership Smart Pointer
type: cpp
---

# shared_ptr — Shared Ownership Smart Pointer

**[cppreference →](https://en.cppreference.com/w/cpp/memory/shared_ptr)** | **[Wikipedia →](https://en.wikipedia.org/wiki/Smart_pointer#shared_ptr)**

A C++ smart pointer that implements shared ownership with reference counting. The managed object is destroyed automatically when the last `shared_ptr` holding it is destroyed or reset — no manual `delete` needed.

```cpp
auto ptr = std::make_shared<DriverData>();
// ref count = 1

{
    auto ptr2 = ptr;   // ref count = 2
}                      // ptr2 destroyed → ref count = 1

// ptr destroyed → ref count = 0 → DriverData deleted automatically
```

## In LDS — Zero-Copy DriverData Lifetime

`DriverData` (the struct carrying an NBD request: type, offset, length, data buffer) travels through the entire system as a single `shared_ptr<DriverData>`:

```
NBDDriverComm::ReceiveRequest()
  → make_shared<DriverData>()     ref count = 1
  → read nbd_request into it
  → return shared_ptr

InputMediator
  → passes to WriteCommand        ref count = 2
  → returns (handler frame pops)  ref count = 1

WriteCommand::Execute()           ref count = 1 (cmd owns it)
  → SendPutBlock(minionA, data)   ← reads buffer, no copy
  → SendPutBlock(minionB, data)   ← reads buffer, no copy
  → driver.SendReply(data)        ← reads handle field
  → Execute() returns             ref count = 0 → destroyed ✅
```

**The data buffer is allocated once and freed automatically. Zero copies of the payload.**

## vs. unique_ptr

| | `shared_ptr` | `unique_ptr` |
|---|---|---|
| Owners | Multiple | Exactly one |
| Overhead | Atomic ref count | None |
| Use when | Lifetime shared across threads | Single clear owner |

LDS uses `shared_ptr<DriverData>` because ownership transfers from the handler to the command and the command outlives the handler's stack frame.

## Connections

**Theory:** [[Core/Domains/03 - C++/Theory/02 - Smart Pointers]]  
**Mental Models:** [[Smart Pointers — The Machine]], [[RAII — The Machine]], [[Move Semantics — The Machine]]  
**LDS Implementation:** [[Decisions/Why RAII]] — the broader principle; [[Request Lifecycle]] — DriverData zero-copy lifecycle  
**Related Glossary:** [[RAII]], [[Templates]]
