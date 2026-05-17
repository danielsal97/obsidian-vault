# Core — Systems Engineering

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
Every bug, every design decision, every interview question lives at one of these transitions.

---

## 1 — Understand the LDS Project

LDS is a Linux live-data server: it watches files via inotify, serves reads over UDP, and delivers changes to clients over TCP. It implements every concept in the stack diagram above.

**The system in one sentence**: inotify fd fires → Reactor reads event → Command queued to ThreadPool → worker reads file → UDP reply sent.

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
→ [[01 - Interview Guide]] — 3-minute pitch, cold Q&A, bugs to mention honestly
→ Use entry 1 above as your anchor: every abstract concept maps to a concrete LDS decision

**The pattern interviewers test:**
```
"What does X do?"
  → API level (what you call)
  → kernel level (what the OS does)
  → hardware level (what the CPU/MMU/NIC does)
```
If you can answer at all three levels, you pass.
