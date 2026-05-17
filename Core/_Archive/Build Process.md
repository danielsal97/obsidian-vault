# Build Process

How source code becomes a running binary.

---

## The Pipeline

```
source.cpp
    │
    ▼ Preprocessor (cpp)
    │  - Expand #include, #define, #ifdef
    │  - Output: pure C++ text
    │
    ▼ Compiler (g++)
    │  - Parse C++ → check types → optimize → generate assembly
    │  - Output: assembly (.s)
    │
    ▼ Assembler (as)
    │  - Assembly → machine code
    │  - Output: object file (.o)
    │
    ▼ Linker (ld)
    │  - Combine .o files + libraries
    │  - Resolve symbols (find definition of every function called)
    │  - Output: executable or shared library
    │
    ▼ ./program
```

Each `.cpp` file compiles independently into a `.o`. The linker connects them.

---

## Object Files

A `.o` file contains:
- Machine code for functions defined in that `.cpp`
- A symbol table: which symbols it **defines** and which it **needs** (undefined references)
- Relocation info: placeholders where the linker fills in addresses

```bash
nm file.o          # list symbols: T = defined, U = undefined (needs linking)
objdump -d file.o  # disassemble
```

---

## Static vs Shared Libraries

**Static library (`.a`):**
- Archive of `.o` files
- Linked at build time — code is copied into the executable
- Executable is self-contained, no runtime dependency
- Larger binary, no sharing between processes

```bash
ar rcs libfoo.a foo.o bar.o     # create
g++ main.cpp -L. -lfoo -o app   # link
```

**Shared library (`.so` on Linux, `.dylib` on Mac):**
- Linked at load time (or runtime with `dlopen`)
- Code stays in the `.so`, not copied into executable
- Multiple processes share one copy in memory
- Smaller executables, but `.so` must be present at runtime

```bash
g++ -fPIC -shared foo.cpp -o libfoo.so    # create
g++ main.cpp -L. -lfoo -Wl,-rpath,. -o app  # link
```

`-fPIC` — Position Independent Code. Required for shared libraries because the code may be loaded at any address.

`-Wl,-rpath,.` — bakes the `.so` search path into the binary so `LD_LIBRARY_PATH` isn't needed.

---

## Dynamic Loading at Runtime

`dlopen` / `dlsym` — load a `.so` at runtime, look up a symbol by name.

```cpp
void* handle = dlopen("plugin.so", RTLD_LAZY);
auto fn = (int(*)())dlsym(handle, "my_function");
fn();
dlclose(handle);
```

Used in LDS for the plugin system — drop a `.so` into a directory, it gets loaded without restarting the server.

---

## Common Compiler Flags

| Flag | Effect |
|---|---|
| `-Wall -Wextra` | Enable most warnings |
| `-pedantic-errors` | Treat all warnings as errors, strict standard compliance |
| `-std=c++20` | Use C++20 standard |
| `-g` | Include debug symbols (for gdb/valgrind) |
| `-O0` | No optimization (default, best for debugging) |
| `-O2` | Standard optimization (production) |
| `-fPIC` | Position-independent code (required for .so) |
| `-shared` | Build a shared library |
| `-fsanitize=address` | Enable AddressSanitizer |
| `-fsanitize=undefined` | Enable UBSanitizer |

---

## GNU Make

Make tracks dependencies between files and only rebuilds what changed.

```makefile
# Rule: target: dependencies
#           recipe (must be tab-indented)

app: main.o util.o
	g++ main.o util.o -o app

main.o: main.cpp
	g++ -c main.cpp -o main.o

clean:
	rm -f *.o app
```

**Auto-discovery of source files:**
```makefile
SRC := $(shell find src -name "*.cpp")
OBJ := $(SRC:.cpp=.o)
```

**Phony targets** (not real files):
```makefile
.PHONY: clean run
```

---

## Header Guards

Without guards, including a header twice causes "redefinition" errors:

```cpp
#ifndef __MYCLASS_HPP__
#define __MYCLASS_HPP__

class MyClass { ... };

#endif
```

Or use `#pragma once` (non-standard but universally supported):
```cpp
#pragma once
class MyClass { ... };
```

---

## Linker Errors vs Compiler Errors

**Compiler error** — syntax/type error in a single `.cpp`:
```
error: 'foo' was not declared in this scope
```
Fix: wrong syntax, missing include, typo.

**Linker error** — symbol defined nowhere or defined twice:
```
undefined reference to 'MyClass::Method()'
```
Fix: forgot to compile/link the `.cpp` that defines it, or forgot `-lfoo`.

```
multiple definition of 'globalVar'
```
Fix: variable defined in a header (not just declared) — use `extern` in header, define in one `.cpp`.

---

## Useful Tools

```bash
ldd ./program          # list shared libraries the binary depends on
nm ./program           # list symbols
objdump -d ./program   # disassemble
size ./program         # show segment sizes (text, data, bss)
strings ./program      # extract readable strings
strace ./program       # trace syscalls at runtime
```

---

## Deep Dives

For internals of each stage (symbol tables, ELF format, optimization passes, relocation entries):
- [[01 - Preprocessor]] — #include expansion, #define, header guards, conditional compilation
- [[02 - Compiler]] — parsing, type checking, optimization levels, template instantiation
- [[03 - Assembler]] — ELF format, symbol table, relocation entries
- [[04 - Linker]] — symbol resolution, PLT/GOT, static vs dynamic, common errors
