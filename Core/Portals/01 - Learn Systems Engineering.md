# Learn Systems Engineering

The journey from source file to live system. Each layer answers: **why does the next layer need the previous one?**

Follow top to bottom. When you finish each layer, you should be able to explain what the machine is doing — not just what the API does.

---

## Layer 1 — How a binary comes to exist
Before a process can run, its binary must exist. This layer is about the pipeline that transforms `.cpp` text into a file the kernel can execute.

→ [[../Domains/00 - Build Process/Theory/01 - Preprocessor]] — text expansion: #include, #define, #ifdef
→ [[../Domains/00 - Build Process/Theory/02 - Compiler]] — parses C++, emits assembly with blank symbol slots
→ [[../Domains/00 - Build Process/Theory/03 - Assembler]] — assembly → .o files (ELF with relocation entries)
→ [[../Domains/00 - Build Process/Theory/04 - Linker]] — resolves blank slots, merges .o files into one executable
→ [[../Domains/00 - Build Process/Theory/05 - Make and CMake]] — automates the full pipeline

Runtime payoff: after this layer, you know why the linker error `undefined reference to X` means the .o that defines X wasn't linked in.

Mental models: [[../Domains/00 - Build Process/Mental Models/01 - Build Process — The Machine]] → [[../Domains/00 - Build Process/Mental Models/02 - Preprocessor — The Machine]] → [[../Domains/00 - Build Process/Mental Models/05 - Linker — The Machine]]

---

## Layer 2 — Where data lives at runtime
The binary exists. Now it runs. This layer is about where memory comes from and how it's organized in a live process.

→ [[../Domains/01 - Memory/Theory/01 - Process Memory Layout]] — text, data, BSS, heap, stack: what lands where in virtual memory
→ [[../Domains/01 - Memory/Theory/02 - Stack vs Heap]] — why stack is fast, why heap is needed, growth direction
→ [[../Domains/02 - C/Theory/02 - Memory - malloc and free]] — how the allocator works, brk(), mmap(), fragmentation
→ [[../Domains/02 - C/Theory/01 - Pointers]] — pointer arithmetic, double pointers, function pointers, void*
→ [[../Domains/02 - C/Theory/04 - Structs and Unions]] — struct layout, padding, alignment rules
→ [[../Domains/01 - Memory/Theory/09 - Memory Errors and Tools]] — leaks, use-after-free, double-free, ASan, Valgrind

Runtime payoff: after this layer, you can look at a segfault address and know which region was accessed and why.

Mental models: [[../Domains/01 - Memory/Mental Models/01 - Process Memory Layout — The Machine]] → [[../Domains/01 - Memory/Mental Models/02 - Stack vs Heap — The Machine]] → [[../Domains/02 - C/Mental Models/08 - malloc and free — The Machine]] → [[../Domains/02 - C/Mental Models/01 - Pointers — The Machine]]

---

## Layer 3 — C: the operating interface
C is the language the OS speaks. This layer covers the C primitives used for I/O, data encoding, and low-level bit manipulation.

→ [[../Domains/02 - C/Theory/05 - File IO]] — POSIX open/read/write/lseek, flags, errno
→ [[../Domains/02 - C/Theory/03 - Strings]] — null terminator, safe copy, sprintf pitfalls
→ [[../Domains/02 - C/Theory/06 - Bitwise Operations]] — AND/OR/XOR/NOT, masking, bit fields, byte reversal
→ [[../Domains/02 - C/Theory/07 - Serialization]] — manual binary encoding, byte order (htons/ntohl), framing
→ [[../Domains/02 - C/Theory/08 - Undefined Behavior]] — what UB is, why the compiler can exploit it, sanitizers

---

## Layer 4 — C++ resource management
C++ adds automatic resource lifetime management on top of C's manual model. This layer is about how C++ manages objects without garbage collection.

→ [[../Domains/03 - C++/Theory/01 - RAII]] — destructor timing, stack unwinding, why resources can't leak
→ [[../Domains/03 - C++/Theory/02 - Smart Pointers]] — unique_ptr (sole ownership), shared_ptr (shared), weak_ptr (no ownership)
→ [[../Domains/03 - C++/Theory/03 - Move Semantics]] — lvalue/rvalue reference, move constructor, Rule of Five
→ [[../Domains/03 - C++/Theory/06 - Virtual Functions]] — vtable layout, override, pure virtual, slicing danger
→ [[../Domains/03 - C++/Theory/04 - Templates]] — function/class templates, specialization, SFINAE
→ [[../Domains/03 - C++/Theory/09 - Exception Handling]] — throw/catch, exception safety levels, noexcept

Runtime payoff: after this layer, you can explain what happens in memory when `unique_ptr<Foo> p = std::move(q)` executes.

Mental models: [[../Domains/03 - C++/Mental Models/01 - RAII — The Machine]] → [[../Domains/03 - C++/Mental Models/02 - Smart Pointers — The Machine]] → [[../Domains/03 - C++/Mental Models/03 - Move Semantics — The Machine]]

---

## Layer 5 — Linux: the OS interface
A process doesn't run in isolation. It interacts with the kernel constantly. This layer is about the system calls that matter for systems programming.

→ [[../Domains/04 - Linux/Theory/01 - Processes]] — fork(), exec(), wait(), zombie, daemon process
→ [[../Domains/04 - Linux/Theory/02 - File Descriptors]] — everything is an fd: files, sockets, pipes, timers
→ [[../Domains/04 - Linux/Theory/03 - Signals]] — sigaction, async-signal-safety, signalfd, SIGPIPE
→ [[../Domains/04 - Linux/Theory/04 - Threads - pthreads]] — pthread_create, mutex, condition variable, TLS
→ [[../Domains/04 - Linux/Theory/05 - Shared Memory]] — shm_open, mmap MAP_SHARED, synchronization
→ [[../Domains/04 - Linux/Theory/06 - Semaphores]] — counting semaphore, sem_wait/post, producer/consumer
→ [[../Domains/04 - Linux/Theory/07 - mmap]] — file-backed vs anonymous mapping, MAP_PRIVATE vs MAP_SHARED

Runtime payoff: after this layer, you can explain the entire process model and why SIGPIPE kills a process writing to a closed socket.

Mental models: [[../Domains/04 - Linux/Mental Models/01 - Processes — The Machine]] → [[../Domains/04 - Linux/Mental Models/02 - File Descriptors — The Machine]] → [[../Domains/04 - Linux/Mental Models/04 - Threads and pthreads — The Machine]]

---

## Layer 6 — Networking: talking to the world
Processes communicate over sockets. This layer covers the socket API, the protocols, and the I/O multiplexing mechanism that makes non-blocking servers possible.

→ [[../Domains/06 - Networking/Theory/01 - Overview]] — physical → Ethernet → IP → TCP/UDP → application
→ [[../Domains/06 - Networking/Theory/02 - Sockets TCP]] — socket(), connect(), RecvAll loop, wire protocol design
→ [[../Domains/06 - Networking/Theory/03 - UDP Sockets]] — sendto/recvfrom, message boundaries, MTU, broadcast
→ [[../Domains/06 - Networking/Theory/04 - epoll]] — select vs poll vs epoll, level vs edge-triggered, EPOLLET
→ [[../Domains/06 - Networking/Theory/05 - IPC Overview]] — pipes, socketpair, unix domain sockets, shared memory

Runtime payoff: after this layer, you can walk through what happens in kernel space when `epoll_wait()` returns.

Mental models: [[../Domains/06 - Networking/Mental Models/04 - epoll — The Machine]] → [[../Domains/06 - Networking/Mental Models/02 - TCP Sockets — The Machine]] → [[../Domains/07 - Design Patterns/Mental Models/01 - Reactor Pattern — The Machine]]

---

## Layer 7 — Design Patterns: structure that scales
Individual components need to be composed. Design patterns are the recurring structures that make concurrent, event-driven systems maintainable.

→ [[../Domains/07 - Design Patterns/Theory/01 - Reactor]] — epoll event loop + handler dispatch table
→ [[../Domains/07 - Design Patterns/Theory/02 - Observer]] — publisher/subscriber, thread-safe notify()
→ [[../Domains/07 - Design Patterns/Theory/05 - Command]] — encapsulate request as object, enables work queues and undo
→ [[../Domains/07 - Design Patterns/Theory/04 - Factory]] — create objects by interface, decouples construction from use
→ [[../Domains/07 - Design Patterns/Theory/03 - Singleton]] — one global instance, thread-safe construction
→ [[../Domains/07 - Design Patterns/Theory/06 - Strategy]] — swap algorithms at runtime via interface

---

## Layer 8 — Concurrency: sharing correctly
Multiple threads operate on shared state. This layer covers the models that prevent data corruption and the primitives that enforce ordering.

→ [[../Domains/05 - Concurrency/Theory/01 - Multithreading Patterns]] — thread pool, producer/consumer WPQ, futures
→ [[../Domains/05 - Concurrency/Theory/02 - Memory Ordering]] — happens-before, acquire/release, CAS, memory barriers

Runtime payoff: after this layer, you can explain why `std::atomic<bool>` with `memory_order_relaxed` is NOT safe for synchronizing two threads.

Mental models: [[../Domains/05 - Concurrency/Mental Models/01 - Multithreading Patterns — The Machine]] → [[../Domains/05 - Concurrency/Mental Models/02 - Memory Ordering — The Machine]]
