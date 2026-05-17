# Move Semantics — The Machine (deep)

## The Model

Move semantics transfers ownership of a resource from one object to another without copying the resource. The source object is left in a valid-but-empty state: it holds nothing, but its destructor can still safely run. On the CPU, a move of a `std::string` is three pointer-sized stores — not a byte-copy of the string data.

The compiler uses moves automatically whenever it can prove the source object will not be used again. Understanding when the compiler chooses move vs copy unlocks both performance and correctness.

---

## Memory View — Move vs Copy

```
String "hello world" (length 11):

BEFORE:
  a: { ptr → heap["hello world"], len=11, cap=16 }
  b: (uninitialized or empty)

AFTER COPY: b = a
  a: { ptr → heap["hello world"], len=11, cap=16 }  (unchanged)
  b: { ptr → NEW heap["hello world"], len=11, cap=16 }  (allocates 16 bytes, copies 11)
  Cost: malloc(16) + memcpy(11 bytes) + 3 pointer assignments

AFTER MOVE: b = std::move(a)
  a: { ptr = nullptr, len=0, cap=0 }  (gutted — valid but empty)
  b: { ptr → heap["hello world"], len=11, cap=16 }  (stole a's pointer)
  Cost: 3 pointer assignments (= 3 stores) + 3 zero-writes to a
  NO heap allocation. NO memcpy.
```

---

## How It Moves — The Four Cases

### Case 1: Explicit move with `std::move`

```cpp
std::string a = "hello";
std::string b = std::move(a);  // b constructed from rvalue reference to a
```

`std::move` does NOT move anything. It's a cast: `static_cast<std::string&&>(a)`. It tells the compiler "treat `a` as an rvalue — its resources can be stolen." The actual stealing happens in `string`'s move constructor.

After this: `a` is in a moved-from state. Still valid (can assign to it or let it destruct), but its content is unspecified (likely empty).

### Case 2: Return Value Optimization (RVO / NRVO)

```cpp
std::string make_string() {
    std::string result = "hello";
    return result;  // NRVO: result constructed directly in caller's space
}

std::string s = make_string();
```

With NRVO (Named Return Value Optimization): the compiler constructs `result` directly in the memory where `s` will live. No copy, no move — the object is built in-place. This is guaranteed since C++17 for some cases (RVO), and very likely for NRVO.

Without NRVO (suppressed by e.g. multiple return paths): the compiler generates a move from `result` into the return slot.

### Case 3: Automatic move from local about to be destroyed

```cpp
std::vector<int> f() {
    std::vector<int> v = {1, 2, 3};
    return v;  // compiler: v is about to die, implicitly move it
}
```

The compiler applies implicit move for return statements when: the returned object is a local variable of the same type as the return type. This is automatic — no `std::move` needed.

### Case 4: Move in containers during reallocation

```cpp
std::vector<std::string> v;
v.push_back(std::string("hello"));  // rvalue: moved into vector
// ... later: push_back triggers reallocation ...
// → existing elements are moved to new storage (if move is noexcept)
```

---

## The Five (Rule of Five)

If you define any of these, define all five:

| | What it does |
|---|---|
| Destructor | Clean up the resource |
| Copy constructor | Deep copy the resource |
| Copy assignment | Deep copy the resource (handle self-assign) |
| Move constructor | Steal the resource, leave source empty |
| Move assignment | Steal the resource, destroy old resource, handle self-assign |

If you define a custom destructor (because you own a resource), the compiler will NOT generate a move constructor — you get a copy constructor instead. Forgetting to define move operations on a resource-owning class silently falls back to copies.

---

## noexcept on Move — Why It Matters

```cpp
class Buffer {
public:
    Buffer(Buffer&& other) noexcept {  // MUST be noexcept
        ptr = other.ptr;
        other.ptr = nullptr;
    }
};
```

`std::vector` reallocation uses `std::move_if_noexcept`: if the move constructor is `noexcept`, it moves. If not, it copies (to preserve the strong exception guarantee — if a move throws halfway through, the old elements are in gutted states with no recovery).

**If your move constructor is not `noexcept`, `vector<YourType>` silently copies instead of moves on reallocation.** This is the single most common performance trap in C++ containers.

---

## What std::forward Does (Perfect Forwarding)

```cpp
template<typename T>
void wrapper(T&& arg) {
    inner(std::forward<T>(arg));  // forward preserves lvalue/rvalue category
}
```

`T&&` in a template is a **forwarding reference** (also called universal reference). `T` deduces to `X&` if called with an lvalue, or `X` if called with an rvalue.

`std::forward<T>(arg)`: if T is `X&` (lvalue was passed), forward returns `X&` (lvalue). If T is `X` (rvalue was passed), forward returns `X&&` (rvalue). It preserves the original value category.

Without `forward`: `arg` is always treated as an lvalue inside `wrapper` (named variables are lvalues, even if their type is `X&&`). Using `forward` ensures that an rvalue passed to `wrapper` is also seen as an rvalue by `inner`, enabling move semantics to work through the wrapper.

---

## Moved-From State — The Contract

After a move, the source is in a "valid but unspecified" state. This means:
- Its destructor can run safely (no double-free, no null dereference)
- Its value is unspecified — do not READ from a moved-from object

Common implementations: `std::string` becomes empty, `std::unique_ptr` becomes nullptr, `std::vector` becomes empty. The standard ONLY guarantees the destructor runs safely.

---

## Related Machines

→ [[02 - Smart Pointers — The Machine]]
→ [[17 - std::vector — The Machine]]
→ [[01 - RAII — The Machine]]
→ [[20 - Exception Unwinding — The Machine]]
→ [[03 - Move Semantics]]
