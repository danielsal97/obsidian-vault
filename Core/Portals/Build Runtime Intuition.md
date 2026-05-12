# Build Runtime Intuition

These notes answer: "what does this FEEL like while running?"

Each Mental Model covers runtime flow, what wakes what, what blocks, where bottlenecks form.
They are NOT API references — they are execution stories with inline links to theory.

---

## Build Process — how your code becomes a binary

→ [[../Mental Models/Build Process — The Machine]]
→ [[../Mental Models/Preprocessor — The Machine]]
→ [[../Mental Models/Compiler — The Machine]]
→ [[../Mental Models/Assembler — The Machine]]
→ [[../Mental Models/Linker — The Machine]]
→ [[../Mental Models/Make and CMake — The Machine]]

---

## Memory — how data lives and moves

→ [[../Mental Models/Process Memory Layout — The Machine]]
→ [[../Mental Models/Stack vs Heap — The Machine]]
→ [[../Mental Models/malloc and free — The Machine]]
→ [[../Mental Models/Pointers — The Machine]]
→ [[../Mental Models/Structs and Unions — The Machine]]
→ [[../Mental Models/Strings — The Machine]]

---

## C language at runtime

→ [[../Mental Models/File IO — The Machine]]
→ [[../Mental Models/Serialization — The Machine]]
→ [[../Mental Models/Bitwise Operations — The Machine]]
→ [[../Mental Models/Undefined Behavior — The Machine]]

---

## C++ object lifecycle

→ [[../Mental Models/RAII — The Machine]]
→ [[../Mental Models/Smart Pointers — The Machine]]
→ [[../Mental Models/Move Semantics — The Machine]]
→ [[../Mental Models/Virtual Functions — The Machine]]
→ [[../Mental Models/Templates — The Machine]]
→ [[../Mental Models/Inheritance — The Machine]]
→ [[../Mental Models/STL Containers — The Machine]]
→ [[../Mental Models/Exception Handling — The Machine]]

---

## Linux — what the OS is doing

→ [[../Mental Models/Processes — The Machine]]
→ [[../Mental Models/File Descriptors — The Machine]]
→ [[../Mental Models/Signals — The Machine]]
→ [[../Mental Models/Threads and pthreads — The Machine]]
→ [[../Mental Models/Shared Memory — The Machine]]
→ [[../Mental Models/Semaphores — The Machine]]
→ [[../Mental Models/mmap — The Machine]]
→ [[../Mental Models/Kernel — The Machine]]

---

## Networking — what happens on the wire

→ [[../Mental Models/Networking Overview — The Machine]]
→ [[../Mental Models/TCP Sockets — The Machine]]
→ [[../Mental Models/UDP Sockets — The Machine]]
→ [[../Mental Models/epoll — The Machine]] ← start here for I/O multiplexing
→ [[../Mental Models/IPC Overview — The Machine]]

---

## Design Patterns — how they execute

→ [[../Mental Models/Reactor Pattern — The Machine]] ← how epoll becomes an event loop
→ [[../Mental Models/Observer Pattern — The Machine]] ← how events propagate
→ [[../Mental Models/Command Pattern — The Machine]] ← how work is queued and executed
→ [[../Mental Models/Factory Pattern — The Machine]]
→ [[../Mental Models/Singleton Pattern — The Machine]]
→ [[../Mental Models/Strategy Pattern — The Machine]]

---

## Concurrency — what threads are actually doing

→ [[../Mental Models/Multithreading Patterns — The Machine]]
→ [[../Mental Models/Memory Ordering — The Machine]]

---

## Algorithms — how they scale

→ [[../Mental Models/Data Structures — The Machine]]
→ [[../Mental Models/Big-O and Complexity — The Machine]]

---

## LDS runtime machines → LDS vault

These show how the above patterns execute inside a real C++ system:
→ LDS/Runtime Machines/LDS System — The Machine
→ LDS/Runtime Machines/Reactor — The Machine
→ LDS/Runtime Machines/Request Lifecycle — The Machine
