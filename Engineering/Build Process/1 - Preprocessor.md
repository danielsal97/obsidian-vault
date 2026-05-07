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
