# Undefined Behavior

Undefined behavior (UB) means the C/C++ standard places no requirements on what the program does. The compiler is free to generate any code — crash, silent wrong result, data corruption, or appear to work correctly in debug mode and fail in release.

---

## Why UB Exists

C trusts the programmer and assumes they won't violate the rules. In return, the compiler can assume those rules are never violated and optimize aggressively. If you break the rules, all bets are off.

Example: the compiler assumes signed integer overflow never happens. It uses this to eliminate "impossible" branches. If overflow does happen, the eliminated branch was load-bearing code.

---

## Common Sources of UB

**Signed integer overflow:**
```c
int x = INT_MAX;
x + 1;   // UB — signed overflow is undefined in C
         // unsigned overflow wraps around (defined)

// Compiler may assume x+1 > x is always true and remove checks
```

**Out-of-bounds array access:**
```c
int arr[5];
arr[5] = 0;    // UB — one past the end
arr[-1] = 0;   // UB
```

**Use-after-free:**
```c
int* p = malloc(4);
free(p);
*p = 5;   // UB
```

**Dereferencing null:**
```c
int* p = NULL;
*p = 5;   // UB — usually segfault, but not guaranteed
```

**Uninitialized read:**
```c
int x;
printf("%d\n", x);   // UB — x contains whatever was on the stack
```

**Signed left shift overflow:**
```c
int x = 1 << 31;   // UB if int is 32 bits — result is INT_MIN territory
```

**Strict aliasing violation:**
```c
int i = 5;
float* fp = (float*)&i;
*fp = 3.14f;   // UB — accessing int memory through float* violates aliasing rules
// Exception: char* and void* can alias anything
```

**Data race:**
```c
// Two threads accessing the same variable without synchronization
// Result is undefined — not just "wrong value"
```

**Modifying a string literal:**
```c
char* s = "hello";
s[0] = 'H';   // UB — string literals are read-only
```

---

## Why It's Dangerous

UB doesn't always crash. It may:
- Work correctly in debug mode (`-O0`), fail in release (`-O2`)
- Work on x86, fail on ARM
- Work today, fail after a compiler update
- Corrupt unrelated memory silently

**Classic example — compiler eliminates null check:**
```c
void f(int* p) {
    *p = 5;         // if p is null, this is UB
    if (p == NULL)  // compiler: "p must not be null (UB above proves it),
        abort();    // so this branch is dead code" → eliminates the check
}
```

---

## Tools to Catch UB

**UBSan (Undefined Behavior Sanitizer):**
```bash
g++ -fsanitize=undefined -g program.cpp -o program
./program
# prints: runtime error: signed integer overflow
```

Catches: integer overflow, null dereference, misaligned access, out-of-bounds, invalid enum.

**ASan catches:** use-after-free, buffer overflow, use-after-return.

**Valgrind catches:** uninitialized reads, memory errors.

**Compile with warnings:**
```bash
g++ -Wall -Wextra -pedantic-errors
```

---

## Implementation-Defined vs Undefined

**Implementation-defined:** the behavior is unspecified but the compiler must document it. Predictable on a given platform.
```c
sizeof(int)          // 4 on most 64-bit platforms (not guaranteed by standard)
-1 >> 1              // arithmetic right shift on most compilers (not guaranteed)
```

**Unspecified:** the standard allows several behaviors, compiler chooses, no documentation required.
```c
int i = 0;
f(i++, i++);   // order of argument evaluation is unspecified
```

**Undefined:** no valid behavior exists. Compiler can do anything.

---

## Understanding Check

> [!question]- Why does UB code often appear to work correctly at `-O0` (debug) but silently break at `-O2` (release)?
> At `-O0` the compiler does the minimum — it generates straightforward code that roughly mirrors the source, so many UB cases happen to produce the "expected" result. At `-O2` the compiler applies aggressive optimizations that are only valid assuming no UB exists. It may eliminate branches it proves are unreachable (because reaching them would require UB that it assumed cannot happen), reorder operations across what looked like a sequence point, or assume a value fits in a range. The bug was always there; the optimized build just exposed it by removing the "accidentally correct" scaffolding.

> [!question]- What goes wrong if you rely on signed integer overflow to detect an overflow condition, such as `if (a + b < a)`?
> The compiler sees that signed overflow is UB, therefore it assumes it never happens, therefore it treats `a + b` as always greater than or equal to `a` when `b >= 0`. The entire check gets optimized away — the very condition you wrote to catch the overflow is the thing the compiler removes. The correct approach is to check before the operation: `if (b > INT_MAX - a)` for addition, or use unsigned arithmetic (which wraps predictably), or use `__builtin_add_overflow` which checks without invoking UB.

> [!question]- The strict aliasing rule says you can't access an `int` through a `float*`. Why does C have this rule, and what is the one type that is always allowed to alias anything?
> Strict aliasing lets the compiler assume that two pointers of different types don't point to the same memory. This enables load/store reordering and caching values in registers — if `float* fp` and `int* ip` can't alias, a write through `fp` can't invalidate the cached value in `ip`. Without this rule, every pointer dereference would require re-reading from memory. The exception is `char*` (and `unsigned char*`): the standard explicitly allows `char*` to alias any type, which is how `memcpy`, serialization, and any byte-level inspection must be done.

> [!question]- In the LDS codebase, two threads access a shared `LocalStorage` map. Without a mutex, why is the data race not just a "wrong value" problem — why is it full undefined behavior?
> The C and C++ memory models define a data race as two concurrent accesses to the same variable where at least one is a write, with no synchronization. The standard declares this undefined behavior — not "returns a stale value" but truly UB with no guaranteed outcome. The compiler and CPU are free to reorder memory operations, cache values in registers, tear writes (write a 64-bit value in two non-atomic 32-bit stores), or speculate in ways that produce values that never existed in the source. A mutex doesn't just prevent wrong values — it establishes a happens-before relationship that makes the memory model's guarantees apply at all.

> [!question]- How can you use UBSan and ASan together in the same build, and what important class of bug does each catch that the other misses?
> You can combine them: `g++ -fsanitize=address,undefined -g`. ASan instruments memory accesses at runtime to catch spatial errors (buffer overflows, use-after-free, heap metadata corruption) and temporal errors (accessing freed memory). UBSan inserts checks for language-rule violations that aren't necessarily bad memory accesses: signed integer overflow, null pointer dereference, misaligned access, invalid enum value, and shift-count-out-of-range. A signed overflow that stays within mapped memory is invisible to ASan but caught by UBSan; a heap buffer overflow that doesn't corrupt anything dangerous is invisible to UBSan but caught by ASan. Running both gives much broader coverage.
