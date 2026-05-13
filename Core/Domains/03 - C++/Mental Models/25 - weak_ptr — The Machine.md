# weak_ptr — The Machine

## The Model

`weak_ptr<T>` is a non-owning observer of a `shared_ptr`-managed object. It holds a pointer to the control block (same as `shared_ptr`) but does NOT increment the strong count. The object can be destroyed while a `weak_ptr` still exists. To access the object, you call `lock()`, which atomically checks whether the object is still alive and — if so — returns a `shared_ptr` that temporarily holds ownership.

---

## Memory Layout

```
weak_ptr<Foo> on stack:
┌─────────────────────┐
│  object_ptr         │ → Foo instance (may be destroyed)
│  control_block_ptr  │ → control block (kept alive by weak_count)
└─────────────────────┘

Control block (shared with shared_ptr):
┌──────────────────┐
│  strong_count    │  atomic<int>  — weak_ptr does NOT increment this
│  weak_count      │  atomic<int>  — weak_ptr INCREMENTS this
│  deleter         │
└──────────────────┘
```

**Key rule:** when `strong_count` hits 0, the object is destroyed but the control block lives on (held by `weak_count + 1`). When `weak_count` also hits 0, the control block itself is freed.

---

## How It Moves — Construction from shared_ptr

```cpp
shared_ptr<Foo> sp = make_shared<Foo>();  // strong=1, weak=1
weak_ptr<Foo>   wp = sp;                   // copy weak_ptr
```

```
weak_ptr constructor:
  → copy object_ptr (point to same Foo)
  → copy control_block_ptr
  → atomically increment weak_count: 1 → 2
  Cost: one atomic increment (~5ns)
  strong_count UNCHANGED: 1
```

---

## How It Moves — lock()

```cpp
if (auto sp = wp.lock()) {
    sp->doWork();  // safe: sp keeps Foo alive during this scope
}
```

```
lock():
  → atomic compare-and-swap:
      if strong_count > 0: increment strong_count → return shared_ptr
      if strong_count == 0: object already gone → return empty shared_ptr
  Cost: one atomic CAS (~5-30ns)
```

The CAS is critical: without it, there's a race between `strong_count == 1` check and the increment — the last `shared_ptr` could be destroyed between the check and the increment.

---

## How It Moves — Destruction

```cpp
{
    weak_ptr<Foo> wp2 = sp;   // weak=3
}  // wp2 destroyed
```

```
weak_ptr destructor:
  → atomically decrement weak_count: 3 → 2
  → if weak_count == 0: free control block
  → does NOT touch strong_count
  → does NOT touch the Foo object
```

---

## The Cycle-Breaking Use Case

```cpp
// BROKEN: ref cycle — neither A nor B ever freed
struct Node {
    shared_ptr<Node> next;
    shared_ptr<Node> prev;  // BAD: both directions strong
};

shared_ptr<Node> a = make_shared<Node>();
shared_ptr<Node> b = make_shared<Node>();
a->next = b;  // a → b: strong
b->prev = a;  // b → a: strong → CYCLE

// When a and b go out of scope:
// a.strong_count would reach 0 only if b is destroyed first
// b.strong_count would reach 0 only if a is destroyed first
// Neither ever reaches 0 → memory leak
```

```cpp
// FIX: break the back-edge with weak_ptr
struct Node {
    shared_ptr<Node> next;   // forward: strong (child keeps alive)
    weak_ptr<Node>   prev;   // back: weak (doesn't prevent destruction)
};

// When a goes out of scope: a.strong_count → 0 → Foo destroyed
// b's weak_ptr prev is now expired — lock() returns empty
```

---

## The Observer Use Case

```cpp
class Cache {
    std::vector<weak_ptr<Texture>> textures_;
    
    void cleanup() {
        textures_.erase(
            std::remove_if(textures_.begin(), textures_.end(),
                [](const weak_ptr<Texture>& wp) { return wp.expired(); }),
            textures_.end());
    }
    
    void render() {
        for (auto& wp : textures_) {
            if (auto sp = wp.lock()) {
                sp->bind();  // safe: sp keeps Texture alive during bind()
            }
            // if expired: texture was freed elsewhere, skip it
        }
    }
};
```

The cache doesn't extend texture lifetime — textures are destroyed when their owning `shared_ptr`s (held elsewhere) go away. The cache sees expired `weak_ptr`s and cleans them up.

---

## expired() vs lock()

```cpp
if (!wp.expired()) {    // BAD: TOCTOU race
    auto sp = wp.lock();
    sp->doWork();       // sp might be empty — object destroyed between the two lines
}

if (auto sp = wp.lock()) {  // GOOD: atomic
    sp->doWork();
}
```

`expired()` is a racy check. The object can die between `expired()` returning false and the next line. Always use `lock()` and check the result.

---

## Hidden Costs

| Operation | Cost |
|---|---|
| `weak_ptr` construction from `shared_ptr` | 1 atomic increment (~5ns) |
| `weak_ptr` destruction | 1 atomic decrement (~5ns) |
| `lock()` | 1 atomic CAS (~5-30ns) |
| Control block kept alive by weak_ptr | Extra heap block until all weak_ptrs die |
| `make_shared` + `weak_ptr` | Control block outlives object (object + control block still one allocation, but object memory freed while control block persists in same allocation) |

---

## make_shared and weak_ptr — The Trade-off

`make_shared` merges Foo and the control block into one allocation. This is normally better (fewer allocs, better cache locality). But: when a `weak_ptr` outlives all `shared_ptr`s, the entire merged allocation stays alive until the last `weak_ptr` dies — even though Foo itself has been destroyed.

```
make_shared:    [Foo | control block] ← one block
                 Foo destroyed → control block still holds memory
                 Memory freed only when weak_count also hits 0

shared_ptr(new Foo):  [Foo] + [control block] ← two blocks
                 Foo destroyed → Foo's block freed immediately
                 control block freed when weak_count hits 0
```

If weak_ptrs are long-lived and Foo is large: `shared_ptr(new Foo)` may reclaim Foo's memory sooner.

---

## Related Machines

→ [[22 - shared_ptr — The Machine]]
→ [[01 - RAII — The Machine]]
→ [[04 - Atomics — The Machine]]
→ [[../Domains/03 - C++/Theory/02 - Smart Pointers]]
