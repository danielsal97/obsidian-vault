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
