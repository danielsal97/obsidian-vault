# Undefined Behavior — The Machine

## The Model
A contract breach that the compiler is legally allowed to exploit. The C++ standard says: if you do X, the program has undefined behavior — and the compiler is allowed to assume X never happens. It then optimizes based on that assumption, potentially deleting your safety checks because "you promised they'd never be needed."

## How It Moves

```
Your code:                         What you assumed:
───────────                        ─────────────────
int x = INT_MAX;                   x + 1 wraps to INT_MIN
int y = x + 1;
if (y > x) { ... }

What the compiler sees:
  "Signed integer overflow is UB. Therefore x + 1 > x is always true (by assumption).
   Therefore the if-branch is always taken. I'll delete the condition entirely."

Result: the safety check is optimized AWAY.
```

**This is not a crash. It's silent, legal optimization that produces wrong results.**

The compiler is not being malicious — it's being correct according to the standard. You violated the contract. The compiler used the violation to optimize. The result is undefined.

## The Blueprint

**Common UB sources:**
- **Signed integer overflow**: `INT_MAX + 1` — use `uint32_t` for arithmetic that might overflow
- **Out-of-bounds access**: `arr[n]` where n >= size — no bounds check in C arrays
- **Null/dangling pointer dereference**: access through a pointer that's NULL or freed
- **Use-after-free**: memory returned to allocator and then read
- **Strict aliasing violation**: `*(float*)(&my_int)` — casting a pointer to an incompatible type and dereferencing (use `memcpy` instead)
- **Data race**: two threads access shared data without synchronization, at least one writes
- **Uninitialized read**: `int x; std::cout << x;` — x is whatever bits were in that stack slot

**How to detect:**
- `-fsanitize=undefined` (UBSan): instruments every potential UB — catches it at runtime with a clear error message
- `-fsanitize=address` (ASan): catches out-of-bounds, use-after-free, double-free
- `-fsanitize=thread` (TSan): catches data races

## Where It Breaks

UB is uniquely dangerous because:
1. It may work correctly in debug builds (`-O0`) and break only in optimized builds (`-O2/-O3`)
2. The crash happens far from the UB — a corrupted pointer crashes 1000 instructions later
3. Sanitizers find it; valgrind finds memory errors; TSan finds races. Always test with these enabled.

## In LDS

`Makefile` — LDS has an ASan build target. Running `make asan` compiles with `-fsanitize=address,undefined`. This catches buffer overflows in the NBD protocol parser (writing past a received buffer) and use-after-free in the Reactor's event handler map.

The `LocalStorage::Read` function copies data to a caller-provided buffer. If the caller provides a buffer smaller than the requested length, the `memcpy` writes out of bounds — UB, silent in release builds, caught immediately by ASan.

## Validate

1. LDS sets `m_running = false` from a signal handler to stop the Reactor loop. The loop reads `m_running` without synchronization. This is a data race — UB. Why might it "work" in debug builds?
2. You index `m_data[offset + len]` in `LocalStorage` without checking `offset + len <= m_data.size()`. This is a potential out-of-bounds access. With `-O2`, what might the compiler do if it can prove `offset + len` is always in-bounds under your assumptions?
3. What command do you run to check LDS for UB right now?

## Connections

**Theory:** (cross-cutting — see C++ notes)  
**Mental Models:** [[Type Casting — The Machine]], [[Memory Ordering — The Machine]], [[Pointers — The Machine]], [[Strings — The Machine]]  
**LDS Implementation:** [[LDS/Debugging/Testing]] — ASan/UBSan build targets
