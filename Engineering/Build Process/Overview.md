# Build Process Overview

Source code → binary in four stages. Each stage transforms one representation into another.

---

## Full Pipeline

```
Source files (.cpp, .c, .h)
        │
        ▼  Stage 1
   [Preprocessor]   — text substitution, header insertion
        │
        ▼  Stage 2
   [Compiler]       — syntax/type checking, optimization, code generation
        │
        ▼  Stage 3
   [Assembler]      — converts assembly text to machine code
        │
        ▼  Stage 4
   [Linker]         — combines object files, resolves symbols → executable
        │
        ▼
   Executable or Shared Library
```

---

## Files at Each Stage

| Stage | Input | Output |
|---|---|---|
| Preprocessor | `.cpp` + `.h` | Translation unit (`.i`) |
| Compiler | Translation unit | Assembly (`.s`) |
| Assembler | Assembly | Object file (`.o`) |
| Linker | Object files + libraries | Executable or `.so` |

---

## Commands

```bash
# All at once (default):
g++ -o myapp main.cpp foo.cpp

# Step by step:
g++ -E main.cpp -o main.i          # preprocess only
g++ -S main.i  -o main.s           # compile to assembly
g++ -c main.s  -o main.o           # assemble to object file
g++ main.o foo.o -o myapp          # link

# GCC shortcuts to stop at a stage:
g++ -E   # stop after preprocessing
g++ -S   # stop after compiling
g++ -c   # stop after assembling
```

---

## Related Notes

| Stage | Deep-dive |
|---|---|
| Preprocessor | [[1 - Preprocessor]] |
| Compiler | [[2 - Compiler]] |
| Assembler | [[3 - Assembler]] |
| Linker | [[4 - Linker]] |

---

## Where Things Live at Runtime

After the linker runs, the OS loader maps the binary into memory. See [[../Memory/Process Memory Layout]] for how text, data, BSS, heap, and stack segments are laid out.
