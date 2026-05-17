# Learn Systems Engineering

The journey from source file to live system. Each layer answers: **why does the next layer need the previous one?**

Follow top to bottom. When you finish each layer, you should be able to explain what the machine is doing — not just what the API does.

---

## Level 0 — The Whole System (start here)

Before any layer: see the full picture. Every layer below is one node in this graph.

```
 ┌─────────────────────── SOURCE ────────────────────────┐
 │  source.cpp  #include  headers  .h files               │
 └───────────────────────────┬───────────────────────────┘
                    Layer 1 (Build Pipeline)
               preprocessor → compiler → assembler → linker
                             ↓
                       [ELF binary on disk]
                             │  exec()
                             ↓
 ┌────────────────── PROCESS (virtual address space) ─────────────────┐
 │                                                                     │
 │  .text │ .data │ .bss │ ←── heap ───→ │ ... │ ←── stack ────      │
 │  ─────────────────── Layer 2 (Memory) ──────────────────────────   │
 │                                                                     │
 │  open() read() write() malloc() free()                             │
 │  pointers · strings · structs · bitwise · serialize                │
 │  ─────────────────── Layer 3 (C) ───────────────────────────────   │
 │                                                                     │
 │  RAII · unique_ptr · move semantics · vtable · templates · throw   │
 │  ─────────────────── Layer 4 (C++) ─────────────────────────────   │
 │                                                                     │
 │  fork() · exec() · signals · pthreads · mmap · context switch      │
 │  ─────────────────── Layer 5 (Linux) ───────────────────────────   │
 │                                                                     │
 │  Thread 1 (Reactor/main)  │  Thread 2 (worker)  │  Thread 3 …     │
 │  ─────────────────── Layer 8 (Concurrency) ─────────────────────   │
 │                                                                     │
 │  Reactor → Observer → Command → Factory → Strategy → ThreadPool    │
 │  ─────────────────── Layer 7 (Design Patterns) ─────────────────   │
 └────────────────────────────┬────────────────────────────────────────┘
                    Layer 6 (Networking)
            socket() · epoll_wait() · send() · recv()
                             │
             ┌───────────────┴───────────────┐
           TCP                             UDP
      (reliable stream)           (unreliable datagrams)
                             │
                       [NIC → wire]
```

**Reading this**: the build pipeline produces a binary. `exec()` loads it into a virtual address space. Memory (Layer 2) is the substrate everything runs on. C (Layer 3) is how the OS speaks. C++ (Layer 4) manages object lifetimes on top. Linux (Layer 5) is the interface to the kernel. Design Patterns (Layer 7) structure the event loop. Concurrency (Layer 8) parallelises it. Networking (Layer 6) connects it to the world. Layer 9 shows how the CPU/kernel executes all of the above.

→ **Full runtime map:** [[Linux Runtime — The Machine]] — all 6 kernel subsystems and how they interact
→ **Execution stories:** [[02 - Build Runtime Intuition]] — what the machine does at each moment

---

## Level 1 — Layer Map (one row per layer)

| Layer | Domain | What it produces |
|---|---|---|
| 1 | Build Pipeline | ELF binary on disk |
| 2 | Memory | Address space: text / heap / stack |
| 3 | C | I/O, data encoding, bit-level access |
| 4 | C++ | Automatic resource lifetimes, polymorphism |
| 5 | Linux | Process model, file descriptors, threads |
| 6 | Networking | Byte streams between machines |
| 7 | Design Patterns | Scalable event-driven structure |
| 8 | Concurrency | Parallel correctness |
| 9 | The Machine | Execution story for each layer above |

---

## Level 2 — Each Layer Expanded

### Layer 1 — How a binary comes to exist
Before a process can run, its binary must exist. The pipeline transforms `.cpp` text into an ELF file the kernel can `exec()`. Each stage has a concrete output you can inspect (`g++ -E`, `g++ -S`, `objdump -d`, `readelf -s`).

```
source.cpp
  → [preprocessor]  #include expanded, macros substituted → translation unit
  → [compiler]      C++ AST → optimized IR → assembly (.s)
  → [assembler]     assembly → .o (ELF with blank relocation slots)
  → [linker]        resolve symbols across .o files → fill slots → ELF executable
                    dynamic linker entry written into PT_INTERP
```

→ [[01 - Preprocessor]] — text expansion: #include, #define, #ifdef
→ [[02 - Compiler]] — parses C++, emits assembly with blank symbol slots
→ [[03 - Assembler]] — assembly → .o files (ELF with relocation entries)
→ [[04 - Linker]] — resolves blank slots, merges .o files into one executable
→ [[05 - Make and CMake]] — automates the full pipeline

Machine: [[Program Startup — The Machine]] — exec() → ELF loader → dynamic linker → constructors → main()

Runtime payoff: `undefined reference to X` = the .o that defines X wasn't passed to the linker. `undefined symbol` at runtime = the shared library wasn't found by the dynamic linker.

---

### Layer 2 — Where data lives at runtime
The binary exists. Now it runs. The kernel `exec()`'d it: mapped `.text` into a read-execute region, `.data` into read-write, zeroed `.bss`, and set up an initial stack. The heap doesn't exist yet — it grows on demand when `malloc()` calls `brk()` or `mmap()`.

```
virtual address space (low → high):
  [.text]  [.data/.bss]  [heap →]  ...  [← stack]
             ↑                              ↑
         loaded by exec()            grows downward
```

→ [[01 - Process Memory Layout]] — text, data, BSS, heap, stack: what lands where in virtual memory
→ [[02 - Stack vs Heap]] — why stack is fast (RSP adjust = 0 cost), why heap requires allocator bookkeeping
→ [[02 - Memory - malloc and free]] — free list → brk/mmap → page fault on first touch
→ [[01 - Pointers]] — pointer arithmetic, double pointers, function pointers, void*
→ [[04 - Structs and Unions]] — struct layout, padding, alignment rules
→ [[09 - Memory Errors and Tools]] — leaks, use-after-free, double-free, ASan, Valgrind

Machine: [[Memory System — The Machine]] — `malloc()` → brk/mmap → page fault → TLB miss → cache miss cascade

Runtime payoff: given a segfault address, you can say which region was accessed (stack overflow? null deref? freed heap?) and why.

---

### Layer 3 — C: the operating interface
C is the language the OS speaks. Every syscall parameter is a C type. Every file, socket, and pipe is accessed via a file descriptor — an `int` that the kernel resolves through the fd table. This layer covers the primitives used for I/O, data encoding, and low-level bit manipulation.

```
open("data", O_RDONLY)
  → kernel: create fd table entry → return fd (int)
read(fd, buf, n)
  → kernel: copy from file/socket buffer → user buf
  → errno on error (not an exception — check the return value)
```

→ [[05 - File IO]] — POSIX open/read/write/lseek, flags, errno
→ [[03 - Strings]] — null terminator, safe copy, sprintf pitfalls
→ [[06 - Bitwise Operations]] — AND/OR/XOR/NOT, masking, bit fields, byte reversal
→ [[07 - Serialization]] — manual binary encoding, byte order (htons/ntohl), framing
→ [[08 - Undefined Behavior]] — what UB is, why the compiler can exploit it, sanitizers

Machine: [[02 - File IO — The Machine]] — fd lifecycle: open → kernel file table → read syscall path

---

### Layer 4 — C++ resource management
C++ adds automatic resource lifetime management on top of C's manual model. No garbage collector: the destructor runs when the object leaves scope — even during exception unwinding. This determinism is what makes RAII safe.

```
{
    auto p = std::make_unique<Foo>();   // heap alloc, vptr written
    risky_call();                        // may throw
}  // ← p.~unique_ptr() fires here regardless
   //   calls delete → Foo::~Foo() → memory freed
   //   even if risky_call() threw
```

Virtual calls: `base->method()` → load `vptr` from object → index vtable → indirect call. Three instructions. The cost is the cache miss on the vtable when cold.

→ [[01 - RAII]] — destructor timing, stack unwinding, why resources can't leak
→ [[02 - Smart Pointers]] — unique_ptr (sole ownership), shared_ptr (refcount+control block), weak_ptr (no ownership)
→ [[03 - Move Semantics]] — lvalue/rvalue reference, move constructor, Rule of Five
→ [[06 - Virtual Functions]] — vtable layout, override, pure virtual, slicing danger
→ [[04 - Templates]] — function/class templates, specialization, SFINAE
→ [[09 - Exception Handling]] — throw/catch, exception safety levels, noexcept

Machine: [[C++ Object Lifetime — The Machine]] — ctor sets vptr → use → move → exception unwind → dtor

Runtime payoff: explain what happens in memory when `unique_ptr<Foo> p = std::move(q)` executes, why noexcept matters on move constructors, and what the CPU executes for `base->virtualMethod()`.

---

### Layer 5 — Linux: the OS interface
A process doesn't run in isolation. It interacts with the kernel constantly via syscalls. The kernel is the boundary between user code and hardware — every `open()`, `read()`, `clone()`, and `mmap()` crosses it. This layer is the syscall interface that matters for systems programming.

```
Every ~1ms: hardware timer fires
  → CPU interrupt → kernel interrupt handler
  → update current thread vruntime
  → if another thread has lower vruntime: set TIF_NEED_RESCHED
  → on syscall return: if TIF_NEED_RESCHED → schedule() → context switch
```

Threads are processes that share the same virtual address space (`clone()` with `CLONE_VM`). Each has its own stack, registers, and errno. They share heap, globals, and fd table.

→ [[01 - Processes]] — fork(), exec(), wait(), zombie, daemon process
→ [[02 - File Descriptors]] — everything is an fd: files, sockets, pipes, timers, inotify
→ [[03 - Signals]] — sigaction, async-signal-safety, signalfd, SIGPIPE
→ [[04 - Threads - pthreads]] — pthread_create, mutex, condition variable, TLS
→ [[05 - Shared Memory]] — shm_open, mmap MAP_SHARED, synchronization
→ [[06 - Semaphores]] — counting semaphore, sem_wait/post, producer/consumer
→ [[07 - mmap]] — file-backed vs anonymous mapping, MAP_PRIVATE vs MAP_SHARED
→ [[09 - Context Switch]] — timer interrupt, register save/restore, pick_next_task
→ [[10 - Scheduler]] — CFS vruntime, nice weights, TIF_NEED_RESCHED

Machine: [[Linux Runtime — The Machine]] — the map: scheduler + MMU + threads + fds + networking in one view

Runtime payoff: explain the process model, why SIGPIPE kills a writer, and what happens at every timer interrupt.

---

### Layer 6 — Networking: talking to the world
Processes communicate over sockets. A socket is a file descriptor. `epoll` watches many fds simultaneously in O(1). When data arrives, the NIC DMAs it into the kernel socket buffer, the kernel adds the fd to the epoll ready list, and `epoll_wait()` wakes your thread — all without polling.

```
NIC DMA → kernel rx ring → softirq → TCP/IP layer
  → socket receive buffer (sk_buff)
  → epoll ready list: add socket fd
  → epoll_wait() returns → your Reactor fires handler
  → recv() copies data from kernel buffer → user buffer
```

→ [[01 - Overview]] — physical → Ethernet → IP → TCP/UDP → application
→ [[02 - Sockets TCP]] — socket(), connect(), RecvAll loop, wire protocol design
→ [[03 - UDP Sockets]] — sendto/recvfrom, message boundaries, MTU, broadcast
→ [[04 - epoll]] — select vs poll vs epoll, level vs edge-triggered, EPOLLET
→ [[05 - IPC Overview]] — pipes, socketpair, unix domain sockets, shared memory

Machine: [[Networking Stack — The Machine]] — NIC DMA → softirq → socket → epoll → Reactor → thread pool

Runtime payoff: walk through everything that happens in kernel space when `epoll_wait()` returns, from NIC interrupt to user recv().

---

### Layer 7 — Design Patterns: structure that scales
Individual components need to be composed. These patterns are the recurring structures that make concurrent, event-driven systems maintainable. The key insight: the Reactor, Command, and Observer patterns chain together to handle one network event end-to-end.

```
epoll_wait() returns fd              ← Reactor: event demux
  → handler dispatch table lookup   ← Reactor: O(1) dispatch
  → handler.onReadable()
  → recv() data
  → notify(observers)               ← Observer: decouple handler from business logic
  → Command{data} pushed to WPQ     ← Command: encapsulate as object, enables queuing
  → worker thread pops + executes   ← ThreadPool: decouple I/O thread from CPU work
```

→ [[01 - Reactor]] — epoll event loop + handler dispatch table
→ [[02 - Observer]] — publisher/subscriber, thread-safe notify()
→ [[05 - Command]] — encapsulate request as object, enables work queues and undo
→ [[04 - Factory]] — create objects by interface, decouples construction from use
→ [[03 - Singleton]] — one global instance, thread-safe construction
→ [[06 - Strategy]] — swap algorithms at runtime via interface

Machine: [[01 - Reactor Pattern — The Machine]] · [[05 - Command Pattern — The Machine]]

Runtime payoff: trace a network event from `epoll_wait()` return through Reactor dispatch → Observer notify → Command queue → worker execution.

---

### Layer 8 — Concurrency: sharing correctly
Multiple threads operate on shared state. The CPU has its own write buffer — a write on thread A is NOT immediately visible to thread B unless you use synchronization primitives that include memory fences. Mutexes protect not just atomicity but visibility.

```
Thread A: mutex.unlock()
  → release fence: all prior writes flushed → globally visible
Thread B: mutex.lock()
  → acquire fence: all subsequent reads see Thread A's writes

Without this:
  Thread A writes x = 1
  Thread B reads x → may still see 0 (stale in B's store buffer)
```

False sharing: two threads on different cores incrementing different variables that happen to share a 64-byte cache line → MESI protocol forces cache line ownership transfer on every increment → 100x slower than expected.

→ [[01 - Multithreading Patterns]] — thread pool, producer/consumer WPQ, futures
→ [[02 - Memory Ordering]] — happens-before, acquire/release, CAS, memory barriers

Machine: [[Concurrency Runtime — The Machine]] — thread pool WPQ → futex fast path → mutex contention → wakeup

Runtime payoff: explain why `memory_order_relaxed` is NOT safe for inter-thread sync, and why adjacent counters can be 100x slower than separate ones.

---

### Layer 9 — The Machine (what the CPU and kernel actually do)
Theory tells you what. The machine tells you how. For each layer above, read the corresponding machine notes to see the execution story — what runs, what blocks, what wakes, where time is spent.

**Build process**
→ [[01 - Build Process — The Machine]] — full pipeline: text → tokens → AST → assembly → ELF → linked binary
→ [[02 - Preprocessor — The Machine]] — macro expansion pass, include graph, conditional branches
→ [[05 - Linker — The Machine]] — symbol table merge, relocation patching, dynamic linker at startup

**Memory**
→ [[01 - Process Memory Layout — The Machine]] — how text/data/BSS/heap/stack land in virtual memory
→ [[02 - Stack vs Heap — The Machine]] — why stack allocation costs zero, why heap requires bookkeeping
→ [[03 - Virtual Memory — The Machine]] — page isn't real until you touch it (demand paging)
→ [[08 - malloc and free — The Machine]] — allocator finds free block, calls brk() when heap is exhausted
→ [[01 - Pointers — The Machine]] — pointer arithmetic at the address level

**C**
→ [[02 - File IO — The Machine]] — POSIX fd lifecycle: open → kernel file table → read/write syscall

**C++**
→ [[01 - RAII — The Machine]] — destructor call order, stack unwind sequence
→ [[02 - Smart Pointers — The Machine]] — unique_ptr destructor deletes; shared_ptr decrements refcount
→ [[21 - Move Semantics — The Machine (deep)]] — moved-from state, noexcept fast path vs copy fallback
→ [[18 - VTables — The Machine]] — vptr at offset 0, vtable in .rodata, three-instruction dispatch
→ [[20 - Exception Unwinding — The Machine]] — .eh_frame lookup, __cxa_throw, destructor per frame

**Linux**
→ [[01 - Processes — The Machine]] — fork/exec lifecycle, address space setup, COW pages
→ [[02 - File Descriptors — The Machine]] — kernel fd table, open file table, inode
→ [[03 - Signals — The Machine]] — signal delivery, pending mask, async-signal-safety constraint
→ [[04 - Threads and pthreads — The Machine]] — clone() syscall, new kernel stack, scheduler context
→ [[10 - Context Switch — The Machine]] — timer interrupt, save RIP/RSP/GPRs, pick_next_task
→ [[11 - Scheduler — The Machine]] — CFS vruntime ordering, TIF_NEED_RESCHED, nice weights

**Networking**
→ [[04 - epoll — The Machine]] — kernel adds fd to ready list, epoll_wait() returns it
→ [[02 - TCP Sockets — The Machine]] — connect/accept, send buffer, ACK, retransmit
→ [[03 - UDP Sockets — The Machine]] — no connection state, message boundaries, recvfrom semantics

**Design patterns**
→ [[01 - Reactor Pattern — The Machine]] — epoll loop + handler dispatch table
→ [[05 - Command Pattern — The Machine]] — event becomes a Command object queued to thread pool

**Concurrency**
→ [[01 - Multithreading Patterns — The Machine]] — thread pool internals: WPQ, work stealing, idle/wake
→ [[02 - Memory Ordering — The Machine]] — when a write on thread A is visible on thread B
→ [[04 - Atomics — The Machine]] — LOCK prefix, MESI exclusive ownership, ~5ns vs 300ns contended
→ [[03 - False Sharing — The Machine]] — two atomics on the same cache line thrash the bus

**High-level runtime machines (whole-system views)**
→ [[Linux Runtime — The Machine]] · [[Memory System — The Machine]] · [[Networking Stack — The Machine]] · [[Concurrency Runtime — The Machine]] · [[C++ Object Lifetime — The Machine]]
