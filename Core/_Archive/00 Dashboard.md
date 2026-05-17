# Engineering Notes

General knowledge that carries across every project and every job.

---

## C Language
- [[01 - Pointers]] — pointer arithmetic, double pointers, function pointers, void*, const
- [[03 - Strings]] — null terminator, safe copy, sprintf, common bugs
- [[04 - Structs and Unions]] — memory layout, padding, opaque pointers, bit fields, unions
- [[02 - Memory - malloc and free]] — how malloc works, fragmentation, custom allocators, tools
- [[08 - Undefined Behavior]] — what UB is, common sources, why it's dangerous, sanitizers
- [[06 - Bitwise Operations]] — AND/OR/XOR/shift, masking patterns, byte reversal, GCC builtins
- [[07 - Serialization]] — manual serialization, packed structs, byte order, length-prefix framing
- [[05 - File IO]] — POSIX open/read/write/lseek, stdio, flags, errno, atomic write pattern

## C++
- [[01 - RAII]] — resource lifetimes, destructors, stack unwinding, writing RAII classes
- [[02 - Smart Pointers]] — unique_ptr, shared_ptr, weak_ptr, custom deleters
- [[03 - Move Semantics]] — lvalue/rvalue, move constructor, std::move, Rule of Five
- [[06 - Virtual Functions]] — vtable, override, pure virtual, virtual destructor, slicing
- [[04 - Templates]] — function/class templates, specialization, SFINAE, type traits
- [[08 - STL Containers]] — vector, map, unordered_map, priority_queue, algorithms
- [[09 - Exception Handling]] — hierarchy, custom exceptions, noexcept, safety levels, re-throwing
- [[05 - Inheritance]] — access specifiers, multiple inheritance, diamond problem, virtual inheritance
- [[07 - Operator Overloading]] — all operators, functors, conversion, rcstring example
- [[10 - Type Casting]] — static_cast, dynamic_cast, const_cast, reinterpret_cast
- [[11 - Effective C++ - Meyers]] — Scott Meyers guidelines: RAII, const, Rule of Five, override, noexcept, lambdas, atomic

### C++ Versions
- [[C++/Version Comparison]] — feature timeline table, which standard to target, compiler support
- [[C++/C++11/Overview]] — auto, lambdas, move semantics, smart pointers, threads, nullptr, constexpr
- [[C++/C++14/Overview]] — make_unique, generic lambdas, move capture, return type deduction
- [[C++/C++17/Overview]] — structured bindings, if constexpr, optional, variant, string_view, filesystem
- [[C++/C++20/Overview]] — concepts, ranges, span, format, coroutines, jthread, spaceship operator

## Linux System Programming
- [[01 - Processes]] — fork, exec, wait, zombies, daemon
- [[03 - Signals]] — sigaction, async-signal-safety, signalfd, SIGPIPE, SIGUSR1/2
- [[02 - File Descriptors]] — everything is a file, fd lifecycle, dup, pipe, socketpair
- [[04 - Threads - pthreads]] — create, mutex, condition variable, rwlock, TLS, pitfalls
- [[05 - Shared Memory]] — shm_open, mmap MAP_SHARED, POSIX shm, sync requirements
- [[06 - Semaphores]] — sem_init, named semaphores, counting semaphores, producer/consumer
- [[07 - mmap]] — file-backed mapping, anonymous mapping, msync, madvise, MAP_SHARED

## Networking
- [[01 - Overview]] — bottom-up: physical → Ethernet → IP → TCP/UDP → TLS → HTTP/DNS
- [[02 - Sockets TCP]] — TCP socket API, RecvAll loop, wire protocol, byte ordering
- [[03 - UDP Sockets]] — UDP vs TCP, message boundaries, MTU, broadcast, multicast
- [[04 - epoll]] — select vs poll vs epoll, level vs edge triggered, Reactor pattern
- [[05 - IPC Overview]] — all IPC: pipes, socketpair, unix sockets, shared memory, mq

## Memory Management
- [[01 - Process Memory Layout]] — text, data, BSS, heap, stack, virtual memory
- [[02 - Stack vs Heap]] — comparison, how each works, when to use each
- [[09 - Memory Errors and Tools]] — leak, use-after-free, double free, overflow, ASan, Valgrind

## Build Process
- [[Build Process]] — pipeline overview, static vs shared libs, dlopen, compiler flags, Make, tools
- [[01 - Preprocessor]] — #include, #define, header guards, conditional compilation
- [[02 - Compiler]] — parsing, type checking, optimization levels, template instantiation
- [[03 - Assembler]] — assembly → object file, ELF format, symbol table, relocations
- [[04 - Linker]] — symbol resolution, static vs dynamic linking, PLT/GOT, common errors

## Design Patterns
- [[03 - Singleton]] — one instance, thread-safe construction, testability tradeoff
- [[04 - Factory]] — create objects via interface, dependency inversion, unique_ptr ownership
- [[02 - Observer]] — publisher/subscriber, thread-safe notify, weak_ptr observers
- [[05 - Command]] — encapsulate requests, work queues, undo/redo, lambda shortcut
- [[01 - Reactor]] — epoll event loop, handler dispatch, LDS single-threaded model
- [[06 - Strategy]] — swappable algorithms at runtime, IStorage as strategy in LDS

## Concurrency
- [[01 - Multithreading Patterns]] — thread pool, producer/consumer, lock hierarchy, futures
- [[02 - Memory Ordering]] — happens-before, std::atomic, acquire/release, CAS, false sharing

## Algorithms
- [[01 - Data Structures]] — array, linked list, hash table, BST, heap/priority queue — complexity + C++ STL type for each
- [[02 - Big-O and Complexity]] — time/space complexity, recognising O(n log n) vs O(n²), binary search, interview patterns

## DevOps & Tools
- [[01 - Docker]] — images, containers, Dockerfile, volumes, docker-compose — LDS Docker setup
- [[Linux/09 - gdb Debugging]] — breakpoints, watchpoints, backtrace, core dumps, multi-thread debugging
- [[Kernel]] — syscalls, scheduler, virtual memory, kernel modules — the OS layer your code runs on

## Interview Prep
*Stored in LDS vault (LDS context is the interview story):*
- [[LDS/Engineering/Interview Guide]] — 3-min pitch, cold Q&A, bugs to mention
- [[LDS/Engineering/Interview - C++ Language]] — interview-focused Q&A on C++ fundamentals
- [[LDS/Engineering/Interview - Concurrency]] — mutex, race conditions, deadlock, condition variables
- [[LDS/Engineering/Interview - Linux & Networking]] — fork/exec, signals, epoll, TCP, byte ordering
- [[LDS/Engineering/Interview - Data Structures]] — Big-O, heap PQ, hash table, trie, UID design
