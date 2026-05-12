# Stage 1 — Preprocessor

The preprocessor is a pure text processor. It runs before the compiler sees your code. It knows nothing about C or C++ syntax — it just manipulates text.

---

## What It Does

### #include — header insertion

```cpp
#include <stdio.h>         // system header — searches /usr/include
#include "myheader.h"      // user header — searches current dir first
```

The preprocessor literally copies the entire file contents in-place. After preprocessing, there are no `#include` lines — just raw text.

This is why large headers slow compilation. If `<windows.h>` is 50,000 lines, every `.cpp` that includes it processes 50,000 lines before the compiler starts.

→ What goes in headers: type definitions, function declarations, inline functions, templates.  
→ What belongs in `.cpp` only: function bodies, global variables.

See [[../C/Structs and Unions]] — struct definitions go in headers so every `.cpp` gets the same layout.  
See [[../C++/Templates]] — templates must be in headers (the compiler needs the full definition to instantiate).

---

### #define — text substitution

```cpp
#define MAX_BUFFER 1024
#define SQUARE(x) ((x) * (x))   // macro function — parenthesize everything

char buf[MAX_BUFFER];            // preprocessor replaces → char buf[1024]
int n = SQUARE(3 + 1);          // → ((3+1) * (3+1)) = 16, not SQUARE(3+1) = 7
```

`#define` is dumb string replacement — no type safety. In C++ prefer `const` variables and inline functions.

```cpp
constexpr int MAX_BUFFER = 1024;    // typed, scoped, debugger-visible
inline int square(int x) { return x * x; }  // real function
```

---

### Header Guards — prevent double inclusion

```cpp
// myheader.h
#ifndef MYHEADER_H
#define MYHEADER_H

// ... header contents ...

#endif
```

Without guards: if `a.h` includes `b.h`, and `main.cpp` includes both, `b.h` gets processed twice → redefinition errors.

Modern alternative — `#pragma once` (non-standard but universally supported):

```cpp
#pragma once
// ... header contents ...
```

---

### Conditional Compilation

```cpp
#ifdef DEBUG
    printf("debug: value = %d\n", x);   // only compiled in debug builds
#endif

#if defined(__linux__)
    // Linux-specific code
#elif defined(__APPLE__)
    // macOS-specific code
#endif
```

Used in build systems to compile different code per platform, or enable/disable logging.

---

### Predefined Macros

```cpp
__FILE__     // current filename as string literal
__LINE__     // current line number as integer
__func__     // current function name (C99/C++11)
__DATE__     // compilation date
__cplusplus  // defined in C++ (value = 201703L for C++17 etc)

// Useful for logging:
#define LOG(msg) fprintf(stderr, "[%s:%d] %s\n", __FILE__, __LINE__, msg)
```

---

## Viewing Preprocessor Output

```bash
g++ -E main.cpp -o main.i   # write to file
g++ -E main.cpp             # print to stdout
```

The output is a single translation unit — all headers inlined, all macros expanded. Every `.cpp` file produces one translation unit. Multiple translation units are compiled independently.

---

## Common Problems

**Macro side effects:**
```cpp
#define MAX(a, b) ((a) > (b) ? (a) : (b))
int x = MAX(i++, j++);   // i++ and j++ may evaluate twice — UB
```

**Missing header guard → multiple definition:**
```
// foo.h — no guard
struct Foo { int x; };

// main.cpp includes foo.h twice (via two different headers)
// → error: redefinition of 'struct Foo'
```

**Circular includes:**  
`a.h` includes `b.h`, `b.h` includes `a.h` → infinite recursion. Header guards break the cycle on the second inclusion, but the order dependency is still fragile. Use forward declarations instead where possible.

---

## Connection to Other Stages

→ [[2 - Compiler]] — the compiler receives the fully preprocessed translation unit. It never sees `#include` or `#define`.

---

## Understanding Check

> [!question]- Why must C++ templates be defined in headers, and what does this have to do with how the preprocessor works?
> Template instantiation happens at compile time, per translation unit. When the compiler sees std::vector<int> in main.cpp, it must generate the full vector<int> class body right there and then — it cannot defer to another translation unit. The preprocessor's job is to inline the header contents so that the compiler sees the complete template definition. If the template body were in a .cpp file instead, the compiler for main.cpp would only see the declaration, have no body to instantiate from, and emit an "undefined reference" error at link time. Headers make this work because the preprocessor copies the full template body into every translation unit that needs it.

> [!question]- What goes wrong if you define a non-inline function in a header file that is included by two .cpp files?
> The preprocessor copies the function body verbatim into both translation units. Each .cpp compiles it independently, producing a GLOBAL symbol with that function's name in both .o files. When the linker combines them it finds two definitions of the same symbol and errors with "multiple definition of 'foo'". The fix is to mark the function inline (which tells the linker to accept multiple identical copies and keep one) or to move the definition to a single .cpp file and keep only the declaration in the header.

> [!question]- Why is #define MAX(a,b) dangerous when called with MAX(i++, j++), and how does constexpr avoid this?
> The preprocessor is pure text substitution with no knowledge of C++ semantics. MAX(i++, j++) expands to ((i++) > (j++) ? (i++) : (j++)) — each operand is evaluated twice, so either i or j gets incremented twice depending on the comparison result. This is undefined behavior when the same variable is modified and read between sequence points. A constexpr function or template is a real function: arguments are evaluated exactly once before the call, subject to normal C++ evaluation rules, and the result is computed at compile time if all inputs are constant expressions.

> [!question]- What is the "static initialization order fiasco" and how does the local-static Singleton pattern avoid it?
> Global objects in different translation units are initialized before main() runs, but the C++ standard does not define the order of initialization across .cpp files. If global object A (in a.cpp) depends on global object B (in b.cpp) during its constructor, B may not yet be initialized — the constructor reads garbage. The local-static pattern (static Foo& instance() { static Foo f; return f; }) avoids this because initialization is triggered by the first call to instance(), which happens inside main() after all global constructors have run. The C++11 guarantee of thread-safe magic-static initialization makes this safe even from multiple threads.

> [!question]- In the LDS codebase, why would putting a platform-detection macro like #if defined(__linux__) in a header shared between the Mac client and the Linux server be preferable to duplicating the code in two separate .cpp files?
> Keeping platform-specific branches in one shared header means there is a single place to update when the interface changes — adding a new field, renaming a function, or fixing a bug touches one file instead of two. The preprocessor selects the right branch per translation unit at compile time with zero runtime overhead. Duplicating the code in two .cpp files risks the two copies diverging silently (different bug fixes, different struct layouts), and the Mac and Linux builds would compile successfully but behave differently at the protocol level. The header approach makes the divergence explicit and co-located.
