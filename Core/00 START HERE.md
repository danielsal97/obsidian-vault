# Core — Systems Engineering

→ [[00 - VAULT MAP]] — top-level vault entry point

---

## Level 0 — The Full Stack

Read this once. Everything in the vault is one row of this diagram.

```
Layer 7 — Build Pipeline
  source.cpp → preprocessor → compiler → assembler → linker → ELF binary
                                                                    │
                                                               exec() syscall
                                                                    │
Layer 2 — Linux (OS interface)                                      ▼
  fork() · exec() · signals · mmap            ┌─── Process (virtual address space) ───┐
  context switch · scheduler ────────────────▶│ .text │ .data │ .bss │ heap │  stack  │
                                              └──────────────────────┬────────────────┘
Layer 1 — Memory                                                     │
  virtual memory · page tables · MMU · TLB                           │ allocation
  heap allocator · page fault · cache ───────────────────────────────┘

Layer 3 — Languages (running inside the process)
  C:   open() · read() · write() · malloc() · pointers · structs · serialize
  C++: RAII · unique_ptr · move semantics · vtable · templates · exceptions

Layer 4 — Concurrency
  Thread 1 (Reactor)  │  Thread 2 (worker)  │  Thread 3 (worker)
  ─── shared heap ────┴──── shared .text ───┴──── shared globals ───
  mutex · futex · memory ordering · atomics · false sharing

Layer 6 — Design Patterns
  Reactor ──epoll──▶ handler dispatch ──Command──▶ ThreadPool
  Observer · Factory · Singleton · Strategy

Layer 5 — Networking
  epoll_wait() → socket fd → recv() / send()
  TCP (reliable stream)  │  UDP (unreliable datagram)
  NIC DMA → softirq → socket buffer → epoll ready list → handler

Layer 0 — Hardware
  CPU cores │ MMU+TLB │ L1/L2/L3 cache │ DRAM │ NIC │ SSD
```

The path: **source file → linker → ELF → exec() → address space → C/C++ objects → threads → epoll → NIC**.

---

## Level 1 — Runtime Machines (start here for traversal learning)

Each machine shows a live execution path. Read these before diving into domain notes.

| Machine | Runtime Path It Shows |
|---|---|
| [[Linux Runtime — The Machine]] | All 6 kernel subsystems simultaneously — the master map |
| [[Networking Stack — The Machine]] | NIC DMA → softirq → epoll → Reactor → ThreadPool |
| [[Memory System — The Machine]] | malloc → page fault → TLB → cache hierarchy |
| [[Concurrency Runtime — The Machine]] | thread spawn → futex → wake → execute |
| [[C++ Object Lifetime — The Machine]] | ctor → vptr set → use → move → dtor |
| [[Fork and Exec — The Machine]] | fork() → CoW → exec() → ELF load → main() |
| [[Program Startup — The Machine]] | exec() → dynamic linker → constructors → main() |
| [[Virtual Dispatch — The Machine]] | vptr load → vtable → indirect call → cache |
| [[Page Fault — The Machine]] | #PF exception → kernel allocates page → resume |
| [[Request Lifecycle — The Machine]] | application request end-to-end: fd event → response |

→ [[00 - Traversal Paths]] — 5 explicit step-by-step runtime walks (networking, memory, startup, concurrency, plugin)

---

## Level 2 — Domain Maps (after you know the runtime)

Enter each domain through its hub. These map the theory + machine notes for that layer.

| Domain | Hub | Key Machine |
|---|---|---|
| C++ | [[00 - C++ Hub]] | [[C++ Object Lifetime — The Machine]] |
| Linux | [[00 - Linux Hub]] | [[Linux Runtime — The Machine]] |
| Networking | [[00 - Networking Hub]] | [[Networking Stack — The Machine]] |
| Concurrency | [[00 - Concurrency Hub]] | [[Concurrency Runtime — The Machine]] |
| Memory | [[03 - Virtual Memory — The Machine]] | [[Memory System — The Machine]] |
| Build Pipeline | [[01 - Build Process — The Machine]] | [[Program Startup — The Machine]] |
| Design Patterns | [[01 - Reactor Pattern — The Machine]] | [[Concurrency Runtime — The Machine]] |
| Algorithms | [[00 - Algorithms Hub]] | — |

---

## Level 3 — Portals (structured learning paths)

→ [[01 - Learn Systems Engineering]] — full curriculum layer by layer
→ [[02 - Build Runtime Intuition]] — 12 runtime moments with machine links
→ [[03 - Study Tradeoffs]] — why epoll, why UDP, why ThreadPool
→ [[04 - Interview Preparation]] — interview strategy, domain hubs, tracks
→ [[05 - Interview Questions Bank]] — full checklist: C++, Linux, Concurrency, Networking

---

## 1 — Understand the LDS Project

LDS is a Linux live-data server: NBD kernel module → Reactor → ThreadPool → RAID01 → UDP minions.

**The system in one sentence**: kernel write() fires → Reactor reads event → Command queued to ThreadPool → worker writes to storage → reply sent.

**Understand the architecture:**
→ [[01 - LDS System — The Machine]] — full system map: which threads, which fds, which patterns
→ [[02 - Request Lifecycle — The Machine]] — one request end-to-end: NBD → Reactor → RAID → UDP reply
→ [[03 - Reactor — The Machine]] — how the epoll loop dispatches to handlers

**Explain the design decisions:**
→ [[04 - Why UDP not TCP]] — application controls retry; TCP retransmit unacceptable for block I/O SLA
→ [[05 - Why TCP for Client]] — client connections are reliable; delivery guarantee matters here
→ [[06 - Why signalfd not sigaction]] — signals as fds fit the Reactor; sigaction breaks async-signal-safety
→ [[01 - Why RAII]] — destructor fires even on exception; no resource leak possible
→ [[02 - Why Observer Pattern]] — decouple file-event source from multiple consumers
→ [[03 - Why Templates not Virtual Functions]] — zero-cost serialization; no vtable overhead in hot path
→ [[07 - Why IN_CLOSE_WRITE not IN_CREATE]] — IN_CREATE fires before write completes; file is empty

**Walk through the code:**
→ [[02 - main() Wiring Explained]] — how to trace the wiring from memory, thread by thread

---

## 2 — Prepare for the Interview

**Step 1 — See the big picture, then drill each layer.**
→ [[01 - Learn Systems Engineering]] — full curriculum: Layer 1 (build pipeline) → Layer 9 (machine)
→ [[02 - Build Runtime Intuition]] — 12 runtime moments, each showing what the CPU/kernel does

**Step 2 — Answer every question cold.**
→ [[05 - Interview Questions Bank]] — full checklist: C++, Linux, Concurrency, Networking, Algorithms

**Step 3 — Know the tradeoffs.**
→ [[03 - Study Tradeoffs]] — why epoll, why UDP, why ThreadPool — with full context

**Step 4 — Practice explaining LDS.**
→ [[01 - Interview Guide]] — 3-minute pitch, cold Q&A, bugs to mention
→ Use Level 1 above as your anchor: every abstract concept maps to a concrete LDS decision

**The pattern interviewers test:**
```
"What does X do?"
  → API level (what you call)
  → kernel level (what the OS does)
  → hardware level (what the CPU/MMU/NIC does)
```
If you can answer at all three levels, you pass.
