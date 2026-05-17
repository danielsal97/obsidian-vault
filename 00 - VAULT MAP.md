# Vault Learning Map

This vault is a live machine you can traverse. Start here. Everything else branches from this node.

---

## The Full Stack — What This Vault Covers

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

Layer 3 — Languages
  C:   open() · read() · write() · malloc() · pointers · structs
  C++: RAII · unique_ptr · move semantics · vtable · templates

Layer 4 — Concurrency
  Thread 1 (Reactor)  │  Thread 2 (worker)  │  Thread 3 (worker)
  mutex · futex · memory ordering · atomics · false sharing

Layer 5 — Networking
  epoll_wait() → socket fd → recv() / send()
  TCP (reliable stream)  │  UDP (unreliable datagram)
  NIC DMA → softirq → socket buffer → epoll ready list → handler

Layer 6 — Design Patterns
  Reactor ──epoll──▶ handler dispatch ──Command──▶ ThreadPool
  Observer · Factory · Singleton · Strategy

Layer 0 — Hardware
  CPU cores │ MMU+TLB │ L1/L2/L3 cache │ DRAM │ NIC │ SSD
```

---

## Two Learning Paths

### Path A — LDS Project (systems engineering in practice)
→ [[LDS/00 START HERE|LDS Start Here]] — the live C++ system: NBD → Reactor → RAID → UDP

### Path B — Core Study (master every layer above)
→ [[Core/00 START HERE|Core Start Here]] — full curriculum from hardware to patterns

---

## Runtime Traversals — Walk Through the Machine

These notes trace real execution paths through the stack. Read them after understanding the architecture.

→ [[00 - Traversal Paths]] — 5 explicit runtime walks: networking, memory, startup, concurrency, plugin

Quick access to the key cross-system machines:
→ [[Linux Runtime — The Machine]] — all 6 kernel subsystems at once
→ [[Networking Stack — The Machine]] — NIC DMA → epoll → Reactor → ThreadPool
→ [[Memory System — The Machine]] — malloc → page fault → TLB → cache
→ [[Concurrency Runtime — The Machine]] — thread spawn → futex → wake cycle
→ [[C++ Object Lifetime — The Machine]] — ctor → use → move → dtor

---

## Quick Jump by Topic

| Topic | Entry | Key Machine |
|---|---|---|
| epoll / Reactor | [[03 - Reactor]] | [[03 - Reactor — The Machine]] |
| Memory / paging | [[03 - Virtual Memory — The Machine]] | [[Memory System — The Machine]] |
| TCP / UDP / sockets | [[06 - Networking Hub]] | [[Networking Stack — The Machine]] |
| Threading / futex | [[01 - Multithreading Patterns — The Machine]] | [[Concurrency Runtime — The Machine]] |
| C++ RAII / smart ptrs | [[00 - C++ Hub]] | [[C++ Object Lifetime — The Machine]] |
| Linux processes | [[00 - Linux Hub]] | [[Linux Runtime — The Machine]] |
| Build pipeline | [[01 - Build Process — The Machine]] | [[Program Startup — The Machine]] |
| LDS full pipeline | [[01 - LDS System — The Machine]] | [[02 - Request Lifecycle — The Machine]] |
