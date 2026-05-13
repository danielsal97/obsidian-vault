# Learning Curriculum

True bottom-up order. Each topic builds on the previous.
Never move to the next layer until the current one is solid.
Every line is a link — no content here, just the path.

**Total:** 57 topics (~42 hrs)

---

## Layer 0 — How Code Becomes a Running Program (Week 1, ~3.5 hrs)

*Start here. Before you write a single line of C or C++, understand the full pipeline from `.cpp` to running process. This gives you the mental model that makes every compiler error, linker error, and "why is this in a header?" question instantly answerable.*

| # | Topic | Est. | What you learn |
|---|---|---|---|
| 0 | [[Engineering/Build Process]] | 30 min | The full pipeline overview, compiler flags, Make, static vs shared libs, dlopen |
| 1 | [[Engineering/Build Process/01 - Preprocessor\|Preprocessor]] | 30 min | What `#include` does, header guards, macros, why duplicate-include bugs happen |
| 2 | [[Engineering/Build Process/02 - Compiler\|Compiler]] | 45 min | Parsing, type checking, optimization levels, why templates must be in headers |
| 3 | [[Engineering/Build Process/03 - Assembler\|Assembler]] | 30 min | `.o` files, ELF format, symbol table — what the linker sees |
| 4 | [[Engineering/Build Process/04 - Linker\|Linker]] | 45 min | Symbol resolution, static vs dynamic linking, PLT/GOT, undefined reference errors |
| 5 | [[Engineering/Build Process/05 - Make and CMake\|Make and CMake]] | 45 min | Makefile rules, variables, `-MMD` dependency tracking, CMakeLists.txt, out-of-source builds |

---

## Layer 1 — Memory: Where Everything Lives (Week 1, ~2.5 hrs)

*Before pointers, before malloc, before the heap — understand the map of memory your program runs in. Once you can draw this from memory, everything in C and C++ becomes obvious.*

| # | Topic | Est. | What you learn |
|---|---|---|---|
| 5 | [[Engineering/Memory/01 - Process Memory Layout\|Process Memory Layout]] | 45 min | Text, data, BSS, heap, stack — every variable has a home; where LDS's Reactor, workers, and storage live |
| 6 | [[Engineering/Memory/02 - Stack vs Heap\|Stack vs Heap]] | 45 min | Stack: automatic, LIFO, O(1), destroyed on return. Heap: manual, persistent, fragmentation risk |
| 7 | [[Engineering/C/02 - Memory - malloc and free\|malloc and free]] | 45 min | How `malloc` actually works internally — free list, coalescing, hidden header; what `new`/`delete` sit on top of |

---

## Layer 2 — C Language: The Metal (Week 2, ~6 hrs)

*C is the foundation of C++. Every pointer, every struct layout, every byte on the wire — this is where it all lives. Study C before C++ or the abstractions are floating in air.*

| # | Topic | Est. | What you learn |
|---|---|---|---|
| 8 | [[Engineering/C/01 - Pointers\|Pointers]] | 1 hr | A pointer IS a memory address. Arithmetic, double pointers, function pointers, const positions, void*, NULL safety |
| 9 | [[Engineering/C/04 - Structs and Unions\|Structs and Unions]] | 30 min | Memory layout, padding, largest-first rule, opaque pointers, unions for type-punning |
| 10 | [[Engineering/C/06 - Bitwise Operations\|Bitwise Operations]] | 45 min | AND/OR/XOR/shift, bit masking, signed vs unsigned rules — how LDS packs protocol fields |
| 11 | [[Engineering/C/03 - Strings\|Strings]] | 45 min | Null terminator, `strncpy` trap, `strcmp` vs `==`, safe buffer handling, `snprintf` |
| 12 | [[Engineering/C/05 - File IO\|File IO]] | 30 min | POSIX `open`/`read`/`write`/`lseek`, `pread`/`pwrite`, `errno`, crash-safe write pattern |
| 13 | [[Engineering/C/07 - Serialization\|Serialization]] | 1 hr | Big-endian vs little-endian, `htonl`/`ntohl`, `memcpy` for misalignment safety, length-prefix framing — the LDS wire protocol |
| 14 | [[Engineering/C/08 - Undefined Behavior\|Undefined Behavior]] | 1 hr | What UB is, why `-O2` exposes bugs `-O0` hides, strict aliasing, data races as UB — not just wrong values |

### Algorithms (study alongside C — you need arrays and structs first)
| # | Topic | Est. | What you learn |
|---|---|---|---|
| 15 | [[Engineering/Algorithms/02 - Big-O and Complexity\|Big-O and Complexity]] | 45 min | How to measure algorithmic efficiency, drop constants, recognise O(n²) vs O(n log n) in code |
| 16 | [[Engineering/Algorithms/01 - Data Structures\|Data Structures]] | 1.5 hrs | Array, linked list, hash table, BST, heap/priority queue — complexity + C++ STL type for each |

---

## Layer 3 — Linux: How the OS Runs Your Program (Week 2–3, ~4 hrs)

*Your program doesn't run in a vacuum. The OS gives it fds, a process, signals, and memory pages. Know this before writing C++ that touches any of it.*

| # | Topic | Est. | What you learn |
|---|---|---|---|
| 17 | [[Engineering/Linux/02 - File Descriptors\|File Descriptors]] | 45 min | Everything is a file. fd lifecycle, dup, socketpair, `FD_CLOEXEC`, fd leak consequences |
| 18 | [[Engineering/Linux/01 - Processes\|Processes]] | 45 min | `fork`/`exec`/`wait`, copy-on-write, zombies, daemon pattern, `WNOHANG` in watchdog |
| 19 | [[Engineering/Linux/03 - Signals\|Signals]] | 45 min | `sigaction`, async-signal-safe functions, `signalfd`, why LDS Reactor uses signalfd not sigaction |
| 20 | [[Engineering/Memory/09 - Memory Errors and Tools\|Memory Errors and Tools]] | 45 min | Use-after-free, double-free, leak, overflow — and how ASan/Valgrind/UBSan catch each one |
| 21 | [[Engineering/Kernel\|Kernel Concepts]] | 45 min | What the kernel does: syscalls, scheduler, virtual memory, kernel modules — the OS layer your code runs on |
| 22 | [[Engineering/Linux/09 - gdb Debugging\|gdb Debugging]] | 1 hr | Breakpoints, watchpoints, backtrace, core dumps, multi-thread debugging — how to actually debug a crash |

---

## Layer 4 — C++ Core (Week 3–4, ~9 hrs)

*Now the abstractions have a foundation. RAII = stack unwinding + destructors. Smart pointers = RAII for heap. Move semantics = ownership via pointers. Virtual functions = vtable = pointer to function table.*

### Ownership & Lifetime
| # | Topic | Est. | What you learn |
|---|---|---|---|
| 19 | [[Engineering/C++/01 - RAII\|RAII]] | 45 min | Resource lifetime = object lifetime. Stack unwinding runs destructors. No manual cleanup |
| 20 | [[Engineering/C++/02 - Smart Pointers\|Smart Pointers]] | 45 min | `unique_ptr` = RAII wrapper for heap. `shared_ptr` = ref-counted. `weak_ptr` = non-owning |
| 21 | [[Engineering/C++/03 - Move Semantics\|Move Semantics]] | 45 min | lvalue vs rvalue, `std::move` is just a cast, move constructor nulls the source pointer |

### Type System & Polymorphism
| # | Topic | Est. | What you learn |
|---|---|---|---|
| 22 | [[Engineering/C++/06 - Virtual Functions\|Virtual Functions]] | 45 min | vtable = array of function pointers. `override`, pure virtual, virtual destructor, object slicing |
| 23 | [[Engineering/C++/05 - Inheritance\|Inheritance]] | 45 min | Access specifiers, construction order, multiple inheritance, diamond problem, when to use composition |
| 24 | [[Engineering/C++/04 - Templates\|Templates]] | 45 min | Compile-time polymorphism, instantiation in headers, SFINAE, type traits — `Dispatcher<T>` in LDS |
| 25 | [[Engineering/C++/08 - STL Containers\|STL Containers]] | 45 min | `vector`, `map`, `unordered_map`, `priority_queue` — iterator invalidation, complexity guarantees |
| 26 | [[Engineering/C++/09 - Exception Handling\|Exception Handling]] | 45 min | `try`/`catch`/`throw`, exception hierarchy, `noexcept`, stack unwinding fires RAII destructors |
| 27 | [[Engineering/C++/07 - Operator Overloading\|Operator Overloading]] | 30 min | Canonical forms, copy-and-swap, `operator+=` as the primitive |
| 28 | [[Engineering/C++/10 - Type Casting\|Type Casting]] | 45 min | `static_cast`, `dynamic_cast`, `const_cast`, `reinterpret_cast` — when each is correct |
| 29 | [[Engineering/C++/11 - Effective C++ - Meyers\|Effective C++ — Meyers]] | 1 hr | Synthesis: all the non-obvious rules that senior devs follow automatically |

### C++ Versions (study after the core — now you know what was missing before each standard)
| # | Topic | Est. | What you learn |
|---|---|---|---|
| 30 | [[Engineering/C++/Version Comparison\|C++ Version Comparison]] | 30 min | Feature timeline table — what landed in which standard, what to target |
| 31 | [[Engineering/C++/C++11/Overview\|C++11]] | 30 min | auto, lambdas, move semantics, smart pointers, threads, nullptr, constexpr, range-for |
| 32 | [[Engineering/C++/C++14/Overview\|C++14]] | 15 min | make_unique, generic lambdas, move capture, return type deduction |
| 33 | [[Engineering/C++/C++17/Overview\|C++17]] | 30 min | Structured bindings, if constexpr, optional, variant, string_view, filesystem |
| 34 | [[Engineering/C++/C++20/Overview\|C++20]] | 30 min | Concepts, ranges, span, format, coroutines, jthread, spaceship operator — LDS uses C++20 |

---

## Layer 5 — Concurrency (Week 5, ~6 hrs)

*Threads share memory. That one fact causes 90% of bugs. Study the raw API first (pthreads), then the patterns built on it.*

| # | Topic | Est. | What you learn |
|---|---|---|---|
| 30 | [[Engineering/Linux/04 - Threads - pthreads\|Threads — pthreads]] | 1 hr | `pthread_create`, mutex, condition variable (why `while` loop), rwlock, TLS, deadlock patterns |
| 31 | [[Engineering/Concurrency/01 - Multithreading Patterns\|Multithreading Patterns]] | 1 hr | Thread pool, producer/consumer, lock hierarchy, futures — how LDS's ThreadPool + WPQ works |
| 32 | [[Engineering/Concurrency/02 - Memory Ordering\|Memory Ordering]] | 1 hr | Happens-before, `std::atomic`, acquire/release, CAS, false sharing, why `volatile` is wrong here |
| 33 | [[Engineering/Linux/05 - Shared Memory\|Shared Memory]] | 45 min | `shm_open`, `mmap MAP_SHARED`, sync requirement — and why LDS uses sockets instead |
| 34 | [[Engineering/Linux/06 - Semaphores\|Semaphores]] | 45 min | Counting semaphore, `sem_timedwait`, producer/consumer — watchdog heartbeat pattern |
| 35 | [[Engineering/Linux/07 - mmap\|mmap]] | 45 min | File-backed mapping, anonymous mapping, `MAP_PRIVATE`, demand paging, `msync` — alternative to `pread`/`pwrite` |

---

## Layer 6 — Networking (Week 6, ~5 hrs)

*Builds on file descriptors (Layer 3). A socket is just an fd. Read the overview first — it gives you the OSI stack that frames everything else.*

| # | Topic | Est. | What you learn |
|---|---|---|---|
| 36 | [[Engineering/Networking/01 - Overview\|Networking Overview]] | 1 hr | Physical → Ethernet → IP → TCP/UDP → TLS → HTTP — full bottom-up OSI walk |
| 37 | [[Engineering/Networking/02 - Sockets TCP\|Sockets TCP]] | 1 hr | `socket`/`bind`/`listen`/`accept`, `RecvAll` loop, `TCP_NODELAY`, byte ordering — `TCPDriverComm` in LDS |
| 38 | [[Engineering/Networking/03 - UDP Sockets\|UDP Sockets]] | 45 min | No connection, message boundaries, MTU, `MSG_ID` tracking — master↔minion protocol in LDS |
| 39 | [[Engineering/Networking/04 - epoll\|epoll]] | 1 hr | `epoll_create`/`epoll_ctl`/`epoll_wait`, level vs edge triggered, O(1) — the LDS Reactor event loop |
| 40 | [[Engineering/Networking/05 - IPC Overview\|IPC Overview]] | 45 min | All IPC mechanisms compared: pipe, socketpair, unix socket, shared mem, mq — when to use which |

---

## Layer 7 — Design Patterns (Week 7, ~5 hrs)

*You've already built these in LDS. Now put formal names on them and understand the tradeoffs. Study Reactor first — it wraps the epoll you just learned.*

| # | Topic | Est. | What you learn |
|---|---|---|---|
| 41 | [[Engineering/Design Patterns/01 - Reactor\|Reactor]] | 1 hr | Event loop on top of epoll — single thread, all I/O, handler dispatch. You built this |
| 42 | [[Engineering/Design Patterns/02 - Observer\|Observer]] | 45 min | Subject notifies observers without knowing who they are — `Dispatcher<T>`/`CallBack<T>` in LDS |
| 43 | [[Engineering/Design Patterns/05 - Command\|Command]] | 45 min | Encapsulate a request as an object — `ICommand` + priority queue in LDS |
| 44 | [[Engineering/Design Patterns/04 - Factory\|Factory]] | 45 min | Create objects via interface — `CommandFactory` eliminates if/else chains |
| 45 | [[Engineering/Design Patterns/06 - Strategy\|Strategy]] | 45 min | Swappable behaviour at runtime — `IDriverComm` lets you swap NBD ↔ TCP without touching mediator |
| 46 | [[Engineering/Design Patterns/03 - Singleton\|Singleton]] | 30 min | One instance, thread-safe construction via C++11 magic statics — Logger in LDS |

---

## Layer 8 — DevOps & Tools (Week 8, ~1 hr)

*Practical skills that come up in any systems role. Docker is already used in LDS.*

| # | Topic | Est. | What you learn |
|---|---|---|---|
| 57 | [[Engineering/DevOps/01 - Docker\|Docker]] | 1 hr | Images, containers, Dockerfile, volumes, port mapping, docker-compose — LDS Docker setup |

---

## Week 8 — Interview Prep

All 46 done. Now shift to active practice — no new topics, only retrieval and explanation.

1. [[LDS/Engineering/Interview Guide]] — 3-min LDS pitch + cold Q&A. Record yourself.
2. [[LDS/System Overview]] + [[LDS/Request Lifecycle]] — can you explain the full request path end-to-end?
3. [[LDS/Engineering/Known Bugs]] — pick 2–3 bugs as debugging stories ("I noticed X, I traced it to Y, I fixed it by Z")
4. For each design pattern: say out loud *why* you chose it — not what it is, but why it was the right call in LDS
5. [[LDS/Manager/Job Search Plan]] — pitch memorised, applications sending daily
