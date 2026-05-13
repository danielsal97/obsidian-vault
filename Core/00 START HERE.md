# 00 START HERE — Core Systems Engineering

The central question: **how does a Linux system actually live and execute?**

Not APIs. Not definitions. What happens, step by step, while a process is running.

---

## Start from a runtime question

### What happens when you run `./program`?
→ [[Domains/00 - Build Process/Theory/04 - Linker]] — how the binary was assembled
→ [[Domains/04 - Linux/Theory/01 - Processes]] — exec(), fork(), process image loaded
→ [[Domains/01 - Memory/Theory/01 - Process Memory Layout]] — where code, stack, heap land in virtual memory
→ [[Runtime Machines/Program Startup — The Machine]] — step-by-step execution from exec() to main()

### What happens when `malloc()` is called?
→ [[Domains/02 - C/Theory/02 - Memory - malloc and free]] — the allocator, brk(), mmap()
→ [[Domains/01 - Memory/Theory/02 - Stack vs Heap]] — why the heap is needed at all
→ [[Domains/01 - Memory/Theory/03 - Virtual Memory]] — pages, page faults, the kernel's role
→ [[Runtime Machines/Memory System — The Machine]] — page fault → TLB miss → cache miss, live

### What happens when a thread starts?
→ [[Domains/04 - Linux/Theory/04 - Threads - pthreads]] — clone(), stack allocation, kernel scheduling
→ [[Domains/04 - Linux/Mental Models/10 - Context Switch — The Machine]] — timer interrupt → save registers → scheduler picks next → load new state
→ [[Domains/04 - Linux/Mental Models/11 - Scheduler — The Machine]] — CFS red-black tree, vruntime, TIF_NEED_RESCHED preemption
→ [[Domains/05 - Concurrency/Theory/01 - Multithreading Patterns]] — thread pool, work queue
→ [[Domains/05 - Concurrency/Theory/02 - Memory Ordering]] — what "visible to another thread" actually means
→ [[Runtime Machines/Concurrency Runtime — The Machine]] — spawn → mutex contention → wake cycle

### What happens when `epoll_wait()` wakes?
→ [[Domains/06 - Networking/Theory/04 - epoll]] — edge-triggered vs level-triggered, kernel internals
→ [[Domains/07 - Design Patterns/Theory/01 - Reactor]] — Reactor pattern: epoll as event demultiplexer
→ [[Domains/04 - Linux/Theory/02 - File Descriptors]] — everything is a file descriptor
→ [[Runtime Machines/Networking Stack — The Machine]] — packet arrives → fd ready → dispatch cycle

### What happens when a UDP packet arrives?
→ [[Domains/06 - Networking/Theory/03 - UDP Sockets]] — socket buffer, recvfrom, no connection state
→ [[Domains/06 - Networking/Theory/01 - Overview]] — the full networking stack picture
→ [[Domains/06 - Networking/Mental Models/03 - UDP Sockets — The Machine]]

### What happens when a `std::vector` reallocates?
→ [[Domains/03 - C++/Mental Models/17 - std::vector — The Machine]] — 2x growth, move_if_noexcept, iterator invalidation
→ [[Domains/03 - C++/Mental Models/21 - Move Semantics — The Machine (deep)]] — why noexcept on move matters here
→ [[Domains/01 - Memory/Mental Models/09 - Cache Hierarchy — The Machine (deep)]] — why sequential vector beats linked list 100x

### What happens when two threads share a struct?
→ [[Domains/05 - Concurrency/Mental Models/03 - False Sharing — The Machine]] — MESI protocol, 64-byte cache line fights
→ [[Domains/05 - Concurrency/Mental Models/04 - Atomics — The Machine]] — lock xadd, acquire/release, CAS
→ [[Domains/05 - Concurrency/Mental Models/02 - Memory Ordering — The Machine]] — what the CPU is allowed to reorder

### What happens when an exception is thrown?
→ [[Domains/03 - C++/Mental Models/20 - Exception Unwinding — The Machine]] — .eh_frame, __cxa_throw, destructor calls per frame
→ [[Domains/03 - C++/Mental Models/23 - Copy Elision — The Machine]] — why `return std::move(x)` is wrong (disables NRVO)
→ [[Domains/03 - C++/Mental Models/01 - RAII — The Machine]] — why destructors run during unwind

### What happens at end of scope (RAII)?
→ [[Domains/03 - C++/Theory/01 - RAII]] — destructor timing, stack unwinding
→ [[Domains/03 - C++/Theory/02 - Smart Pointers]] — unique_ptr/shared_ptr destruction
→ [[Domains/03 - C++/Mental Models/22 - shared_ptr — The Machine]] — control block, atomic ref count, weak_ptr cycle breaking
→ [[Domains/03 - C++/Mental Models/25 - weak_ptr — The Machine]] — non-owning observer, lock() CAS, expired() race
→ [[Runtime Machines/C++ Object Lifetime — The Machine]] — ctor → use → dtor, live

---

## Guided paths (ordered study)

→ [[Portals/01 - Learn Systems Engineering]] — full layered curriculum, bottom to top
→ [[Portals/02 - Build Runtime Intuition]] — execution stories for every component
→ [[Portals/03 - Study Tradeoffs]] — why each design decision was made
→ [[Portals/04 - Interview Preparation]] — interview-ready in sequence

---

## Runtime Machines (high-level entry points)

→ [[Runtime Machines/Linux Runtime — The Machine]] — how Linux runs a process end to end
→ [[Runtime Machines/Program Startup — The Machine]] — exec() → constructors → main()
→ [[Runtime Machines/Memory System — The Machine]] — malloc → page fault → cache hierarchy
→ [[Runtime Machines/Networking Stack — The Machine]] — packet → fd → epoll → handler
→ [[Runtime Machines/Concurrency Runtime — The Machine]] — thread spawn → mutex → wakeup
→ [[Runtime Machines/C++ Object Lifetime — The Machine]] — ctor → move → dtor
→ [[Runtime Machines/Request Lifecycle — The Machine]] — LDS: NBD → Reactor → RAID → UDP reply

---

## Jump directly to a domain

→ **[[Domains/00 - Build Process]]** — preprocessor · compiler · assembler · linker · make
→ **[[Domains/01 - Memory]]** — layout · heap · virtual memory · paging · MMU · TLB · cache
→ **[[Domains/02 - C]]** — pointers · malloc · strings · structs · file IO · bitwise · serialization
→ **[[Domains/03 - C++]]** — RAII · smart ptrs · move · vtables · object layout · exception unwinding · STL · allocators · versions
→ **[[Domains/04 - Linux]]** — processes · fds · signals · threads · context switch · scheduler · mmap · kernel · gdb
→ **[[Domains/05 - Concurrency]]** — threading patterns · memory ordering · false sharing · atomics
→ **[[Domains/06 - Networking]]** — sockets · TCP · UDP · epoll · IPC · tradeoffs
→ **[[Domains/07 - Design Patterns]]** — Reactor · Observer · Singleton · Factory · Command · Strategy
→ **[[Domains/08 - Algorithms]]** — data structures · Big-O
→ **[[Domains/09 - DevOps]]** — Docker

---

## Quick vocabulary
→ [[Glossary/16 - epoll]] · [[Glossary/12 - TCP]] · [[Glossary/14 - UDP]] · [[Glossary/11 - RAII]] · [[Glossary/13 - Templates]] · [[Glossary/17 - pthreads]] · [[Glossary/18 - shared_ptr]] · [[Glossary/15 - VFS]] · [[Glossary/19 - socketpair]]
