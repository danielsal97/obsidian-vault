# Interview Preparation

Systems engineering interviews test whether you can **explain what the machine is doing** — not whether you can recite the API.

---

## Level 0 — What Interviewers Are Testing

Every interview question is a probe into one or more layers of this stack. The interviewer wants to know if you can trace the path from API call → kernel → hardware.

```
"What does fork() do?"
  → Layer 5 (Linux): creates new task_struct, COW page tables
  → Layer 2 (Memory): child shares physical pages until first write → page fault

"What is a vtable?"
  → Layer 4 (C++): vptr at offset 0, vtable in .rodata, three-instruction dispatch
  → Layer 9 (Machine): cache miss on cold vtable, devirtualization with final

"Why epoll over select?"
  → Layer 6 (Networking): O(1) per-event vs O(n) fd scan; kernel maintains ready list
  → Layer 7 (Design Patterns): Reactor pattern — epoll as the event demultiplexer

"What is a race condition?"
  → Layer 8 (Concurrency): shared write without synchronization
  → Layer 9 (Machine): store buffer not flushed, acquire/release fence prevents reorder
```

**The mental model interviewers want:**
```
your code
  → syscall → kernel subsystem (Scheduler / MM / VFS / Net)
                → hardware (CPU / MMU / NIC / DRAM)
```

If you can answer from BOTH the API level AND the kernel/hardware level, you pass.

---

## Step 1 — Know the theory cold

→ [[01 - Learn Systems Engineering]] — theory: layers 1–8, from build pipeline to concurrency
→ [[02 - Build Runtime Intuition]] — machine: what the CPU and kernel actually execute at each moment

Work through theory top to bottom. Use the machine notes to deepen each layer as you go.
When you can explain every layer without notes, move to Step 2.

---

## Step 2 — Answer interview questions

→ [[05 - Interview Questions Bank]] — every question you might be asked, use as a checklist

Enter each subject from the machine perspective, then drill to theory, Q&A, and glossary:

→ [[00 - C++ Hub]] — RAII · smart pointers · move semantics · vtables · templates · exceptions
→ [[00 - Linux Hub]] — processes · file descriptors · signals · threads · context switch · scheduler
→ [[00 - Networking Hub]] — epoll · TCP · UDP · sockets · IPC · Reactor
→ [[00 - Concurrency Hub]] — thread pool · memory ordering · atomics · false sharing
→ [[00 - Algorithms Hub]] — Big-O · heap · hash table · trie · system design

---

## Step 3 — Know the tradeoffs

Interviewers ask "why" questions constantly. "Why epoll?" "Why UDP?" "Why a thread pool?"

→ [[03 - Study Tradeoffs]] — generic engineering tradeoffs with full context
→ LDS/Decisions/ — LDS-specific decisions with full rationale (use when explaining the project)

---

## Step 4 — Practice explaining the LDS project

The project is the anchor for every abstract concept you know.

→ [[01 - Interview Guide]] — 3-minute pitch, cold Q&A, bugs to mention honestly
→ [[02 - main() Wiring Explained]] — how to walk through the wiring from memory

The pattern: interviewers ask about epoll → explain the Reactor in LDS → show you know both the pattern and a real implementation.

---

## Quick reference during prep

→ [[02 - Interview Prep Track]] — interview stages and what each one tests
→ [[01 - Learning Curriculum]] — full ordered curriculum to track coverage
