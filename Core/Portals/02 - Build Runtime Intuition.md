# Build Runtime Intuition

These notes answer: **"what is the machine doing right now?"**

Organized by runtime moment — pick the moment you want to understand. Each Mental Model is an execution story: what runs, what blocks, what wakes, where time is spent.

---

## Level 0 — The Full Runtime System

Every moment below is a path through this map. Learn the map first.

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER SPACE                              │
│                                                                 │
│  Thread 1 (Reactor)    Thread 2 (worker)    Thread 3 (worker)  │
│  ┌──────────────┐      ┌──────────────┐     ┌──────────────┐   │
│  │ stack        │      │ stack        │      │ stack        │   │
│  │ registers    │      │ registers    │      │ registers    │   │
│  │ TLS/errno    │      │ TLS/errno    │      │ TLS/errno    │   │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘  │
│         └──────────────────────┴───────────────────┘            │
│                    shared heap  shared .text  shared globals    │
└────────────────────────────┬────────────────────────────────────┘
                              │  syscall / interrupt
┌────────────────────────────▼────────────────────────────────────┐
│                       KERNEL SPACE                              │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  Scheduler  │  │  MM subsys   │  │  VFS / Net stack       │ │
│  │  CFS rbtree │  │  page tables │  │  socket buffers        │ │
│  │  vruntime   │  │  VMAs / mmap │  │  fd table              │ │
│  │  runqueues  │  │  page cache  │  │  epoll instances       │ │
│  └─────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌────────────────────────────▼────────────────────────────────────┐
│                        HARDWARE                                 │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌─────────────┐  │
│  │  CPU     │  │  MMU + TLB │  │  DRAM    │  │  NIC / SSD  │  │
│  │  cores   │  │  CR3 reg   │  │  pages   │  │  DMA engine │  │
│  └──────────┘  └────────────┘  └──────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Six subsystems** operate simultaneously. Every moment below is a path through them.

| Subsystem | What it does |
|---|---|
| **Scheduler** | Decides which thread runs on which CPU core |
| **MM** | Manages virtual→physical mapping, demand paging, CoW |
| **VFS/Net** | Handles fd operations, socket buffers, epoll ready list |
| **CPU** | Executes instructions, raises exceptions on faults/interrupts |
| **MMU+TLB** | Translates virtual addresses; caches mappings in TLB |
| **NIC/SSD** | DMA data into/out of kernel ring buffers without CPU |

---

## Level 1 — Moment Map (which subsystems each moment activates)

| Moment | Subsystems | Description |
|---|---|---|
| 1 — Process starts | Scheduler, MM, VFS | exec() → ELF load → dynamic linker → main() |
| 2 — malloc() | MM, MMU+TLB, CPU | free list → brk/mmap → page fault → cache miss |
| 3 — I/O event arrives | VFS/Net, Scheduler, MM | NIC → epoll ready → Reactor wakes → recv() |
| 4 — UDP packet | NIC, VFS/Net, Scheduler | DMA → softirq → socket buffer → recvfrom() |
| 5 — Thread spawned | Scheduler, MM | clone() → new task_struct → runqueue |
| 6 — Mutex contested | Scheduler, CPU | futex fast path → FUTEX_WAIT → sleep → wake |
| 7 — Object destroyed | CPU, MM | destructor call order, stack unwind, delete |
| 8 — Exception thrown | CPU, MM | .eh_frame lookup → __cxa_throw → unwind → catch |
| 9 — Virtual call | CPU, MMU+TLB | vptr load → vtable index → indirect call |
| 10 — vector grows | MM, MMU+TLB, CPU | 2x realloc → move elements → cache-warm layout |
| 11 — Atomic contended | CPU, MMU+TLB | LOCK prefix → MESI exclusive → ~300ns contended |
| 12 — Context switch | Scheduler, CPU, MMU+TLB | timer IRQ → save registers → pick_next → load |

---

## Level 2 — Each Moment Expanded

### Moment 1 — A process starts

The kernel runs `exec()`. Before your first line of code runs, a lot happens.

→ [[01 - Processes — The Machine]] — fork/exec lifecycle, address space setup
→ [[01 - Process Memory Layout — The Machine]] — how text/data/BSS/heap/stack land in virtual memory
→ [[05 - Linker — The Machine]] — why the dynamic linker runs first to resolve shared library symbols
→ [[01 - RAII — The Machine]] — global constructors run before main()

---

### Moment 2 — Code allocates memory

`new Foo()` or `malloc(256)` is called. What actually happens?

→ [[08 - malloc and free — The Machine]] — allocator finds a free block, calls brk() if heap is exhausted
→ [[02 - Stack vs Heap — The Machine]] — why stack allocation costs nothing but heap requires bookkeeping
→ [[03 - Virtual Memory — The Machine]] — the page isn't real until you touch it (demand paging)
→ [[04 - Paging — The Machine]] — page fault → kernel allocates physical page → resumes
→ [[07 - TLB — The Machine]] — the TLB miss cost when touching a new page
→ [[08 - Cache Hierarchy — The Machine]] — L1/L2/L3 miss cascade on first access

---

### Moment 3 — An I/O event arrives

A socket becomes readable. `epoll_wait()` returns. What fires, in what order?

→ [[04 - epoll — The Machine]] — kernel adds fd to ready list, epoll_wait() returns it
→ [[02 - File Descriptors — The Machine]] — what an fd is at the kernel level, the open file table
→ [[01 - Reactor Pattern — The Machine]] — how the Reactor dispatches to the right handler
→ [[05 - Command Pattern — The Machine]] — how the event becomes a Command object queued to a thread pool

---

### Moment 4 — A packet arrives (UDP)

Data hits the NIC. Where does it go before your `recvfrom()` returns?

→ [[01 - Networking Overview — The Machine]] — NIC DMA → kernel socket buffer → syscall return
→ [[03 - UDP Sockets — The Machine]] — no connection state, message boundaries, recvfrom semantics
→ [[02 - TCP Sockets — The Machine]] — TCP for comparison: ACK, retransmit, receive window

---

### Moment 5 — A thread is spawned

`pthread_create()` or `std::thread` fires. What does the kernel actually do?

→ [[04 - Threads and pthreads — The Machine]] — clone() syscall, new kernel stack, scheduler context
→ [[01 - Multithreading Patterns — The Machine]] — thread pool internals: WPQ, work stealing, idle/wake cycle
→ [[06 - Semaphores — The Machine]] — counting semaphore blocks/wakes threads
→ [[02 - Memory Ordering — The Machine]] — when a write on thread A is visible on thread B

---

### Moment 6 — A mutex is contested

Thread A holds the mutex. Thread B calls `lock()`. What happens to thread B?

→ [[01 - Multithreading Patterns — The Machine]] — futex: user-space fast path, kernel sleep on contention
→ [[02 - Memory Ordering — The Machine]] — acquire on lock, release on unlock: what memory is guaranteed visible

---

### Moment 7 — An object is destroyed (RAII)

A `unique_ptr<Foo>` goes out of scope. Stack unwinds during an exception. What runs?

→ [[01 - RAII — The Machine]] — destructor call order, stack unwind sequence
→ [[02 - Smart Pointers — The Machine]] — unique_ptr destructor deletes, shared_ptr decrements refcount
→ [[22 - shared_ptr — The Machine]] — control block layout, atomic strong count, deleter call
→ [[25 - weak_ptr — The Machine]] — weak count, lock() CAS, cycle breaking
→ [[21 - Move Semantics — The Machine (deep)]] — moved-from object: valid but empty, destructor runs safely

---

### Moment 8 — An exception is thrown

`throw std::runtime_error("bad state")` inside a function that has local objects. What does the runtime do?

→ [[20 - Exception Unwinding — The Machine]] — .eh_frame lookup, __cxa_throw allocates on heap, destructor per frame
→ [[01 - RAII — The Machine]] — why RAII objects are safe: destructors always run during unwind
→ [[23 - Copy Elision — The Machine]] — why `return std::move(local)` defeats the optimizer (and why it's wrong)

---

### Moment 9 — A virtual function is called

`base->virtualMethod()` where base is a derived type. What does the CPU actually execute?

→ [[18 - VTables — The Machine]] — vptr at offset 0, vtable in .rodata, three-instruction dispatch
→ [[19 - Object Layout — The Machine]] — struct padding, EBO, multiple inheritance pointer adjustment
→ [[08 - Cache Hierarchy — The Machine]] — vtable lives in .rodata, cache miss on first indirect call

---

### Moment 10 — A std::vector grows

`push_back()` hits capacity. A new buffer must be allocated and all elements moved. What's the cost?

→ [[17 - std::vector — The Machine]] — 2x growth, move_if_noexcept, all iterators invalidated
→ [[21 - Move Semantics — The Machine (deep)]] — noexcept move → O(1) steal; missing noexcept → O(n) copies
→ [[09 - Cache Hierarchy — The Machine (deep)]] — why sequential vector beats list 100x (prefetcher, cache line packing)
→ [[24 - Allocators — The Machine]] — what happens inside malloc() during the reallocation

---

### Moment 11 — An atomic counter is incremented under contention

Two threads on different cores both call `counter.fetch_add(1)`. What happens on the bus?

→ [[04 - Atomics — The Machine]] — LOCK prefix, MESI exclusive ownership, ~5ns no contention → 300ns contended
→ [[03 - False Sharing — The Machine]] — even different atomics on the same cache line thrash
→ [[02 - Memory Ordering — The Machine]] — what acquire/release actually prevents the CPU from reordering

---

### Moment 12 — A thread is context-switched

The scheduler timer fires while thread A is executing. Thread B gets the CPU. What changes?

→ [[10 - Context Switch — The Machine]] — timer interrupt, save RIP/RSP/GPRs, pick_next_task, load new thread state
→ [[11 - Scheduler — The Machine]] — CFS vruntime ordering, TIF_NEED_RESCHED, nice weights
→ [[09 - Cache Hierarchy — The Machine (deep)]] — TLB flush only on CR3 change; L1/L2 cache is NOT flushed

---

## Level 3 — Full domain lists (browse all mental models)

→ **Build Process**: [[01 - Build Process — The Machine]] · [[02 - Preprocessor — The Machine]] · [[03 - Compiler — The Machine]] · [[04 - Assembler — The Machine]] · [[05 - Linker — The Machine]] · [[06 - Make and CMake — The Machine]]

→ **C**: [[01 - Pointers — The Machine]] · [[02 - File IO — The Machine]] · [[03 - Strings — The Machine]] · [[04 - Structs and Unions — The Machine]] · [[05 - Bitwise Operations — The Machine]] · [[06 - Serialization — The Machine]] · [[07 - Undefined Behavior — The Machine]] · [[08 - malloc and free — The Machine]]

→ **C++**: [[01 - RAII — The Machine]] · [[02 - Smart Pointers — The Machine]] · [[03 - Move Semantics — The Machine]] · [[04 - Templates — The Machine]] · [[05 - Inheritance — The Machine]] · [[06 - Virtual Functions — The Machine]] · [[07 - Operator Overloading — The Machine]] · [[08 - STL Containers — The Machine]] · [[09 - Exception Handling — The Machine]] · [[10 - Type Casting — The Machine]] · [[11 - Effective C++ Meyers — The Machine]] · [[12 - C++11 — The Machine]] · [[13 - C++14 — The Machine]] · [[14 - C++17 — The Machine]] · [[15 - C++20 — The Machine]] · [[16 - C++ Version Comparison — The Machine]] · [[17 - std::vector — The Machine]] · [[18 - VTables — The Machine]] · [[19 - Object Layout — The Machine]] · [[20 - Exception Unwinding — The Machine]] · [[21 - Move Semantics — The Machine (deep)]] · [[22 - shared_ptr — The Machine]] · [[23 - Copy Elision — The Machine]] · [[24 - Allocators — The Machine]] · [[25 - weak_ptr — The Machine]]

→ **Linux**: [[01 - Processes — The Machine]] · [[02 - File Descriptors — The Machine]] · [[03 - Signals — The Machine]] · [[04 - Threads and pthreads — The Machine]] · [[05 - Shared Memory — The Machine]] · [[06 - Semaphores — The Machine]] · [[07 - Kernel — The Machine]] · [[08 - mmap — The Machine]] · [[09 - gdb Debugging — The Machine]] · [[10 - Context Switch — The Machine]] · [[11 - Scheduler — The Machine]]

→ **Memory**: [[01 - Process Memory Layout — The Machine]] · [[02 - Stack vs Heap — The Machine]] · [[03 - Virtual Memory — The Machine]] · [[04 - Paging — The Machine]] · [[05 - MMU — The Machine]] · [[06 - Page Walk — The Machine]] · [[07 - TLB — The Machine]] · [[08 - Cache Hierarchy — The Machine]] · [[09 - Cache Hierarchy — The Machine (deep)]] · [[10 - Allocators and Memory Pools — The Machine]]

→ **Runtime Machines**: [[Linux Runtime — The Machine]] · [[Fork and Exec — The Machine]] · [[Program Startup — The Machine]] · [[Page Fault — The Machine]] · [[Memory System — The Machine]] · [[Networking Stack — The Machine]] · [[Concurrency Runtime — The Machine]] · [[Virtual Dispatch — The Machine]] · [[C++ Object Lifetime — The Machine]]

→ **Networking**: [[01 - Networking Overview — The Machine]] · [[02 - TCP Sockets — The Machine]] · [[03 - UDP Sockets — The Machine]] · [[04 - epoll — The Machine]] · [[05 - IPC Overview — The Machine]]

→ **Design Patterns**: [[01 - Reactor Pattern — The Machine]] · [[02 - Observer Pattern — The Machine]] · [[03 - Singleton Pattern — The Machine]] · [[04 - Factory Pattern — The Machine]] · [[05 - Command Pattern — The Machine]] · [[06 - Strategy Pattern — The Machine]]

→ **Concurrency**: [[01 - Multithreading Patterns — The Machine]] · [[02 - Memory Ordering — The Machine]] · [[03 - False Sharing — The Machine]] · [[04 - Atomics — The Machine]]

→ **Algorithms**: [[01 - Data Structures — The Machine]] · [[02 - Big-O and Complexity — The Machine]]

---

## LDS runtime machines → LDS vault

See how these patterns execute inside a real C++ system:
→ [[01 - LDS System — The Machine]]
→ [[03 - Reactor — The Machine]]
→ [[02 - Request Lifecycle — The Machine]]
