# The Plan — Getting My First C++ Job

**Goal:** First C++ systems/backend offer  
**Started:** 2026-05-08 | **Target:** Offer by 2026-07-31

---

## The Core Rule

**Don't wait to be ready. Apply from Week 1.**
Hiring pipelines take 3–5 weeks. Start filling the pipeline today while learning and building in parallel. By the time screens arrive, you'll be ready.

---

## Daily Structure

```
Morning  (1–2 hrs)   Study — one topic from the weekly plan below
Afternoon (2–3 hrs)  Build — next task in LDS Phase 2
Evening  (30 min)    Apply — 2–3 job applications + follow up
```

---

## Week-by-Week Plan

### Week 1 — Foundation + Launch (May 8–14)

**The goal this week:** Understand how code becomes a running program, get the repo polished, send the first applications, and start drilling the pitch.

| Area | Task |
|---|---|
| **Study** | [[Engineering/Build Process]] → [[Engineering/Build Process/1 - Preprocessor\|Preprocessor]] → [[Engineering/Build Process/2 - Compiler\|Compiler]] → [[Engineering/Build Process/3 - Assembler\|Assembler]] → [[Engineering/Build Process/4 - Linker\|Linker]] → [[Engineering/Build Process/Make and CMake\|Make & CMake]] |
| **Study** | [[Engineering/Memory/Process Memory Layout\|Process Memory Layout]] → [[Engineering/Memory/Stack vs Heap\|Stack vs Heap]] → [[Engineering/C/Memory - malloc and free\|malloc and free]] |
| **Interview prep** | Memorise the LDS pitch — [[LDS/Engineering/Interview Guide]]. Record yourself. No notes. |
| **Interview prep** | [[Engineering/Algorithms/Big-O and Complexity\|Big-O]] + [[Engineering/Algorithms/Data Structures\|Data Structures]] — these don't require any prior knowledge, do them now |
| **LDS** | Add gtest unit tests (3 files) — [[LDS/Manager/Job Search Plan]] checklist |
| **LDS** | Add GitHub Actions CI — green checkmark on every commit |
| **Apply** | Send first 5–10 applications — [[LDS/Manager/Job Search Plan]] |

---

### Week 2 — C Language + Coding Practice (May 15–21)

**The goal:** Know C cold. Coding rounds test this daily. Start LeetCode.

| Area | Task |
|---|---|
| **Study** | [[Engineering/C/Pointers\|Pointers]] → [[Engineering/C/Structs and Unions\|Structs]] → [[Engineering/C/Bitwise Operations\|Bitwise]] → [[Engineering/C/Strings\|Strings]] → [[Engineering/C/File IO\|File IO]] → [[Engineering/C/Serialization\|Serialization]] → [[Engineering/C/Undefined Behavior\|Undefined Behavior]] |
| **Interview prep** | LeetCode: 1 problem/day — arrays and hash maps only (Easy → Medium) |
| **Interview prep** | Can you explain Big-O of every data structure without notes? |
| **LDS** | Phase 2 — MinionProxy skeleton: define the interface and UDP send |
| **Apply** | 3–5 applications/day |

---

### Week 3 — Linux OS + Algorithms (May 22–28)

**The goal:** Understand how the OS runs your program. Know every data structure cold.

| Area | Task |
|---|---|
| **Study** | [[Engineering/Linux/File Descriptors\|File Descriptors]] → [[Engineering/Linux/Processes\|Processes]] → [[Engineering/Linux/Signals\|Signals]] → [[Engineering/Memory/Memory Errors and Tools\|Memory Errors]] → [[Engineering/Kernel\|Kernel]] → [[Engineering/Linux/gdb Debugging\|gdb]] |
| **Interview prep** | LeetCode: 1 problem/day — linked lists + two pointers |
| **Interview prep** | Explain: what is a file descriptor? what happens on fork()? what is epoll? |
| **LDS** | Phase 2 — MinionProxy: UDP send with MSG_ID, basic retry loop |
| **Apply** | 3–5/day. First screens may start arriving — [[LDS/Engineering/Interview Guide]] ready |

---

### Week 4 — C++ Core Part 1 (May 29 – Jun 4)

**The goal:** C++ fundamentals cold. This is what every C++ interview tests first.

| Area | Task |
|---|---|
| **Study** | [[Engineering/C++/RAII\|RAII]] → [[Engineering/C++/Smart Pointers\|Smart Pointers]] → [[Engineering/C++/Move Semantics\|Move Semantics]] → [[Engineering/C++/Virtual Functions\|Virtual Functions]] → [[Engineering/C++/Inheritance\|Inheritance]] → [[Engineering/C++/Templates\|Templates]] |
| **Interview prep** | [[LDS/Engineering/Interview - C++ Language]] — answer every question without looking |
| **Interview prep** | LeetCode: 1 problem/day — stacks, queues, heaps |
| **LDS** | Phase 2 — ResponseManager: match MSG_IDs, handle timeouts |
| **Apply** | 3–5/day. If screens are active: prep over applying |

---

### Week 5 — C++ Core Part 2 + Concurrency (Jun 5–11)

**The goal:** Complete C++. Add concurrency — systems roles always ask this.

| Area | Task |
|---|---|
| **Study** | [[Engineering/C++/STL Containers\|STL]] → [[Engineering/C++/Exception Handling\|Exceptions]] → [[Engineering/C++/Type Casting\|Type Casting]] → [[Engineering/C++/Effective C++ - Meyers\|Meyers]] → [[Engineering/C++/Version Comparison\|Versions]] |
| **Study** | [[Engineering/Linux/Threads - pthreads\|pthreads]] → [[Engineering/Concurrency/Multithreading Patterns\|Multithreading Patterns]] → [[Engineering/Concurrency/Memory Ordering\|Memory Ordering]] |
| **Interview prep** | [[LDS/Engineering/Interview - Concurrency]] — race conditions, deadlock, condition_variable |
| **Interview prep** | LeetCode: 1 problem/day — binary search + sorting |
| **LDS** | Phase 2 — Scheduler: exponential backoff, timeout tracking |
| **Apply** | 3–5/day or active screens |

---

### Week 6 — Networking + Systems Prep (Jun 12–18)

**The goal:** Networking from socket to wire. This is where LDS shines.

| Area | Task |
|---|---|
| **Study** | [[Engineering/Networking/Overview\|Networking Overview]] → [[Engineering/Networking/Sockets TCP\|TCP Sockets]] → [[Engineering/Networking/UDP Sockets\|UDP]] → [[Engineering/Networking/epoll\|epoll]] → [[Engineering/Networking/IPC Overview\|IPC]] |
| **Study** | [[Engineering/Linux/Shared Memory\|Shared Memory]] → [[Engineering/Linux/Semaphores\|Semaphores]] → [[Engineering/Linux/mmap\|mmap]] |
| **Interview prep** | [[LDS/Engineering/Interview - Linux & Networking]] — epoll, TCP, byte ordering, fork |
| **Interview prep** | Practice: walk through a write() to /dev/nbd0 end-to-end — [[LDS/Request Lifecycle]] |
| **LDS** | Phase 2 — complete RAID01Manager or begin integration |
| **Apply** | Active screens + first onsites may start |

---

### Week 7 — Design Patterns + LDS Architecture (Jun 19–25)

**The goal:** Formalise the patterns you built. Be able to draw and defend every LDS design decision.

| Area | Task |
|---|---|
| **Study** | [[Engineering/Design Patterns/Reactor\|Reactor]] → [[Engineering/Design Patterns/Observer\|Observer]] → [[Engineering/Design Patterns/Command\|Command]] → [[Engineering/Design Patterns/Factory\|Factory]] → [[Engineering/Design Patterns/Strategy\|Strategy]] → [[Engineering/Design Patterns/Singleton\|Singleton]] |
| **Study** | [[Engineering/DevOps/Docker\|Docker]] + [[Engineering/C++/C++20/Overview\|C++20]] |
| **Interview prep** | For each LDS pattern: say out loud — *why* this pattern, *what* the alternative was, *what* it gave you |
| **Interview prep** | Practice drawing the LDS architecture diagram from memory |
| **LDS** | Polish: ASan clean run, README up to date, CI green |
| **Apply** | Onsites — full interview prep mode |

---

### Week 8 — Review + Interview Sprint (Jun 26 – Jul 2)

**The goal:** No new topics. Pure retrieval and practice.

| Area | Task |
|---|---|
| **Review** | Go through [[Strategy/Progress Tracker]] — any unchecked topics, do them now |
| **Review** | Re-read [[LDS/Engineering/Known Bugs]] — pick 2–3 as debugging stories |
| **Interview prep** | Full mock: pitch → coding problem → C++ question → concurrency → systems |
| **Interview prep** | Time your answers. Weak spots: re-read the relevant file, redo the Understanding Check |
| **LDS** | Any remaining Phase 2 tasks |
| **Apply** | Close open processes, negotiate |

---

## Progress Snapshot

| Area | Status |
|---|---|
| Topics studied | 0 / 57 — [[Strategy/Progress Tracker\|tracker]] |
| Applications sent | 0 — [[LDS/Manager/Job Search Plan\|tracker]] |
| Technical screens | 0 |
| LDS phase | [[LDS/00 Dashboard\|Phase 2 — Active]] |

---

## Reference Files

*Open these when you need depth — not daily.*

| File | Use it for |
|---|---|
| [[Strategy/Progress Tracker]] | Tick off topics as you complete them |
| [[Strategy/Learning Curriculum]] | Full topic list with times and LDS tie-ins |
| [[Strategy/Interview Prep Track]] | Interview stage details and question lists |
| [[LDS/Manager/Job Search Plan]] | Applications, CV bullets, where to apply |
| [[LDS/Engineering/Interview Guide]] | The pitch + cold Q&A |
| [[Engineering/00 Dashboard]] | All Engineering topics by category |
