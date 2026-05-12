# Smart Pointers

Smart pointers manage heap-allocated objects using RAII. They automatically delete the object when it's no longer needed. Never call `delete` manually in modern C++.

---

## unique_ptr — Sole Ownership

One owner. Non-copyable, movable. Destructor calls `delete`. Zero overhead vs raw pointer.

```cpp
auto p = std::make_unique<int>(42);   // allocate + construct
*p = 100;                              // dereference like a raw pointer
p.get();                               // get raw pointer (don't delete it)
p.reset();                             // delete and set to nullptr
p.release();                           // give up ownership — caller must delete

// Move ownership:
auto q = std::move(p);   // p is now nullptr, q owns the object
```

**Array form:**
```cpp
auto arr = std::make_unique<int[]>(100);   // allocate array
arr[5] = 99;
```

**When to use:** default choice for heap allocation. One clear owner, lifetime matches the owner's scope.

---

## shared_ptr — Shared Ownership

Multiple owners. Reference-counted — destructor decrements count; when count reaches 0, deletes. Slightly heavier than `unique_ptr` (atomic ref count).

```cpp
auto a = std::make_shared<int>(42);   // count = 1
auto b = a;                            // count = 2
auto c = a;                            // count = 3
b.reset();                             // count = 2
c.reset();                             // count = 1
// when a goes out of scope: count = 0 → delete
```

**Use case:** ownership is genuinely shared — multiple parts of the code hold a reference, and you don't know statically which one will be last.

**LDS example:** `shared_ptr<DriverData>` — the driver creates it, InputMediator holds it, LocalStorage holds it while processing. Any of them could be last to release.

---

## weak_ptr — Non-Owning Observer

Observes a `shared_ptr` without contributing to the ref count. Must be "locked" (upgraded to `shared_ptr`) before use. Returns `nullptr` if the object was already deleted.

```cpp
std::shared_ptr<int> sp = std::make_shared<int>(42);
std::weak_ptr<int> wp = sp;

// Later, check if still alive:
if (auto locked = wp.lock()) {
    // locked is a shared_ptr — object is alive
    *locked = 100;
} else {
    // object was deleted
}
```

**Primary use: break reference cycles.**

```cpp
// Cycle — A owns B, B owns A → neither is ever deleted:
struct A { std::shared_ptr<B> b; };
struct B { std::shared_ptr<A> a; };   // cycle — leak

// Fix — B uses weak_ptr:
struct B { std::weak_ptr<A> a; };     // no cycle — A is freed when its external owners release
```

---

## make_unique vs make_shared vs new

Always prefer `make_unique` / `make_shared` over calling `new` directly:

```cpp
// Bad — two separate allocations:
std::shared_ptr<int> p(new int(42));

// Good — one allocation (control block + object together):
auto p = std::make_shared<int>(42);
```

`make_shared` is also safer — `new` in a complex expression can leak if an exception is thrown between the `new` and the constructor of `shared_ptr`.

---

## Custom Deleters

When the resource isn't heap memory:

```cpp
// File descriptor:
auto fd_guard = std::unique_ptr<int, void(*)(int*)>(
    new int(open("file.txt", O_RDONLY)),
    [](int* fd){ close(*fd); delete fd; }
);

// Cleaner with a deleter struct:
struct FdDeleter {
    void operator()(int* fd) const { close(*fd); delete fd; }
};
std::unique_ptr<int, FdDeleter> fd(new int(open("file.txt", O_RDONLY)));
```

---

## Ownership Rules

| Situation | Use |
|---|---|
| One owner, stack-like lifetime | `unique_ptr` |
| Shared ownership, unknown last owner | `shared_ptr` |
| Need to observe without owning | `weak_ptr` |
| Non-owning observation, lifetime guaranteed | raw pointer or reference |
| Old API requires raw pointer | `.get()` then don't delete |

---

## Performance

| Type | Size | Overhead |
|---|---|---|
| Raw pointer | 8 bytes | none |
| `unique_ptr` | 8 bytes | none (destructor calls delete) |
| `shared_ptr` | 16 bytes | atomic ref count increment/decrement |
| `weak_ptr` | 16 bytes | atomic ref count check |

`unique_ptr` is truly zero overhead — in release builds it compiles to exactly the same code as a raw pointer with `delete`.

---

## Common Mistakes

**Giving a raw pointer to two unique_ptrs:**
```cpp
int* raw = new int(42);
unique_ptr<int> a(raw);
unique_ptr<int> b(raw);   // double delete — undefined behavior
```

**Circular shared_ptr:**
```cpp
// A and B keep each other alive forever — use weak_ptr to break the cycle
```

**Holding a raw pointer from a shared_ptr after it might expire:**
```cpp
int* raw = sp.get();
sp.reset();          // object deleted
*raw = 5;            // use-after-free
```

---

## Understanding Check

> [!question]- Why is `unique_ptr` truly zero-overhead while `shared_ptr` has a measurable cost, even though both call `delete` in their destructor?
> `unique_ptr` stores only the raw pointer; its destructor is a direct `delete` call that inlines to nothing in release builds — identical to manual memory management. `shared_ptr` carries a second pointer to a separately-allocated control block containing an *atomic* reference count. Every copy, reset, or destruction must atomically increment or decrement this count, which requires a full memory barrier — expensive on multi-core systems under contention. In LDS the `DriverData` shared_ptr crosses thread boundaries, so every handoff between the driver thread and the worker thread pays this atomic cost.

> [!question]- What goes wrong if you construct two separate `unique_ptr`s from the same raw pointer?
> Both will believe they are the sole owner. When the first goes out of scope it calls `delete` on the address. The second's destructor later calls `delete` on the same address — a double-free, which is undefined behavior. It typically corrupts the heap allocator's free list and causes a crash or silent data corruption elsewhere. The fix is to never construct a smart pointer from a raw pointer you don't own outright; use `make_unique`/`make_shared` exclusively.

> [!question]- Why must you call `wp.lock()` before using a `weak_ptr`, and what would happen if you dereferenced it directly?
> `weak_ptr` does not own the object; the object can be destroyed by the last `shared_ptr` owner at any moment, even between the check and the use. `lock()` atomically elevates the `weak_ptr` to a `shared_ptr` — if the object is still alive the ref count is incremented, guaranteeing it stays alive for the duration of your use. Without `lock()` there is no such guarantee, so direct dereference would be a use-after-free race condition. In LDS, any observer pattern that holds a `weak_ptr` to a subscriber must `lock()` before dispatching.

> [!question]- What goes wrong if two `shared_ptr` objects form a reference cycle and you never use `weak_ptr`?
> Each object keeps the other's ref count at ≥ 1. When all *external* owners release their handles, both ref counts drop to 1 (not 0). Neither destructor is ever called — the objects live forever, leaking memory for the process lifetime. In LDS, if a subscriber held a `shared_ptr` back to the `Dispatcher`, and the `Dispatcher` held a `shared_ptr` to the subscriber, neither would destruct on shutdown. The fix is for the non-owning side to use `weak_ptr`.

> [!question]- Why does `make_shared` outperform `shared_ptr<T>(new T(...))` in both allocation count and exception safety?
> `shared_ptr<T>(new T(...))` performs two heap allocations: one for `T` and one for the control block. `make_shared` fuses them into a single allocation. On exception safety: in an expression like `f(shared_ptr<T>(new T()), g())`, if `g()` throws after `new T()` runs but before the `shared_ptr` constructor completes, `T` leaks — there is no smart pointer yet to clean it up. `make_shared` is a single expression with no such gap.
