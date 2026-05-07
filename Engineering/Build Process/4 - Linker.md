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
