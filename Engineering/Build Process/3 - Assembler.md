# Stage 3 — Assembler

Takes assembly text (`.s`) and converts it to machine code (`.o` — object file). This step is mostly mechanical — assembly mnemonics map 1:1 to binary opcodes.

---

## What It Does

```bash
g++ -c main.s -o main.o    # assemble only
# or in one step:
g++ -c main.cpp -o main.o  # preprocess + compile + assemble (most common)
```

The assembler:
1. Converts each instruction mnemonic to its binary encoding
2. Assigns local symbol offsets (relative addresses within the `.o`)
3. Produces a relocation table — list of "holes" that need to be filled in

---

## Object File Format — ELF (Linux)

On Linux, object files use the ELF (Executable and Linkable Format):

```
ELF Object File (.o)
├── ELF header          — magic bytes, architecture, entry point
├── .text section       — compiled machine code (instructions)
├── .data section       — initialized global/static variables
├── .bss section        — uninitialized global/static variables (no bytes stored)
├── .rodata section     — read-only data (string literals, const globals)
├── Symbol table        — list of defined and referenced symbols
└── Relocation table    — where the linker needs to patch addresses
```

See [[../Memory/Process Memory Layout]] — these sections map directly to the runtime memory segments.

---

## Symbol Table

Every function and global variable gets an entry:

```
Symbol      | Type     | Binding  | Section
------------|----------|----------|--------
main        | FUNC     | GLOBAL   | .text
g_counter   | OBJECT   | GLOBAL   | .data
helper()    | FUNC     | GLOBAL   | .text
printf      | FUNC     | GLOBAL   | UNDEF    ← defined elsewhere, linker resolves
```

- **GLOBAL** — visible to other object files (external linkage)
- **LOCAL** — only visible within this `.o` (`static` functions/variables)
- **UNDEF** — referenced here but defined elsewhere; the linker must find it

---

## Relocation Entries

When the assembler encounters a symbol whose address is unknown (e.g., calling `printf` or referencing a global in another `.o`), it writes a placeholder and records a relocation:

```
Relocation: at offset 0x1A in .text, fill in the address of symbol 'printf'
```

The linker reads all relocation tables and patches the placeholder bytes with real addresses.

---

## Inspecting Object Files

```bash
nm main.o              # list symbols (U = undefined, T = text section)
objdump -d main.o      # disassemble machine code
objdump -h main.o      # show sections and their sizes
readelf -a main.o      # full ELF dump
```

---

## Static vs Inline Functions

```cpp
static void helper() { ... }   // LOCAL symbol — not visible to linker across .o files
inline void helper() { ... }   // may be inlined by compiler; if not, also LOCAL
```

Two `.o` files can both define `static void helper()` without conflict — they're invisible to each other. But two `.o` files cannot both define `void helper()` (non-static) — that's a duplicate symbol error at link time.

---

## One Translation Unit = One Object File

Every `.cpp` file compiles to its own `.o` independently:
- `main.cpp` → `main.o`
- `foo.cpp` → `foo.o`
- `bar.cpp` → `bar.o`

They're combined later by the linker. This is why you can't call a function defined in `foo.cpp` without either including its `.cpp` (bad) or declaring it in a header (correct) — the assembler only knows about the current translation unit.

---

## Connection to Other Stages

← [[2 - Compiler]] — receives `.s` assembly  
→ [[4 - Linker]] — sends `.o` object file(s)

---

## Understanding Check

> [!question]- Why does the assembler produce a relocation table instead of final addresses for cross-file symbols like printf?
> At assembly time, the assembler knows the layout of the current .o file but has no knowledge of other .o files or where they will be placed in the final executable. printf is defined in libc, which hasn't been processed yet. The assembler writes a placeholder (typically zero or a relative offset of zero) at the call site and records a relocation entry: "at offset X in .text, substitute the address of symbol 'printf'." The linker, which sees all .o files and libraries simultaneously, reads these relocation tables and patches every placeholder with the actual resolved address.

> [!question]- What is the difference between a LOCAL and GLOBAL symbol in the object file, and how does this explain why two .o files can each have a static helper() without conflict?
> GLOBAL symbols are exported — they are visible to the linker when combining multiple .o files, and the linker expects exactly one GLOBAL definition for each referenced symbol. LOCAL symbols (produced by static functions or variables in C++) are invisible to the linker outside their .o file; they don't participate in cross-file symbol resolution. Two .o files each with static void helper() produce two LOCAL symbols of the same name that live in separate namespaces from the linker's perspective. They never collide because the linker never tries to unify them. A non-static helper() is GLOBAL and would cause a "multiple definition" error.

> [!question]- What goes wrong if a .o file's .bss section claims 4MB for uninitialized global arrays but no bytes are actually stored in the file?
> Nothing — that's the intended behavior of .bss. The .bss section stores only its size, not the actual zeros. When the OS loads the executable it allocates virtual memory pages for .bss and zero-initializes them (copy-on-write from a zero page). This keeps the binary size small: a program with a 100MB uninitialized global array has a .o and executable that don't contain 100MB of zeros on disk. The "goes wrong" case is mistakenly putting a large initialized (non-zero) array in .data instead of .bss — that forces all those bytes into the binary file on disk.

> [!question]- Why does nm show printf as 'U' (UNDEF) in main.o but 'T' (text section) in libc.so, and how does this connect to the linker's job?
> 'U' means the symbol is referenced in this .o but defined elsewhere — the assembler recorded it as an UNDEF relocation. 'T' means the symbol has a definition in the .text section of that object. When the linker processes main.o it collects all UNDEF references and searches subsequent .o files and libraries for matching GLOBAL definitions. Finding printf's 'T' entry in libc.so resolves the UNDEF, and the linker patches main.o's call site with the correct address (or PLT stub for dynamic linking). If no GLOBAL 'T' definition is found for an UNDEF symbol, the linker errors with "undefined reference."

> [!question]- In LDS, each .cpp (InputMediator.cpp, LocalStorage.cpp, etc.) compiles to its own .o. What would break if someone put the LocalStorage class definition in a header AND in LocalStorage.cpp?
> The header copy is included by every .cpp that needs LocalStorage — say InputMediator.cpp and main.cpp. After preprocessing, each of those translation units has the full LocalStorage class body. The compiler emits GLOBAL symbols for LocalStorage's methods in both resulting .o files. When the linker combines them, it finds duplicate GLOBAL definitions for LocalStorage::Read, LocalStorage::Write, etc., and errors with "multiple definition." The fix is to keep only the class declaration (member signatures) in the header and the method bodies exclusively in LocalStorage.cpp.
