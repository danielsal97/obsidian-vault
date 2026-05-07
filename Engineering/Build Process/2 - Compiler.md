# Stage 2 — Compiler

Takes one preprocessed translation unit (`.i`) and produces assembly code (`.s`). This is where syntax errors, type errors, and most warnings come from.

---

## What It Does — Internal Phases

```
Translation unit (.i)
        │
   [Lexer]          — tokenizes source text
        │
   [Parser]         — builds AST (abstract syntax tree)
        │
   [Semantic Analysis] — type checking, name resolution, overload resolution
        │
   [IR Generation]  — converts AST to intermediate representation (LLVM IR / GCC GIMPLE)
        │
   [Optimizer]      — transforms IR to be faster/smaller (-O flags control this)
        │
   [Code Generator] — outputs assembly (.s) for the target CPU
```

---

## Optimization Levels

```bash
g++ -O0   # no optimization — fast compile, easy debugging (default)
g++ -O1   # basic optimizations
g++ -O2   # most optimizations, no size/speed tradeoffs (production)
g++ -O3   # aggressive — vectorization, inlining, may increase binary size
g++ -Os   # optimize for size
g++ -Og   # optimize for debugging experience
```

Common optimizations the compiler performs:
- **Inlining** — replaces function call with function body (removes call overhead)
- **Dead code elimination** — removes unreachable code
- **Constant folding** — `3 * 4` → `12` at compile time
- **Loop unrolling** — duplicates loop body to reduce branch overhead
- **Register allocation** — assigns variables to CPU registers instead of stack

---

## Template Instantiation Happens Here

When the compiler sees `std::vector<int>`, it generates the full `vector<int>` class from the template. This happens per translation unit — if `main.cpp` and `foo.cpp` both use `vector<int>`, both generate it (the linker deduplicates).

This is why templates must be fully defined in headers: the compiler needs the template body at instantiation time.

See [[../C++/Templates]] for template mechanics.

---

## Type Checking

The compiler enforces:
- No implicit narrowing conversions (with `-Wconversion`)
- const correctness — cannot pass `const T*` where `T*` is expected
- Virtual function overrides match base class signature

See [[../C++/Type Casting]] — only `static_cast` and friends are safe because the compiler checks them.  
See [[../C++/Virtual Functions]] — vtable pointers are set up by the compiler based on `virtual` declarations.

---

## Common Compiler Flags

```bash
-Wall         # most warnings
-Wextra       # extra warnings
-Werror       # treat warnings as errors
-std=c++20    # set C++ standard
-g            # include debug info (for GDB/LLDB)
-fPIC         # position-independent code (required for shared libraries)
-I path       # add include search path
-D MACRO      # define a macro (equivalent to #define MACRO 1)
```

---

## What the Compiler Does NOT Do

- Does not know about other translation units — sees only one `.cpp` + its headers at a time
- Does not resolve `extern` symbols — those are the linker's job
- Does not allocate final memory addresses — those are relative, patched by the linker

This is why you can call a function declared in another `.cpp` as long as you have its declaration in a header — the compiler trusts the declaration and leaves a placeholder. The linker fills it in.

---

## Output: Assembly

```bash
g++ -S main.cpp -o main.s   # stop after compilation, emit assembly
cat main.s                  # human-readable x86_64 instructions
```

The assembly file contains:
- Instruction mnemonics (`movq`, `callq`, `ret`, etc.)
- Symbol names (function names, global variable names)
- Relocation markers (holes the linker will fill in)

---

## Viewing IR (LLVM/Clang)

```bash
clang++ -emit-llvm -S main.cpp -o main.ll   # human-readable LLVM IR
```

Useful for understanding what the optimizer does to your code.

---

## Connection to Other Stages

← [[1 - Preprocessor]] — sends the fully expanded translation unit  
→ [[3 - Assembler]] — receives the `.s` assembly file
