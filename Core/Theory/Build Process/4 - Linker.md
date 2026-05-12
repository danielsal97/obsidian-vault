# Stage 4 — Linker

Takes all object files (`.o`) and libraries, resolves all symbol references, assigns final addresses, and produces the executable or shared library.

---

## What It Does

```bash
g++ main.o foo.o bar.o -o myapp          # link object files
g++ main.o -lm -o myapp                  # link with libm (math library)
g++ main.o -L/my/libs -lmylib -o myapp  # -L adds search path for libraries
```

Steps:
1. **Symbol resolution** — match each `UNDEF` symbol to a `GLOBAL` definition
2. **Relocation** — patch placeholder addresses with real final addresses
3. **Address assignment** — lay out all sections into the final binary's virtual address space
4. **Output** — write the ELF executable or shared library

---

## Static vs Dynamic Linking

### Static Linking (`-static` or `.a` archives)

```bash
ar rcs libfoo.a foo.o bar.o   # create static library
g++ main.o -L. -lfoo -static -o myapp
```

- All needed code is copied into the executable at link time
- Resulting binary is self-contained — no dependencies at runtime
- Larger binary size
- Used in embedded systems, or when you want zero runtime dependencies

### Dynamic Linking (default, `.so` shared objects)

```bash
g++ -fPIC -shared foo.o bar.o -o libfoo.so   # create shared library
g++ main.o -L. -lfoo -o myapp                # link against it
```

- The executable stores a reference to `libfoo.so`, not its code
- At runtime, the dynamic linker (`ld.so`) loads the `.so` and patches the PLT
- Multiple programs share one copy of the library in memory
- Library can be updated without relinking the executable

```bash
ldd myapp          # show which .so files the binary depends on
LD_LIBRARY_PATH=/my/libs ./myapp   # tell loader where to find .so at runtime
```

---

## Symbol Resolution Rules

1. Scan object files left to right
2. If a symbol is `UNDEF`, look for it in subsequent `.o` files and libraries
3. **Order matters** — if `main.o` calls something in `libfoo.a`, `-lfoo` must come AFTER `main.o`

```bash
# Wrong — libfoo scanned before main.o needs it:
g++ -lfoo main.o -o myapp   # may fail

# Correct:
g++ main.o -lfoo -o myapp
```

---

## Duplicate Symbols

If two `.o` files both define `void foo()`, the linker errors:

```
multiple definition of 'foo'
```

Avoid by:
- Using `static` (internal linkage)
- Putting definitions only in `.cpp` files, not headers
- Using `inline` for functions defined in headers (special linker rule: `inline` allows multiple identical definitions — linker keeps one)

---

## The PLT and GOT (Dynamic Linking Internals)

When a shared library is dynamically linked, external function calls go through:
- **PLT** (Procedure Linkage Table) — a trampoline that redirects to the actual function
- **GOT** (Global Offset Table) — a table of addresses, filled in by the dynamic linker at load time

The first call to `printf` hits the PLT stub → dynamic linker resolves and patches the GOT entry → all future calls go directly to `printf`.

---

## What Linker Puts in Memory

```
Virtual Address Space (set by linker, loaded by OS):
0x400000  .text    — executable code (read + execute)
0x600000  .rodata  — string literals, const globals (read only)
0x601000  .data    — initialized globals (read + write)
0x602000  .bss     — uninitialized globals (read + write, zero-initialized)
          [heap]   — grows up (managed by malloc / new)
          [stack]  — grows down (managed by the OS/CPU)
```

See [[../Memory/Process Memory Layout]] for the full runtime layout.  
See [[../C/Memory - malloc and free]] — `malloc` manages the heap which exists above `.bss`.

---

## Common Linker Errors

| Error | Cause |
|---|---|
| `undefined reference to 'foo'` | foo declared but never defined; missing `-lfoo` |
| `multiple definition of 'foo'` | function defined in a header without `inline`; defined in two `.cpp` files |
| `cannot find -lbar` | missing `-L` path; library not installed |
| `SONAME not found at runtime` | `.so` installed but not in `LD_LIBRARY_PATH` or `/etc/ld.so.conf` |

---

## Make and the Linker

In a Makefile, the final link step looks like:

```makefile
myapp: main.o foo.o bar.o
    g++ $^ -o $@ -lpthread -lm
```

Each `.o` is built by its own compile rule. The final rule links them all.

See [[../Build Process/Overview]] for where this fits in the pipeline.

---

## Connection to Other Stages

← [[3 - Assembler]] — receives `.o` object files  
→ Executable loaded by the OS dynamic linker (`/lib64/ld-linux-x86-64.so.2`) at runtime

---

## Understanding Check

> [!question]- Why does linker argument order matter for static libraries but not for object files?
> Object files are always fully included — the linker takes every symbol from every .o listed. Static libraries (.a archives) are treated differently: the linker only extracts .o members from a .a that satisfy an UNDEF symbol it has already encountered. If -lfoo appears before main.o, the linker scans libfoo.a before it knows main.o needs anything from it, extracts nothing, and moves on. When it later processes main.o and discovers the UNDEF references, libfoo.a has already been scanned and won't be revisited. The fix is to list .o files before the libraries they depend on, so the UNDEFs are registered first.

> [!question]- What goes wrong if LDS is built as a dynamically linked binary and the deployment Linux machine doesn't have the matching libc.so version?
> At load time, the dynamic linker (/lib64/ld-linux-x86-64.so.2) reads the binary's NEEDED list and searches for each .so by SONAME. If the required libc.so.6 version is not present or is a different ABI-incompatible version, the dynamic linker fails with "version 'GLIBC_2.34' not found" and the program refuses to start — not just crash on the first missing call, but fail immediately before main() even runs. This is why LDS could be built statically for deployment on minimal containers, or why Docker images pin to a specific base image with known library versions.

> [!question]- Why can inline functions be defined in headers and included in multiple .cpp files without causing "multiple definition" linker errors, while regular functions cannot?
> The C++ standard grants inline functions special linkage rules: each translation unit may have its own copy of an inline function's definition, and the linker is required to merge all identical copies into one. The compiler marks inline functions with COMDAT (or "weak") linkage in the .o, signaling to the linker that duplicate definitions are expected and acceptable. A regular (non-inline) function has GLOBAL strong linkage — the linker treats two GLOBAL definitions as a hard error. This is why header-only libraries work: every included method marked inline can appear in many .o files without conflict.

> [!question]- What is the PLT and why is there a performance cost on the first call to a dynamically linked function like malloc?
> The PLT (Procedure Linkage Table) is a set of small trampolines in the executable. When you call malloc for the first time, execution jumps to the PLT stub for malloc, which calls the dynamic linker's resolver. The resolver finds the actual address of malloc in libc.so, writes it into the GOT (Global Offset Table) entry for malloc, and jumps to it. All subsequent calls to malloc jump through the PLT stub, read the now-populated GOT entry, and jump directly to malloc — one extra indirection but no resolver overhead. The first-call cost is the dynamic linker walking the symbol table of libc.so, which can take microseconds in a large library.

> [!question]- In LDS's Makefile, if LocalStorage.cpp changes but InputMediator.cpp does not, why is it correct to only recompile LocalStorage.cpp and re-run the link step?
> Each .cpp file produces an independent .o via its own compile rule. Only the changed file and its dependents need recompilation — Make tracks this via timestamps. LocalStorage.o is regenerated from the changed LocalStorage.cpp. InputMediator.o is unchanged because InputMediator.cpp and its included headers have not changed. The link step must re-run because it combines all .o files and the new LocalStorage.o has different content (new code, potentially different symbol offsets). The linker produces a fresh executable from the mix of old and new .o files. This incremental build model is why separating code into multiple .cpp files and headers is worth the organizational effort.
