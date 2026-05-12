# Operator Overloading — The Machine

## The Model
Defining what the machine does when you press a button. `+` on a string = concatenate. `[]` on a map = lookup. `<<` on a stream = serialize. `==` on a struct = compare fields. Every operator is a function call in disguise — `a + b` compiles to `operator+(a, b)` or `a.operator+(b)`.

## How It Moves

```
a + b   → a.operator+(b)   or   operator+(a, b)
a == b  → a.operator==(b)
a < b   → a.operator<(b)
a[i]    → a.operator[](i)
*ptr    → ptr.operator*()
```

**The compiler substitution:** when you write `request1 < request2`, the compiler looks for `operator<` on the `Request` type. If it finds it, it substitutes the call. If not, compile error. The substitution is purely mechanical — no magic.

## The Blueprint

```cpp
struct Request {
    uint32_t priority;
    uint64_t id;
    
    // Comparison for priority_queue (heap ordering):
    bool operator<(const Request& other) const {
        return priority < other.priority;   // smaller priority = lower in heap
    }
    
    // Equality:
    bool operator==(const Request& other) const {
        return id == other.id;
    }
    
    // Stream output (friend: takes stream as first arg):
    friend std::ostream& operator<<(std::ostream& os, const Request& r) {
        return os << "Request{id=" << r.id << ", pri=" << r.priority << "}";
    }
};

// C++20 spaceship — generates all 6 comparisons automatically:
auto operator<=>(const Request&) const = default;
```

**Rules:**
- Operators that must be members: `=`, `[]`, `()`, `->`
- Operators best as non-members (for symmetric behavior): `+`, `-`, `==`, `<`
- Never overload `&&`, `||`, `,` — they lose short-circuit evaluation

## Where It Breaks

- **`operator=` not self-assignment safe**: `a = a` → if you free a's memory before copying from `other`, and `other == a`, you just freed the data you're about to copy
- **Inconsistent operators**: defining `==` but not `!=`, or `<` but not `>` — use C++20 `<=>` to generate all at once
- **`operator[]` without bounds check**: returns a reference to an element — writing past the end is UB

## In LDS

`utilities/thread_safe_data_structures/priority_queue/include/wpq.hpp`

The WPQ stores tasks ordered by priority. To work with `std::priority_queue`, the task type needs `operator<` (or a custom comparator). Tasks with higher priority value should bubble to the top — the heap uses `operator<` to decide ordering. WRITE=2 > READ=1 > FLUSH=0: a WRITE task compares `>` all others, so it rises to the top of the heap.

## Validate

1. `std::priority_queue<Task>` uses `operator<`. You want WRITE tasks at the top (highest priority). Should `operator<` return `true` when left has LOWER or HIGHER priority than right?
2. You define `operator==` for `Request` but not `operator!=`. C++20 code writes `req1 != req2`. Does it compile? Why?
3. `request[5]` — `Request` doesn't define `operator[]`. What is the compile error, and could you add `operator[]` to make it work for accessing the 5th byte of the serialized request?

## Connections

**Theory:** [[Core/Theory/C++/Operator Overloading]]  
**Mental Models:** [[STL Containers — The Machine]], [[Smart Pointers — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Utilities Framework]] — WPQ task ordering via operator<
