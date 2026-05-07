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
