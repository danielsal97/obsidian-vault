# C++ Compilation Pipeline

![[cpp_compilation_pipeline.png]]

---

## Main Stages

- [[Preprocessor]]
- [[Translation Unit]]
- [[Parser]]
- [[AST]]
- [[Semantic Analysis]]
- [[Optimizer]]
- [[Linker]]
- [[ELF Loader]]

---

## Runtime Flow

Source File
→ Preprocessor
→ Translation Unit
→ Parser
→ AST
→ IR
→ Optimizer
→ Assembly
→ Linker
→ Executable

---

## Important Concepts

- [[Macro Expansion]]
- [[Conditional Compilation]]
- [[Name Mangling]]
- [[Template Instantiation]]