# Engineering Notes

General knowledge that carries across every project and every job.

---

## C Language
- [[C/Pointers]] — pointer arithmetic, double pointers, function pointers, void*, const
- [[C/Strings]] — null terminator, safe copy, sprintf, common bugs
- [[C/Structs and Unions]] — memory layout, padding, opaque pointers, bit fields, unions
- [[C/Memory - malloc and free]] — how malloc works, fragmentation, custom allocators, tools
- [[C/Undefined Behavior]] — what UB is, common sources, why it's dangerous, sanitizers
- [[C/Bitwise Operations]] — AND/OR/XOR/shift, masking patterns, byte reversal, GCC builtins
- [[C/Serialization]] — manual serialization, packed structs, byte order, length-prefix framing
- [[C/File IO]] — POSIX open/read/write/lseek, stdio, flags, errno, atomic write pattern

## C++
- [[C++/RAII]] — resource lifetimes, destructors, stack unwinding, writing RAII classes
- [[C++/Smart Pointers]] — unique_ptr, shared_ptr, weak_ptr, custom deleters
- [[C++/Move Semantics]] — lvalue/rvalue, move constructor, std::move, Rule of Five
- [[C++/Virtual Functions]] — vtable, override, pure virtual, virtual destructor, slicing
- [[C++/Templates]] — function/class templates, specialization, SFINAE, type traits
- [[C++/STL Containers]] — vector, map, unordered_map, priority_queue, algorithms
- [[C++/Exception Handling]] — hierarchy, custom exceptions, noexcept, safety levels, re-throwing
- [[C++/Inheritance]] — access specifiers, multiple inheritance, diamond problem, virtual inheritance
- [[C++/Operator Overloading]] — all operators, functors, conversion, rcstring example
- [[C++/Type Casting]] — static_cast, dynamic_cast, const_cast, reinterpret_cast
- [[C++/Effective C++ - Meyers]] — Scott Meyers guidelines: RAII, const, Rule of Five, override, noexcept, lambdas, atomic

### C++ Versions
- [[C++/Version Comparison]] — feature timeline table, which standard to target, compiler support
- [[C++/C++11/Overview]] — auto, lambdas, move semantics, smart pointers, threads, nullptr, constexpr
- [[C++/C++14/Overview]] — make_unique, generic lambdas, move capture, return type deduction
- [[C++/C++17/Overview]] — structured bindings, if constexpr, optional, variant, string_view, filesystem
- [[C++/C++20/Overview]] — concepts, ranges, span, format, coroutines, jthread, spaceship operator

## Linux System Programming
- [[Linux/Processes]] — fork, exec, wait, zombies, daemon
- [[Linux/Signals]] — sigaction, async-signal-safety, signalfd, SIGPIPE, SIGUSR1/2
- [[Linux/File Descriptors]] — everything is a file, fd lifecycle, dup, pipe, socketpair
- [[Linux/Threads - pthreads]] — create, mutex, condition variable, rwlock, TLS, pitfalls
- [[Linux/Shared Memory]] — shm_open, mmap MAP_SHARED, POSIX shm, sync requirements
- [[Linux/Semaphores]] — sem_init, named semaphores, counting semaphores, producer/consumer
- [[Linux/mmap]] — file-backed mapping, anonymous mapping, msync, madvise, MAP_SHARED

## Networking
- [[Networking/Overview]] — bottom-up: physical → Ethernet → IP → TCP/UDP → TLS → HTTP/DNS
- [[Networking/Sockets TCP]] — TCP socket API, RecvAll loop, wire protocol, byte ordering
- [[Networking/UDP Sockets]] — UDP vs TCP, message boundaries, MTU, broadcast, multicast
- [[Networking/epoll]] — select vs poll vs epoll, level vs edge triggered, Reactor pattern
- [[Networking/IPC Overview]] — all IPC: pipes, socketpair, unix sockets, shared memory, mq

## Memory Management
- [[Memory/Process Memory Layout]] — text, data, BSS, heap, stack, virtual memory
- [[Memory/Stack vs Heap]] — comparison, how each works, when to use each
- [[Memory/Memory Errors and Tools]] — leak, use-after-free, double free, overflow, ASan, Valgrind

## Build Process
- [[Build Process]] — pipeline overview, static vs shared libs, dlopen, compiler flags, Make, tools
- [[Build Process/1 - Preprocessor]] — #include, #define, header guards, conditional compilation
- [[Build Process/2 - Compiler]] — parsing, type checking, optimization levels, template instantiation
- [[Build Process/3 - Assembler]] — assembly → object file, ELF format, symbol table, relocations
- [[Build Process/4 - Linker]] — symbol resolution, static vs dynamic linking, PLT/GOT, common errors

## Design Patterns
- [[Design Patterns/Singleton]] — one instance, thread-safe construction, testability tradeoff
- [[Design Patterns/Factory]] — create objects via interface, dependency inversion, unique_ptr ownership
- [[Design Patterns/Observer]] — publisher/subscriber, thread-safe notify, weak_ptr observers
- [[Design Patterns/Command]] — encapsulate requests, work queues, undo/redo, lambda shortcut
- [[Design Patterns/Reactor]] — epoll event loop, handler dispatch, LDS single-threaded model
- [[Design Patterns/Strategy]] — swappable algorithms at runtime, IStorage as strategy in LDS

## Concurrency
- [[Concurrency/Multithreading Patterns]] — thread pool, producer/consumer, lock hierarchy, futures
- [[Concurrency/Memory Ordering]] — happens-before, std::atomic, acquire/release, CAS, false sharing

## Algorithms
- [[Algorithms/Data Structures]] — array, linked list, hash table, BST, heap/priority queue — complexity + C++ STL type for each
- [[Algorithms/Big-O and Complexity]] — time/space complexity, recognising O(n log n) vs O(n²), binary search, interview patterns

## DevOps & Tools
- [[DevOps/Docker]] — images, containers, Dockerfile, volumes, docker-compose — LDS Docker setup
- [[Linux/gdb Debugging]] — breakpoints, watchpoints, backtrace, core dumps, multi-thread debugging
- [[Kernel]] — syscalls, scheduler, virtual memory, kernel modules — the OS layer your code runs on

## Interview Prep
*Stored in LDS vault (LDS context is the interview story):*
- [[LDS/Engineering/Interview Guide]] — 3-min pitch, cold Q&A, bugs to mention
- [[LDS/Engineering/Interview - C++ Language]] — interview-focused Q&A on C++ fundamentals
- [[LDS/Engineering/Interview - Concurrency]] — mutex, race conditions, deadlock, condition variables
- [[LDS/Engineering/Interview - Linux & Networking]] — fork/exec, signals, epoll, TCP, byte ordering
- [[LDS/Engineering/Interview - Data Structures]] — Big-O, heap PQ, hash table, trie, UID design
