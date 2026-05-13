# Learn Systems Engineering

Follow this path top to bottom to build a complete systems engineering foundation.
Each layer depends on the one above it.

---

## Layer 1 — How programs are built
Understand what happens before your code runs.

→ [[../Theory/Build Process/01 - Preprocessor]] — #include resolution, macros, header guards
→ [[../Theory/Build Process/02 - Compiler]] — parsing, type checking, optimization, assembly output
→ [[../Theory/Build Process/03 - Assembler]] — assembly → object files, ELF, symbol table
→ [[../Theory/Build Process/04 - Linker]] — symbol resolution, static vs dynamic, PLT/GOT
→ [[../Theory/Build Process/05 - Make and CMake]] — build automation

Mental models: [[../Mental Models/01 - Build Process — The Machine]] → [[../Mental Models/05 - Linker — The Machine]]

---

## Layer 2 — Memory and the C model
Understand how data lives in memory.

→ [[../Theory/Memory/01 - Process Memory Layout]] — text, data, BSS, heap, stack, virtual memory
→ [[../Theory/Memory/02 - Stack vs Heap]] — when each is used, growth direction, tradeoffs
→ [[../Theory/C/02 - Memory - malloc and free]] — how the allocator works, fragmentation
→ [[../Theory/C/01 - Pointers]] — pointer arithmetic, double pointers, function pointers, void*
→ [[../Theory/C/04 - Structs and Unions]] — layout, padding, alignment, bit fields
→ [[../Theory/Memory/09 - Memory Errors and Tools]] — leaks, use-after-free, ASan, Valgrind

Mental models: [[../Mental Models/30 - Process Memory Layout — The Machine]] → [[../Mental Models/31 - Stack vs Heap — The Machine]] → [[../Mental Models/malloc and free — The Machine]] → [[../Mental Models/07 - Pointers — The Machine]]

---

## Layer 3 — C language fundamentals
→ [[../Theory/C/05 - File IO]] — POSIX open/read/write/lseek, flags, errno
→ [[../Theory/C/03 - Strings]] — null terminator, safe copy, sprintf
→ [[../Theory/C/06 - Bitwise Operations]] — AND/OR/XOR, masking, byte reversal
→ [[../Theory/C/07 - Serialization]] — manual serialization, byte order, framing
→ [[../Theory/C/08 - Undefined Behavior]] — what UB is, why it's dangerous, sanitizers

---

## Layer 4 — C++ resource management
→ [[../Theory/C++/01 - RAII]] — resource lifetimes, destructors, stack unwinding
→ [[../Theory/C++/02 - Smart Pointers]] — unique_ptr, shared_ptr, weak_ptr
→ [[../Theory/C++/03 - Move Semantics]] — lvalue/rvalue, move constructor, Rule of Five
→ [[../Theory/C++/06 - Virtual Functions]] — vtable, override, pure virtual, slicing
→ [[../Theory/C++/04 - Templates]] — function/class templates, specialization, SFINAE
→ [[../Theory/C++/09 - Exception Handling]] — hierarchy, safety levels, noexcept

Mental models: [[../Mental Models/14 - RAII — The Machine]] → [[../Mental Models/15 - Smart Pointers — The Machine]] → [[../Mental Models/16 - Move Semantics — The Machine]]

---

## Layer 5 — Linux system programming
→ [[../Theory/Linux/01 - Processes]] — fork, exec, wait, zombies, daemon
→ [[../Theory/Linux/02 - File Descriptors]] — everything is a file, fd lifecycle, dup, pipe, socketpair
→ [[../Theory/Linux/03 - Signals]] — sigaction, async-signal-safety, signalfd, SIGPIPE
→ [[../Theory/Linux/04 - Threads - pthreads]] — create, mutex, condition variable, rwlock, TLS
→ [[../Theory/Linux/05 - Shared Memory]] — shm_open, mmap MAP_SHARED, sync
→ [[../Theory/Linux/06 - Semaphores]] — sem_init, counting semaphores, producer/consumer
→ [[../Theory/Linux/07 - mmap]] — file-backed mapping, anonymous mapping, msync

Mental models: [[../Mental Models/38 - Processes — The Machine]] → [[../Mental Models/39 - File Descriptors — The Machine]] → [[../Mental Models/41 - Threads and pthreads — The Machine]]

---

## Layer 6 — Networking
→ [[../Theory/Networking/01 - Overview]] — physical → Ethernet → IP → TCP/UDP → TLS → HTTP
→ [[../Theory/Networking/02 - Sockets TCP]] — socket API, RecvAll loop, wire protocol, byte ordering
→ [[../Theory/Networking/03 - UDP Sockets]] — UDP vs TCP, message boundaries, MTU, broadcast
→ [[../Theory/Networking/04 - epoll]] — select vs poll vs epoll, level vs edge triggered
→ [[../Theory/Networking/05 - IPC Overview]] — pipes, socketpair, unix sockets, shared memory, mq

Mental models: [[../Mental Models/48 - epoll — The Machine]] → [[../Mental Models/46 - TCP Sockets — The Machine]] → [[../Mental Models/52 - Reactor Pattern — The Machine]]

---

## Layer 7 — Design Patterns
→ [[../Theory/Design Patterns/01 - Reactor]] — epoll event loop, handler dispatch
→ [[../Theory/Design Patterns/02 - Observer]] — publisher/subscriber, thread-safe notify
→ [[../Theory/Design Patterns/05 - Command]] — encapsulate requests, work queues
→ [[../Theory/Design Patterns/04 - Factory]] — create objects via interface
→ [[../Theory/Design Patterns/03 - Singleton]] — one instance, thread-safe construction
→ [[../Theory/Design Patterns/06 - Strategy]] — swappable algorithms at runtime

---

## Layer 8 — Concurrency
→ [[../Theory/Concurrency/01 - Multithreading Patterns]] — thread pool, producer/consumer, futures
→ [[../Theory/Concurrency/02 - Memory Ordering]] — happens-before, atomic, acquire/release, CAS

Mental models: [[../Mental Models/50 - Multithreading Patterns — The Machine]] → [[../Mental Models/51 - Memory Ordering — The Machine]]
