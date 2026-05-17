# Copy Elision — The Machine

## The Model

Copy elision is the compiler's license to construct an object directly in its final destination, skipping the copy or move constructor entirely. The source object is never created in a temporary location — it is built once, in place. Since C++17, two forms are **guaranteed** by the standard; others are optional but universal in practice.

---

## The Three Forms

### RVO — Return Value Optimization (guaranteed, C++17)

```cpp
std::string make_greeting() {
    return std::string("hello");  // prvalue
}

std::string s = make_greeting();
```

```
Without RVO:
  1. Construct std::string("hello") as temporary on stack
  2. Move-construct s from temporary
  3. Destroy temporary
  Total: 1 construction + 1 move + 1 destruction

With RVO (C++17 mandatory for prvalue):
  1. Construct std::string("hello") directly in s's memory
  Total: 1 construction, nothing else
```

The temporary **never exists**. The compiler sees a prvalue return (an unnamed temporary constructed at the return site) and materializes it directly in the caller's stack slot. This is mandated by C++17 — the move constructor is not even called, even if it has side effects.

### NRVO — Named Return Value Optimization (optional, universal in practice)

```cpp
std::string make_greeting() {
    std::string result = "hello";  // named local variable
    return result;                 // NRVO
}

std::string s = make_greeting();
```

```
Without NRVO:
  1. Construct result on stack
  2. Move-construct return slot from result
  3. Destroy result
  4. Move-construct s from return slot
  Total: 1 construction + 2 moves + 1 destruction

With NRVO (not mandated, but every major compiler does it):
  1. Construct result directly in s's memory
  Total: 1 construction
```

The compiler allocates `result` at the address of `s` in the caller. When `return result` executes, no copy or move happens — `result` IS `s`.

NRVO can be suppressed: multiple return paths returning different named locals, returning a reference, or marking the function `[[clang::optnone]]`.

### Throw/Catch Copy Elision (optional)

```cpp
void f() {
    MyException ex;
    throw ex;  // compiler may elide the copy into the exception storage
}
```

The compiler may construct the exception object directly in the exception storage allocated by `__cxa_throw`, skipping the copy from `ex`.

---

## When NRVO Is Suppressed — Fallback to Move

```cpp
std::string choose(bool flag) {
    std::string a = "hello";
    std::string b = "world";
    return flag ? a : b;  // NRVO impossible: two different objects
}
```

Compiler cannot use NRVO (it doesn't know at compile time which variable to alias to the return slot). Falls back to: `std::move` of the chosen variable into the return slot. Cost: one move constructor, not zero.

---

## What This Means in Practice

```cpp
// These are ALL the same cost (one construction):
std::vector<int> f1() { return std::vector<int>(1000, 0); }  // RVO
std::vector<int> f2() { std::vector<int> v(1000, 0); return v; }  // NRVO
std::vector<int> f3() { return {}; }  // RVO

// WRONG optimization — prevents elision:
std::vector<int> f4() {
    std::vector<int> v(1000, 0);
    return std::move(v);  // explicit move DISABLES NRVO — forces a move instead of elision
}
```

**Never `std::move` a local variable in a return statement.** It disables NRVO and forces a move where the compiler would have done zero-cost construction.

---

## Hidden Cost: When Move Constructor Is Not `noexcept`

Even when NRVO applies, if the compiler cannot elide (suppressed NRVO, multiple returns), it generates a move. If the move constructor is not `noexcept`, the compiler may fall back to a copy. See [[21 - Move Semantics — The Machine (deep)]] — `std::vector` uses `move_if_noexcept`.

---

## Hidden Costs Summary

| Case | Cost |
|---|---|
| RVO (prvalue return, C++17) | 1 construction, no move |
| NRVO (named local, not suppressed) | 1 construction, no move |
| NRVO suppressed (multiple returns) | 1 construction + 1 move |
| `return std::move(local)` — wrong | 1 construction + 1 move (NRVO disabled) |
| Pass-by-value argument, forwarded to field | 1 construction if caller passes rvalue, 0 extra |

---

## Related Machines

→ [[21 - Move Semantics — The Machine (deep)]]
→ [[17 - std::vector — The Machine]]
→ [[01 - RAII — The Machine]]
→ [[03 - Move Semantics]]
