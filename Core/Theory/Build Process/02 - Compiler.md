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

See [[../C++/04 - Templates]] for template mechanics.

---

## Type Checking

The compiler enforces:
- No implicit narrowing conversions (with `-Wconversion`)
- const correctness — cannot pass `const T*` where `T*` is expected
- Virtual function overrides match base class signature

See [[../C++/10 - Type Casting]] — only `static_cast` and friends are safe because the compiler checks them.  
See [[../C++/06 - Virtual Functions]] — vtable pointers are set up by the compiler based on `virtual` declarations.

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

---

## Understanding Check

> [!question]- Why can the compiler catch a type mismatch between a function call and its definition, but not a missing definition in another translation unit?
> The compiler processes one translation unit at a time and has no visibility into other .cpp files. It does see the declaration (from the header) and uses it to type-check the call site — argument types, return type, const-correctness. But the actual function body lives in another translation unit that the compiler hasn't read. It leaves a placeholder (an UNDEF relocation entry) and trusts that the linker will supply the address later. A missing definition only becomes an error at link time when the linker scans all .o files and cannot find a GLOBAL symbol to satisfy the UNDEF reference.

> [!question]- What goes wrong if you compile LDS with -O3 but forget to mark a shared-memory flag as std::atomic or volatile?
> At -O3 the compiler aggressively assumes single-threaded semantics within a translation unit. It may hoist a loop condition check (while (!ready)) out of the loop entirely — if ready is a plain bool, the compiler proves it was false on entry and concludes it can never change within that thread's code, generating an infinite loop or eliminating the check entirely. Even without hoisting, it may cache the value in a register and never re-read from memory. std::atomic or at minimum volatile tells the compiler the variable can change externally and forces a memory read on every access.

> [!question]- Why does -fPIC (position-independent code) exist, and when does LDS need it?
> Position-independent code uses relative addressing — instructions reference other symbols as offsets from the current program counter rather than absolute addresses. This is required for shared libraries (.so files) because the dynamic linker loads them at an address determined at runtime, which varies per process and per run (ASLR). An absolute-addressed library would need to be relocated to a fixed address in every process, eliminating the memory-sharing benefit. LDS uses -fPIC when building any component that will be linked as a shared library. Executables themselves can use absolute addresses and don't require -fPIC unless they also serve as shared libraries (unusual).

> [!question]- How does the compiler handle a virtual function call differently from a regular function call, and why can't it always inline virtual calls even at -O3?
> A regular function call resolves at compile time to a direct jump instruction with a fixed target address (or a relocation that the linker fills in). A virtual call goes through the vtable: the compiler emits code to load the vtable pointer from the object, index to the correct slot, and call through the pointer — an indirect call whose target is only known at runtime. Inlining requires knowing the exact callee at compile time. If the compiler can prove via devirtualization (knowing the concrete type from context, e.g., a local variable declared as a concrete class) it may inline the virtual call. Without that proof — a polymorphic pointer or reference — it cannot inline it because the actual type and target function are unknown until runtime.

> [!question]- What does the compiler's semantic analysis phase do that the preprocessor and lexer do not, and why does this matter for LDS's use of const-correctness?
> The preprocessor does pure text substitution with no understanding of types or scoping. The lexer splits text into tokens (identifiers, keywords, literals) but applies no meaning. Semantic analysis resolves names to their declarations, checks type compatibility, enforces access specifiers, and verifies const-correctness — ensuring you don't pass a const T* where T* is expected, don't modify a const member through a non-const method, and don't call non-const methods on const objects. For LDS, marking storage accessors const ensures the compiler catches accidental mutations in read paths; without semantic analysis these would silently compile and produce subtle data corruption bugs only visible at runtime.
