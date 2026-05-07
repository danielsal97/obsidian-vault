# Engineering Notes

General knowledge that carries across every project and every job.

---

## C Language
- [[C/Pointers]] — pointer arithmetic, double pointers, function pointers, void*, const
- [[C/Strings]] — null terminator, safe copy, sprintf, common bugs
- [[C/Structs and Unions]] — memory layout, padding, opaque pointers, bit fields, unions
- [[C/Memory - malloc and free]] — how malloc works, fragmentation, custom allocators, tools
- [[C/Undefined Behavior]] — what UB is, common sources, why it's dangerous, sanitizers

## C++
- [[C++/RAII]] — resource lifetimes, destructors, stack unwinding, writing RAII classes
- [[C++/Smart Pointers]] — unique_ptr, shared_ptr, weak_ptr, custom deleters
- [[C++/Move Semantics]] — lvalue/rvalue, move constructor, std::move, Rule of Five
- [[C++/Virtual Functions]] — vtable, override, pure virtual, virtual destructor, slicing
- [[C++/Templates]] — function/class templates, specialization, SFINAE, type traits
- [[C++/STL Containers]] — vector, map, unordered_map, priority_queue, algorithms

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
- [[Linux/epoll]] — select vs poll vs epoll, level vs edge triggered, Reactor pattern
- [[Linux/Sockets TCP]] — server/client setup, RecvAll, byte ordering, disconnect

## Memory Management
- [[Memory/Process Memory Layout]] — text, data, BSS, heap, stack, virtual memory
- [[Memory/Stack vs Heap]] — comparison, how each works, when to use each
- [[Memory/Memory Errors and Tools]] — leak, use-after-free, double free, overflow, ASan, Valgrind

## Build Process
- [[Build Process]] — preprocessor → compiler → linker, .o/.a/.so, Make, flags

## Interview Prep
- [[Interview/Interview Guide]] — 3-min pitch, cold Q&A, bugs to mention
- [[Interview/C++ Language]] — interview-focused Q&A on C++ fundamentals
- [[Interview/Concurrency]] — mutex, race conditions, deadlock, condition variables
- [[Interview/Linux & Networking]] — fork/exec, signals, epoll, TCP, byte ordering
- [[Interview/Data Structures]] — Big-O, heap PQ, hash table, trie, UID design
