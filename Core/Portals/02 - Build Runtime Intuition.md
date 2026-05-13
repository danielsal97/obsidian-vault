# Build Runtime Intuition

These notes answer: **"what is the machine doing right now?"**

Organized by runtime moment — pick the moment you want to understand. Each Mental Model is an execution story: what runs, what blocks, what wakes, where time is spent.

---

## Moment 1 — A process starts

The kernel runs `exec()`. Before your first line of code runs, a lot happens.

→ [[../Domains/04 - Linux/Mental Models/01 - Processes — The Machine]] — fork/exec lifecycle, address space setup
→ [[../Domains/01 - Memory/Mental Models/01 - Process Memory Layout — The Machine]] — how text/data/BSS/heap/stack land in virtual memory
→ [[../Domains/00 - Build Process/Mental Models/05 - Linker — The Machine]] — why the dynamic linker runs first to resolve shared library symbols
→ [[../Domains/03 - C++/Mental Models/01 - RAII — The Machine]] — global constructors run before main()

---

## Moment 2 — Code allocates memory

`new Foo()` or `malloc(256)` is called. What actually happens?

→ [[../Domains/02 - C/Mental Models/08 - malloc and free — The Machine]] — allocator finds a free block, calls brk() if heap is exhausted
→ [[../Domains/01 - Memory/Mental Models/02 - Stack vs Heap — The Machine]] — why stack allocation costs nothing but heap requires bookkeeping
→ [[../Domains/01 - Memory/Mental Models/03 - Virtual Memory — The Machine]] — the page isn't real until you touch it (demand paging)
→ [[../Domains/01 - Memory/Mental Models/04 - Paging — The Machine]] — page fault → kernel allocates physical page → resumes
→ [[../Domains/01 - Memory/Mental Models/07 - TLB — The Machine]] — the TLB miss cost when touching a new page
→ [[../Domains/01 - Memory/Mental Models/08 - Cache Hierarchy — The Machine]] — L1/L2/L3 miss cascade on first access

---

## Moment 3 — An I/O event arrives

A socket becomes readable. `epoll_wait()` returns. What fires, in what order?

→ [[../Domains/06 - Networking/Mental Models/04 - epoll — The Machine]] — kernel adds fd to ready list, epoll_wait() returns it
→ [[../Domains/04 - Linux/Mental Models/02 - File Descriptors — The Machine]] — what an fd is at the kernel level, the open file table
→ [[../Domains/07 - Design Patterns/Mental Models/01 - Reactor Pattern — The Machine]] — how the Reactor dispatches to the right handler
→ [[../Domains/07 - Design Patterns/Mental Models/05 - Command Pattern — The Machine]] — how the event becomes a Command object queued to a thread pool

---

## Moment 4 — A packet arrives (UDP)

Data hits the NIC. Where does it go before your `recvfrom()` returns?

→ [[../Domains/06 - Networking/Mental Models/01 - Networking Overview — The Machine]] — NIC DMA → kernel socket buffer → syscall return
→ [[../Domains/06 - Networking/Mental Models/03 - UDP Sockets — The Machine]] — no connection state, message boundaries, recvfrom semantics
→ [[../Domains/06 - Networking/Mental Models/02 - TCP Sockets — The Machine]] — TCP for comparison: ACK, retransmit, receive window

---

## Moment 5 — A thread is spawned

`pthread_create()` or `std::thread` fires. What does the kernel actually do?

→ [[../Domains/04 - Linux/Mental Models/04 - Threads and pthreads — The Machine]] — clone() syscall, new kernel stack, scheduler context
→ [[../Domains/05 - Concurrency/Mental Models/01 - Multithreading Patterns — The Machine]] — thread pool internals: WPQ, work stealing, idle/wake cycle
→ [[../Domains/04 - Linux/Mental Models/06 - Semaphores — The Machine]] — counting semaphore blocks/wakes threads
→ [[../Domains/05 - Concurrency/Mental Models/02 - Memory Ordering — The Machine]] — when a write on thread A is visible on thread B

---

## Moment 6 — A mutex is contested

Thread A holds the mutex. Thread B calls `lock()`. What happens to thread B?

→ [[../Domains/05 - Concurrency/Mental Models/01 - Multithreading Patterns — The Machine]] — futex: user-space fast path, kernel sleep on contention
→ [[../Domains/05 - Concurrency/Mental Models/02 - Memory Ordering — The Machine]] — acquire on lock, release on unlock: what memory is guaranteed visible

---

## Moment 7 — An object is destroyed (RAII)

A `unique_ptr<Foo>` goes out of scope. Stack unwinds during an exception. What runs?

→ [[../Domains/03 - C++/Mental Models/01 - RAII — The Machine]] — destructor call order, stack unwind sequence
→ [[../Domains/03 - C++/Mental Models/02 - Smart Pointers — The Machine]] — unique_ptr destructor deletes, shared_ptr decrements refcount
→ [[../Domains/03 - C++/Mental Models/22 - shared_ptr — The Machine]] — control block layout, atomic strong count, deleter call
→ [[../Domains/03 - C++/Mental Models/25 - weak_ptr — The Machine]] — weak count, lock() CAS, cycle breaking
→ [[../Domains/03 - C++/Mental Models/21 - Move Semantics — The Machine (deep)]] — moved-from object: valid but empty, destructor runs safely

---

## Moment 8 — An exception is thrown

`throw std::runtime_error("bad state")` inside a function that has local objects. What does the runtime do?

→ [[../Domains/03 - C++/Mental Models/20 - Exception Unwinding — The Machine]] — .eh_frame lookup, __cxa_throw allocates on heap, destructor per frame
→ [[../Domains/03 - C++/Mental Models/01 - RAII — The Machine]] — why RAII objects are safe: destructors always run during unwind
→ [[../Domains/03 - C++/Mental Models/23 - Copy Elision — The Machine]] — why `return std::move(local)` defeats the optimizer (and why it's wrong)

---

## Moment 9 — A virtual function is called

`base->virtualMethod()` where base is a derived type. What does the CPU actually execute?

→ [[../Domains/03 - C++/Mental Models/18 - VTables — The Machine]] — vptr at offset 0, vtable in .rodata, three-instruction dispatch
→ [[../Domains/03 - C++/Mental Models/19 - Object Layout — The Machine]] — struct padding, EBO, multiple inheritance pointer adjustment
→ [[../Domains/01 - Memory/Mental Models/08 - Cache Hierarchy — The Machine]] — vtable lives in .rodata, cache miss on first indirect call

---

## Moment 10 — A std::vector grows

`push_back()` hits capacity. A new buffer must be allocated and all elements moved. What's the cost?

→ [[../Domains/03 - C++/Mental Models/17 - std::vector — The Machine]] — 2x growth, move_if_noexcept, all iterators invalidated
→ [[../Domains/03 - C++/Mental Models/21 - Move Semantics — The Machine (deep)]] — noexcept move → O(1) steal; missing noexcept → O(n) copies
→ [[../Domains/01 - Memory/Mental Models/09 - Cache Hierarchy — The Machine (deep)]] — why sequential vector beats list 100x (prefetcher, cache line packing)
→ [[../Domains/03 - C++/Mental Models/24 - Allocators — The Machine]] — what happens inside malloc() during the reallocation

---

## Moment 11 — An atomic counter is incremented under contention

Two threads on different cores both call `counter.fetch_add(1)`. What happens on the bus?

→ [[../Domains/05 - Concurrency/Mental Models/04 - Atomics — The Machine]] — LOCK prefix, MESI exclusive ownership, ~5ns no contention → 300ns contended
→ [[../Domains/05 - Concurrency/Mental Models/03 - False Sharing — The Machine]] — even different atomics on the same cache line thrash
→ [[../Domains/05 - Concurrency/Mental Models/02 - Memory Ordering — The Machine]] — what acquire/release actually prevents the CPU from reordering

---

## Moment 12 — A thread is context-switched

The scheduler timer fires while thread A is executing. Thread B gets the CPU. What changes?

→ [[../Domains/04 - Linux/Mental Models/10 - Context Switch — The Machine]] — timer interrupt, save RIP/RSP/GPRs, pick_next_task, load new thread state
→ [[../Domains/04 - Linux/Mental Models/11 - Scheduler — The Machine]] — CFS vruntime ordering, TIF_NEED_RESCHED, nice weights
→ [[../Domains/01 - Memory/Mental Models/09 - Cache Hierarchy — The Machine (deep)]] — TLB flush only on CR3 change; L1/L2 cache is NOT flushed

---

## Full domain lists (browse all mental models)

→ **Build Process**: [[../Domains/00 - Build Process/Mental Models/01 - Build Process — The Machine]] · [[../Domains/00 - Build Process/Mental Models/02 - Preprocessor — The Machine]] · [[../Domains/00 - Build Process/Mental Models/03 - Compiler — The Machine]] · [[../Domains/00 - Build Process/Mental Models/04 - Assembler — The Machine]] · [[../Domains/00 - Build Process/Mental Models/05 - Linker — The Machine]] · [[../Domains/00 - Build Process/Mental Models/06 - Make and CMake — The Machine]]

→ **Memory**: [[../Domains/01 - Memory/Mental Models/01 - Process Memory Layout — The Machine]] · [[../Domains/01 - Memory/Mental Models/02 - Stack vs Heap — The Machine]] · [[../Domains/01 - Memory/Mental Models/03 - Virtual Memory — The Machine]] · [[../Domains/01 - Memory/Mental Models/04 - Paging — The Machine]] · [[../Domains/01 - Memory/Mental Models/05 - MMU — The Machine]] · [[../Domains/01 - Memory/Mental Models/06 - Page Walk — The Machine]] · [[../Domains/01 - Memory/Mental Models/07 - TLB — The Machine]] · [[../Domains/01 - Memory/Mental Models/08 - Cache Hierarchy — The Machine]]

→ **C**: [[../Domains/02 - C/Mental Models/01 - Pointers — The Machine]] · [[../Domains/02 - C/Mental Models/02 - File IO — The Machine]] · [[../Domains/02 - C/Mental Models/03 - Strings — The Machine]] · [[../Domains/02 - C/Mental Models/04 - Structs and Unions — The Machine]] · [[../Domains/02 - C/Mental Models/05 - Bitwise Operations — The Machine]] · [[../Domains/02 - C/Mental Models/06 - Serialization — The Machine]] · [[../Domains/02 - C/Mental Models/07 - Undefined Behavior — The Machine]] · [[../Domains/02 - C/Mental Models/08 - malloc and free — The Machine]]

→ **C++**: [[../Domains/03 - C++/Mental Models/01 - RAII — The Machine]] · [[../Domains/03 - C++/Mental Models/02 - Smart Pointers — The Machine]] · [[../Domains/03 - C++/Mental Models/03 - Move Semantics — The Machine]] · [[../Domains/03 - C++/Mental Models/04 - Templates — The Machine]] · [[../Domains/03 - C++/Mental Models/05 - Inheritance — The Machine]] · [[../Domains/03 - C++/Mental Models/06 - Virtual Functions — The Machine]] · [[../Domains/03 - C++/Mental Models/17 - std::vector — The Machine]] · [[../Domains/03 - C++/Mental Models/18 - VTables — The Machine]] · [[../Domains/03 - C++/Mental Models/19 - Object Layout — The Machine]] · [[../Domains/03 - C++/Mental Models/20 - Exception Unwinding — The Machine]] · [[../Domains/03 - C++/Mental Models/21 - Move Semantics — The Machine (deep)]] · [[../Domains/03 - C++/Mental Models/22 - shared_ptr — The Machine]] · [[../Domains/03 - C++/Mental Models/23 - Copy Elision — The Machine]] · [[../Domains/03 - C++/Mental Models/24 - Allocators — The Machine]] · [[../Domains/03 - C++/Mental Models/25 - weak_ptr — The Machine]]

→ **Linux**: [[../Domains/04 - Linux/Mental Models/01 - Processes — The Machine]] · [[../Domains/04 - Linux/Mental Models/02 - File Descriptors — The Machine]] · [[../Domains/04 - Linux/Mental Models/03 - Signals — The Machine]] · [[../Domains/04 - Linux/Mental Models/04 - Threads and pthreads — The Machine]] · [[../Domains/04 - Linux/Mental Models/05 - Shared Memory — The Machine]] · [[../Domains/04 - Linux/Mental Models/06 - Semaphores — The Machine]] · [[../Domains/04 - Linux/Mental Models/07 - Kernel — The Machine]] · [[../Domains/04 - Linux/Mental Models/08 - mmap — The Machine]] · [[../Domains/04 - Linux/Mental Models/09 - gdb Debugging — The Machine]] · [[../Domains/04 - Linux/Mental Models/10 - Context Switch — The Machine]] · [[../Domains/04 - Linux/Mental Models/11 - Scheduler — The Machine]]

→ **Memory**: [[../Domains/01 - Memory/Mental Models/01 - Process Memory Layout — The Machine]] · [[../Domains/01 - Memory/Mental Models/02 - Stack vs Heap — The Machine]] · [[../Domains/01 - Memory/Mental Models/03 - Virtual Memory — The Machine]] · [[../Domains/01 - Memory/Mental Models/04 - Paging — The Machine]] · [[../Domains/01 - Memory/Mental Models/05 - MMU — The Machine]] · [[../Domains/01 - Memory/Mental Models/06 - Page Walk — The Machine]] · [[../Domains/01 - Memory/Mental Models/07 - TLB — The Machine]] · [[../Domains/01 - Memory/Mental Models/08 - Cache Hierarchy — The Machine]] · [[../Domains/01 - Memory/Mental Models/09 - Cache Hierarchy — The Machine (deep)]] · [[../Domains/01 - Memory/Mental Models/10 - Allocators and Memory Pools — The Machine]]

→ **Networking**: [[../Domains/06 - Networking/Mental Models/01 - Networking Overview — The Machine]] · [[../Domains/06 - Networking/Mental Models/02 - TCP Sockets — The Machine]] · [[../Domains/06 - Networking/Mental Models/03 - UDP Sockets — The Machine]] · [[../Domains/06 - Networking/Mental Models/04 - epoll — The Machine]] · [[../Domains/06 - Networking/Mental Models/05 - IPC Overview — The Machine]]

→ **Design Patterns**: [[../Domains/07 - Design Patterns/Mental Models/01 - Reactor Pattern — The Machine]] · [[../Domains/07 - Design Patterns/Mental Models/02 - Observer Pattern — The Machine]] · [[../Domains/07 - Design Patterns/Mental Models/03 - Singleton Pattern — The Machine]] · [[../Domains/07 - Design Patterns/Mental Models/04 - Factory Pattern — The Machine]] · [[../Domains/07 - Design Patterns/Mental Models/05 - Command Pattern — The Machine]] · [[../Domains/07 - Design Patterns/Mental Models/06 - Strategy Pattern — The Machine]]

→ **Concurrency**: [[../Domains/05 - Concurrency/Mental Models/01 - Multithreading Patterns — The Machine]] · [[../Domains/05 - Concurrency/Mental Models/02 - Memory Ordering — The Machine]] · [[../Domains/05 - Concurrency/Mental Models/03 - False Sharing — The Machine]] · [[../Domains/05 - Concurrency/Mental Models/04 - Atomics — The Machine]]

→ **Algorithms**: [[../Domains/08 - Algorithms/Mental Models/01 - Data Structures — The Machine]] · [[../Domains/08 - Algorithms/Mental Models/02 - Big-O and Complexity — The Machine]]

---

## LDS runtime machines → LDS vault

See how these patterns execute inside a real C++ system:
→ LDS/Runtime Machines/LDS System — The Machine
→ LDS/Runtime Machines/Reactor — The Machine
→ LDS/Runtime Machines/Request Lifecycle — The Machine
