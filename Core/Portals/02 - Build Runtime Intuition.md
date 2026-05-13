# Build Runtime Intuition

These notes answer: "what does this FEEL like while running?"

Each Mental Model covers runtime flow, what wakes what, what blocks, where bottlenecks form.
They are NOT API references — they are execution stories with inline links to theory.

---

## Build Process — how your code becomes a binary

→ [[../Mental Models/01 - Build Process — The Machine]]
→ [[../Mental Models/02 - Preprocessor — The Machine]]
→ [[../Mental Models/03 - Compiler — The Machine]]
→ [[../Mental Models/04 - Assembler — The Machine]]
→ [[../Mental Models/05 - Linker — The Machine]]
→ [[../Mental Models/06 - Make and CMake — The Machine]]

---

## Memory — how data lives and moves

→ [[../Mental Models/30 - Process Memory Layout — The Machine]]
→ [[../Mental Models/31 - Stack vs Heap — The Machine]]
→ [[../Mental Models/malloc and free — The Machine]]
→ [[../Mental Models/07 - Pointers — The Machine]]
→ [[../Mental Models/10 - Structs and Unions — The Machine]]
→ [[../Mental Models/09 - Strings — The Machine]]

---

## C language at runtime

→ [[../Mental Models/08 - File IO — The Machine]]
→ [[../Mental Models/12 - Serialization — The Machine]]
→ [[../Mental Models/11 - Bitwise Operations — The Machine]]
→ [[../Mental Models/13 - Undefined Behavior — The Machine]]

---

## C++ object lifecycle

→ [[../Mental Models/14 - RAII — The Machine]]
→ [[../Mental Models/15 - Smart Pointers — The Machine]]
→ [[../Mental Models/16 - Move Semantics — The Machine]]
→ [[../Mental Models/19 - Virtual Functions — The Machine]]
→ [[../Mental Models/17 - Templates — The Machine]]
→ [[../Mental Models/18 - Inheritance — The Machine]]
→ [[../Mental Models/21 - STL Containers — The Machine]]
→ [[../Mental Models/22 - Exception Handling — The Machine]]

---

## Linux — what the OS is doing

→ [[../Mental Models/38 - Processes — The Machine]]
→ [[../Mental Models/39 - File Descriptors — The Machine]]
→ [[../Mental Models/40 - Signals — The Machine]]
→ [[../Mental Models/41 - Threads and pthreads — The Machine]]
→ [[../Mental Models/42 - Shared Memory — The Machine]]
→ [[../Mental Models/43 - Semaphores — The Machine]]
→ [[../Mental Models/mmap — The Machine]]
→ [[../Mental Models/44 - Kernel — The Machine]]

---

## Networking — what happens on the wire

→ [[../Mental Models/45 - Networking Overview — The Machine]]
→ [[../Mental Models/46 - TCP Sockets — The Machine]]
→ [[../Mental Models/47 - UDP Sockets — The Machine]]
→ [[../Mental Models/48 - epoll — The Machine]] ← start here for I/O multiplexing
→ [[../Mental Models/49 - IPC Overview — The Machine]]

---

## Design Patterns — how they execute

→ [[../Mental Models/52 - Reactor Pattern — The Machine]] ← how epoll becomes an event loop
→ [[../Mental Models/53 - Observer Pattern — The Machine]] ← how events propagate
→ [[../Mental Models/56 - Command Pattern — The Machine]] ← how work is queued and executed
→ [[../Mental Models/55 - Factory Pattern — The Machine]]
→ [[../Mental Models/54 - Singleton Pattern — The Machine]]
→ [[../Mental Models/57 - Strategy Pattern — The Machine]]

---

## Concurrency — what threads are actually doing

→ [[../Mental Models/50 - Multithreading Patterns — The Machine]]
→ [[../Mental Models/51 - Memory Ordering — The Machine]]

---

## Algorithms — how they scale

→ [[../Mental Models/58 - Data Structures — The Machine]]
→ [[../Mental Models/59 - Big-O and Complexity — The Machine]]

---

## LDS runtime machines → LDS vault

These show how the above patterns execute inside a real C++ system:
→ LDS/Runtime Machines/LDS System — The Machine
→ LDS/Runtime Machines/Reactor — The Machine
→ LDS/Runtime Machines/Request Lifecycle — The Machine
