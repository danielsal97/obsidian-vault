# shared_ptr — The Machine

## The Model

`shared_ptr<T>` is two pointers on the stack: one to the managed object, one to a control block. The control block lives on the heap and stores two reference counts: the strong count (number of `shared_ptr`s that keep the object alive) and the weak count (number of `weak_ptr`s + 1 for the strong count itself). When the strong count hits zero, the object is destroyed. When the weak count also hits zero, the control block is freed.

---

## Memory Layout

```
Stack:
┌─────────────────────┐
│  object_ptr         │ → Foo instance (heap)
│  control_block_ptr  │ → control block (heap)
└─────────────────────┘

Heap (two separate allocations, unless make_shared):

  Foo instance:
  ┌──────────────────┐
  │  Foo data...     │
  └──────────────────┘

  Control block:
  ┌──────────────────┐
  │  strong_count    │  atomic<int>
  │  weak_count      │  atomic<int>
  │  deleter         │  function ptr or lambda (how to delete Foo)
  │  allocator       │  (for custom allocators)
  └──────────────────┘
```

**`make_shared<T>` optimization**: allocates ONE block containing both the Foo instance AND the control block. Two heap allocations become one. Better cache locality (control block and object are adjacent). 

---

## How It Moves — Copy (increment strong count)

```cpp
shared_ptr<Foo> a = make_shared<Foo>();   // strong=1, weak=1
shared_ptr<Foo> b = a;                     // copy
```

```
Copy constructor:
  → copy object_ptr (point to same Foo)
  → copy control_block_ptr (point to same control block)
  → atomically increment strong_count: 1 → 2
Done. Foo is NOT copied. Cost: one atomic increment (~5ns, or 30-300ns under contention)
```

---

## How It Moves — Destruction (decrement strong count)

```cpp
{
    shared_ptr<Foo> b = a;  // strong=2
}  // b destroyed
```

```
Destructor:
  → atomically decrement strong_count: 2 → 1
  → if strong_count == 0:
      → call deleter(object_ptr): Foo::~Foo() runs, memory freed
      → atomically decrement weak_count: N → N-1
      → if weak_count == 0: free control block
  → if strong_count > 0: nothing more to do
```

---

## How It Moves — Move (no atomic operation)

```cpp
shared_ptr<Foo> b = std::move(a);
```

```
Move constructor:
  → copy object_ptr to b
  → copy control_block_ptr to b
  → set a.object_ptr = nullptr
  → set a.control_block_ptr = nullptr
  → NO atomic operations — count doesn't change
Done. Cost: 4 pointer assignments. ~1ns.
```

Prefer move over copy when transferring ownership. The atomic increment/decrement is the expensive part.

---

## Thread Safety — What Is and Isn't Protected

The **reference count** is always thread-safe (atomic operations). Multiple threads can copy/destroy `shared_ptr`s to the same object concurrently without data races.

The **pointed-to object** is NOT protected. Multiple threads accessing `*ptr` concurrently still need their own synchronization.

The **`shared_ptr` instance itself** is NOT thread-safe. You cannot safely copy from a `shared_ptr` on one thread while another thread destroys it. Use per-thread copies of `shared_ptr`.

---

## weak_ptr — Cycle Breaking

```cpp
shared_ptr<Node> a = make_shared<Node>();
shared_ptr<Node> b = make_shared<Node>();
a->next = b;   // a holds strong ref to b
b->prev = a;   // b holds strong ref to a → CYCLE: neither ever frees
```

```cpp
// Fix: weak_ptr does not increment strong_count
a->next = b;
b->prev = weak_ptr<Node>(a);   // weak: doesn't keep a alive
```

```
weak_ptr internals:
  → shares the same control block as the shared_ptr it was created from
  → does NOT increment strong_count
  → increments weak_count (keeps control block alive even after object dies)

weak_ptr::lock():
  → atomically: if strong_count > 0: increment strong_count, return shared_ptr
  → if strong_count == 0: object already destroyed, return empty shared_ptr
  Cost: one atomic CAS operation
```

---

## Hidden Costs

| Operation | Cost |
|---|---|
| `make_shared<T>()` | 1 allocation (object + control block) |
| `shared_ptr<T>(new T)` | 2 allocations (object separate from control block) |
| `shared_ptr` copy | 1 atomic increment (~5-300ns depending on contention) |
| `shared_ptr` move | 4 pointer assignments (~1ns) |
| `shared_ptr` destroy (last ref) | 1 atomic decrement + destructor + possibly free |
| `weak_ptr::lock()` | 1 atomic CAS |
| Control block cache miss | Object and control block may be on different cache lines (unless make_shared) |

**The atomic increment cost is the main reason to prefer `unique_ptr`** when ownership doesn't need to be shared. `unique_ptr` has zero overhead over a raw pointer.

---

## enable_shared_from_this

```cpp
class Foo : public std::enable_shared_from_this<Foo> {
    void callback() {
        auto self = shared_from_this();  // get shared_ptr to this
        // self keeps Foo alive during the async operation
    }
};
```

Without `enable_shared_from_this`: `shared_ptr<Foo>(this)` creates a NEW control block — independent from the existing one. Two control blocks, two strong counts: the object gets double-freed when both hit zero.

`enable_shared_from_this` stores a `weak_ptr<Foo>` inside Foo. `shared_from_this()` calls `lock()` on that weak_ptr, returning a `shared_ptr` that shares the ORIGINAL control block. Safe.

---

## Related Machines

→ [[01 - RAII — The Machine]]
→ [[21 - Move Semantics — The Machine (deep)]]
→ [[08 - malloc and free — The Machine]]
→ [[04 - Atomics — The Machine]]
→ [[02 - Smart Pointers]]
