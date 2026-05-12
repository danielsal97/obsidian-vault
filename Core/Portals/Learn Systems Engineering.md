# Learn Systems Engineering

Follow this path top to bottom to build a complete systems engineering foundation.
Each layer depends on the one above it.

---

## Layer 1 — How programs are built
Understand what happens before your code runs.

→ [[../Theory/Build Process/1 - Preprocessor]] — #include resolution, macros, header guards
→ [[../Theory/Build Process/2 - Compiler]] — parsing, type checking, optimization, assembly output
→ [[../Theory/Build Process/3 - Assembler]] — assembly → object files, ELF, symbol table
→ [[../Theory/Build Process/4 - Linker]] — symbol resolution, static vs dynamic, PLT/GOT
→ [[../Theory/Build Process/Make and CMake]] — build automation

Mental models: [[../Mental Models/Build Process — The Machine]] → [[../Mental Models/Linker — The Machine]]

---

## Layer 2 — Memory and the C model
Understand how data lives in memory.

→ [[../Theory/Memory/Process Memory Layout]] — text, data, BSS, heap, stack, virtual memory
→ [[../Theory/Memory/Stack vs Heap]] — when each is used, growth direction, tradeoffs
→ [[../Theory/C/Memory - malloc and free]] — how the allocator works, fragmentation
→ [[../Theory/C/Pointers]] — pointer arithmetic, double pointers, function pointers, void*
→ [[../Theory/C/Structs and Unions]] — layout, padding, alignment, bit fields
→ [[../Theory/Memory/Memory Errors and Tools]] — leaks, use-after-free, ASan, Valgrind

Mental models: [[../Mental Models/Process Memory Layout — The Machine]] → [[../Mental Models/Stack vs Heap — The Machine]] → [[../Mental Models/malloc and free — The Machine]] → [[../Mental Models/Pointers — The Machine]]

---

## Layer 3 — C language fundamentals
→ [[../Theory/C/File IO]] — POSIX open/read/write/lseek, flags, errno
→ [[../Theory/C/Strings]] — null terminator, safe copy, sprintf
→ [[../Theory/C/Bitwise Operations]] — AND/OR/XOR, masking, byte reversal
→ [[../Theory/C/Serialization]] — manual serialization, byte order, framing
→ [[../Theory/C/Undefined Behavior]] — what UB is, why it's dangerous, sanitizers

---

## Layer 4 — C++ resource management
→ [[../Theory/C++/RAII]] — resource lifetimes, destructors, stack unwinding
→ [[../Theory/C++/Smart Pointers]] — unique_ptr, shared_ptr, weak_ptr
→ [[../Theory/C++/Move Semantics]] — lvalue/rvalue, move constructor, Rule of Five
→ [[../Theory/C++/Virtual Functions]] — vtable, override, pure virtual, slicing
→ [[../Theory/C++/Templates]] — function/class templates, specialization, SFINAE
→ [[../Theory/C++/Exception Handling]] — hierarchy, safety levels, noexcept

Mental models: [[../Mental Models/RAII — The Machine]] → [[../Mental Models/Smart Pointers — The Machine]] → [[../Mental Models/Move Semantics — The Machine]]

---

## Layer 5 — Linux system programming
→ [[../Theory/Linux/Processes]] — fork, exec, wait, zombies, daemon
→ [[../Theory/Linux/File Descriptors]] — everything is a file, fd lifecycle, dup, pipe, socketpair
→ [[../Theory/Linux/Signals]] — sigaction, async-signal-safety, signalfd, SIGPIPE
→ [[../Theory/Linux/Threads - pthreads]] — create, mutex, condition variable, rwlock, TLS
→ [[../Theory/Linux/Shared Memory]] — shm_open, mmap MAP_SHARED, sync
→ [[../Theory/Linux/Semaphores]] — sem_init, counting semaphores, producer/consumer
→ [[../Theory/Linux/mmap]] — file-backed mapping, anonymous mapping, msync

Mental models: [[../Mental Models/Processes — The Machine]] → [[../Mental Models/File Descriptors — The Machine]] → [[../Mental Models/Threads and pthreads — The Machine]]

---

## Layer 6 — Networking
→ [[../Theory/Networking/Overview]] — physical → Ethernet → IP → TCP/UDP → TLS → HTTP
→ [[../Theory/Networking/Sockets TCP]] — socket API, RecvAll loop, wire protocol, byte ordering
→ [[../Theory/Networking/UDP Sockets]] — UDP vs TCP, message boundaries, MTU, broadcast
→ [[../Theory/Networking/epoll]] — select vs poll vs epoll, level vs edge triggered
→ [[../Theory/Networking/IPC Overview]] — pipes, socketpair, unix sockets, shared memory, mq

Mental models: [[../Mental Models/epoll — The Machine]] → [[../Mental Models/TCP Sockets — The Machine]] → [[../Mental Models/Reactor Pattern — The Machine]]

---

## Layer 7 — Design Patterns
→ [[../Theory/Design Patterns/Reactor]] — epoll event loop, handler dispatch
→ [[../Theory/Design Patterns/Observer]] — publisher/subscriber, thread-safe notify
→ [[../Theory/Design Patterns/Command]] — encapsulate requests, work queues
→ [[../Theory/Design Patterns/Factory]] — create objects via interface
→ [[../Theory/Design Patterns/Singleton]] — one instance, thread-safe construction
→ [[../Theory/Design Patterns/Strategy]] — swappable algorithms at runtime

---

## Layer 8 — Concurrency
→ [[../Theory/Concurrency/Multithreading Patterns]] — thread pool, producer/consumer, futures
→ [[../Theory/Concurrency/Memory Ordering]] — happens-before, atomic, acquire/release, CAS

Mental models: [[../Mental Models/Multithreading Patterns — The Machine]] → [[../Mental Models/Memory Ordering — The Machine]]
