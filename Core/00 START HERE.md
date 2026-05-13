# 00 START HERE — Core Systems Engineering

The central question: **how does a Linux system actually live and execute?**

Not APIs. Not definitions. What happens, step by step, while a process is running.

---

## Start from a runtime question

### What happens when you run `./program`?
→ [[Domains/00 - Build Process/Theory/04 - Linker]] — how the binary was assembled from .o files
→ [[Domains/04 - Linux/Theory/01 - Processes]] — exec(), fork(), process image loaded by kernel
→ [[Domains/01 - Memory/Theory/01 - Process Memory Layout]] — where text/data/BSS/heap/stack land in virtual memory
**→ See it all connected:** [[Runtime Machines/Fork and Exec — The Machine]] — fork() CoW → exec() ELF → dynamic linker → .init_array → main()
**→ Or just the startup detail:** [[Runtime Machines/Program Startup — The Machine]] — exec() → ELF loader → dynamic linker → main()

---

### What happens when `malloc()` is called?
→ [[Domains/02 - C/Theory/02 - Memory - malloc and free]] — the allocator, brk(), mmap()
→ [[Domains/01 - Memory/Theory/02 - Stack vs Heap]] — why the heap is needed at all
→ [[Domains/01 - Memory/Theory/03 - Virtual Memory]] — pages, page faults, the kernel's role
→ [[Domains/03 - C++/Mental Models/24 - Allocators — The Machine]] — ptmalloc2 free bins, arena/pool/tcmalloc patterns
→ [[Domains/01 - Memory/Mental Models/10 - Allocators and Memory Pools — The Machine]] — chunk layout, fragmentation, multi-threaded arenas
**→ See it all connected:** [[Runtime Machines/Memory System — The Machine]] — malloc → brk/mmap → page fault → TLB miss → cache miss
**→ The page fault in detail:** [[Runtime Machines/Page Fault — The Machine]] — #PF handler → allocate physical page → TLB fill → resume

---

### What happens when a virtual function is called?
→ [[Domains/03 - C++/Mental Models/18 - VTables — The Machine]] — vptr at offset 0, vtable in .rodata, three-instruction dispatch
→ [[Domains/03 - C++/Mental Models/19 - Object Layout — The Machine]] — struct padding, EBO, multiple inheritance pointer adjustment
→ [[Domains/01 - Memory/Mental Models/09 - Cache Hierarchy — The Machine (deep)]] — vtable in .rodata, cache miss on cold indirect call
**→ See it all connected:** [[Runtime Machines/Virtual Dispatch — The Machine]] — construction sets vptr, three-instruction dispatch, cold miss, devirtualization
**→ Full object story:** [[Runtime Machines/C++ Object Lifetime — The Machine]] — ctor → vptr → use → exception → dtor

---

### What happens when a thread starts?
→ [[Domains/04 - Linux/Theory/04 - Threads - pthreads]] — clone(), new kernel stack, TLS allocation
→ [[Domains/04 - Linux/Mental Models/10 - Context Switch — The Machine]] — timer interrupt → save registers → scheduler picks next → load new state
→ [[Domains/04 - Linux/Mental Models/11 - Scheduler — The Machine]] — CFS red-black tree, vruntime, TIF_NEED_RESCHED preemption
→ [[Domains/05 - Concurrency/Theory/01 - Multithreading Patterns]] — thread pool, work queue
→ [[Domains/05 - Concurrency/Theory/02 - Memory Ordering]] — what "visible to another thread" actually means
**→ See it all connected:** [[Runtime Machines/Concurrency Runtime — The Machine]] — spawn → futex contention → mutex → wake cycle

---

### What happens when `epoll_wait()` wakes?
→ [[Domains/06 - Networking/Theory/04 - epoll]] — edge-triggered vs level-triggered, kernel internals
→ [[Domains/07 - Design Patterns/Theory/01 - Reactor]] — Reactor pattern: epoll as event demultiplexer
→ [[Domains/04 - Linux/Theory/02 - File Descriptors]] — everything is a file descriptor
**→ See it all connected:** [[Runtime Machines/Networking Stack — The Machine]] — NIC DMA → softirq → socket lookup → epoll ready list → Reactor dispatch → ThreadPool

---

### What happens when a UDP packet arrives?
→ [[Domains/06 - Networking/Theory/03 - UDP Sockets]] — socket buffer, recvfrom, no connection state
→ [[Domains/06 - Networking/Theory/01 - Overview]] — the full networking stack picture
→ [[Domains/06 - Networking/Mental Models/03 - UDP Sockets — The Machine]]
**→ See it all connected:** [[Runtime Machines/Networking Stack — The Machine]] — NIC DMA → IP/UDP demux → sk_buff → recvfrom returns

---

### What happens when a `std::vector` reallocates?
→ [[Domains/03 - C++/Mental Models/17 - std::vector — The Machine]] — 2x growth, move_if_noexcept, iterator invalidation
→ [[Domains/03 - C++/Mental Models/21 - Move Semantics — The Machine (deep)]] — why noexcept on move matters: missing it means copies, not moves
→ [[Domains/01 - Memory/Mental Models/09 - Cache Hierarchy — The Machine (deep)]] — why sequential vector beats linked list 100x
**→ See it all connected:** [[Runtime Machines/Memory System — The Machine]] — malloc new block → move elements → cache-warm sequential layout

---

### What happens when two threads share a struct?
→ [[Domains/05 - Concurrency/Mental Models/03 - False Sharing — The Machine]] — MESI protocol, 64-byte cache line fights between cores
→ [[Domains/05 - Concurrency/Mental Models/04 - Atomics — The Machine]] — lock xadd, acquire/release semantics, CAS
→ [[Domains/05 - Concurrency/Mental Models/02 - Memory Ordering — The Machine]] — what the CPU is allowed to reorder and when
**→ See it all connected:** [[Runtime Machines/Concurrency Runtime — The Machine]] — WPQ push/pop, futex fast path, cache coherence traffic

---

### What happens when an exception is thrown?
→ [[Domains/03 - C++/Mental Models/20 - Exception Unwinding — The Machine]] — .eh_frame lookup, __cxa_throw, destructor per stack frame
→ [[Domains/03 - C++/Mental Models/01 - RAII — The Machine]] — why destructors always run: zero-cost until thrown, then RAII saves you
→ [[Domains/03 - C++/Theory/09 - Exception Handling]] — exception safety levels, noexcept, destructor rules
**→ See it all connected:** [[Runtime Machines/C++ Object Lifetime — The Machine]] — throw → unwind → RAII destructors fire in reverse order → catch

---

### What happens when a `shared_ptr` is copied?
→ [[Domains/03 - C++/Mental Models/22 - shared_ptr — The Machine]] — control block layout, atomic strong count, deleter, make_shared optimization
→ [[Domains/03 - C++/Mental Models/25 - weak_ptr — The Machine]] — non-owning observer, lock() CAS atomicity, expired() TOCTOU race
→ [[Domains/03 - C++/Mental Models/21 - Move Semantics — The Machine (deep)]] — why move costs 1ns but copy costs 5-300ns (atomic vs pointer assign)
**→ See it all connected:** [[Runtime Machines/C++ Object Lifetime — The Machine]] — shared ownership across threads, last ref destroys, weak_ptr lock() on destruction

---

### What happens at end of scope (RAII)?
→ [[Domains/03 - C++/Theory/01 - RAII]] — destructor timing, stack unwinding order
→ [[Domains/03 - C++/Theory/02 - Smart Pointers]] — unique_ptr/shared_ptr destruction
→ [[Domains/03 - C++/Mental Models/23 - Copy Elision — The Machine]] — RVO/NRVO: why the object is often built in-place with zero copy/move
**→ See it all connected:** [[Runtime Machines/C++ Object Lifetime — The Machine]] — ctor → vptr → use → move → dtor, every transition

---

## Guided paths (ordered study)

→ [[Portals/01 - Learn Systems Engineering]] — full layered curriculum, bottom to top
→ [[Portals/02 - Build Runtime Intuition]] — execution stories for every component
→ [[Portals/03 - Study Tradeoffs]] — why each design decision was made
→ [[Portals/04 - Interview Preparation]] — interview-ready in sequence

---

## Runtime Machines (all entry points)

**Start here to see how everything connects:**
→ [[Runtime Machines/Linux Runtime — The Machine]] — the map: all 6 subsystems (memory, MMU, scheduler, threads, fds, networking) and how they interact

**Zoom in on a subsystem:**
→ [[Runtime Machines/Fork and Exec — The Machine]] — fork() CoW page tables → exec() ELF load → dynamic linker → main()
→ [[Runtime Machines/Program Startup — The Machine]] — exec() → constructors → main() (detailed linker path)
→ [[Runtime Machines/Page Fault — The Machine]] — #PF handler → demand paging → CoW → file-backed → stack growth
→ [[Runtime Machines/Memory System — The Machine]] — malloc → brk/mmap → page fault → TLB miss → cache miss
→ [[Runtime Machines/Networking Stack — The Machine]] — NIC DMA → softirq → socket lookup → epoll → handler
→ [[Runtime Machines/Concurrency Runtime — The Machine]] — thread spawn → futex fast path → mutex contention → wakeup
→ [[Runtime Machines/Virtual Dispatch — The Machine]] — vptr → vtable → indirect call, cold miss, devirtualization
→ [[Runtime Machines/C++ Object Lifetime — The Machine]] — ctor sets vptr → use → exception unwind → dtor
→ [[Runtime Machines/Request Lifecycle — The Machine]] — LDS: NBD → Reactor → RAID → UDP reply

---

## Jump directly to a domain

→ **[[Domains/00 - Build Process]]** — preprocessor · compiler · assembler · linker · make
→ **[[Domains/01 - Memory]]** — layout · heap · virtual memory · paging · MMU · TLB · cache · allocators
→ **[[Domains/02 - C]]** — pointers · malloc · strings · structs · file IO · bitwise · serialization
→ **[[Domains/03 - C++]]** — RAII · smart ptrs · move · vtables · object layout · exception unwinding · STL · allocators · copy elision · versions
→ **[[Domains/04 - Linux]]** — processes · fds · signals · threads · context switch · scheduler · mmap · kernel · gdb
→ **[[Domains/05 - Concurrency]]** — threading patterns · memory ordering · false sharing · atomics
→ **[[Domains/06 - Networking]]** — sockets · TCP · UDP · epoll · IPC · tradeoffs
→ **[[Domains/07 - Design Patterns]]** — Reactor · Observer · Singleton · Factory · Command · Strategy
→ **[[Domains/08 - Algorithms]]** — data structures · Big-O
→ **[[Domains/09 - DevOps]]** — Docker

---

## Quick vocabulary
→ [[Glossary/16 - epoll]] · [[Glossary/12 - TCP]] · [[Glossary/14 - UDP]] · [[Glossary/11 - RAII]] · [[Glossary/13 - Templates]] · [[Glossary/17 - pthreads]] · [[Glossary/18 - shared_ptr]] · [[Glossary/15 - VFS]] · [[Glossary/19 - socketpair]]
