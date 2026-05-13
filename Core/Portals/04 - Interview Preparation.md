# Interview Preparation

Systems engineering interviews test whether you can **explain what the machine is doing** — not whether you can recite the API.

---

## Step 1 — Know the theory cold

Work through [[01 - Learn Systems Engineering]] in order.
When you can explain every layer without notes, move to Step 2.

---

## Step 2 — Build runtime intuition

Work through [[02 - Build Runtime Intuition]].
The difference between a good candidate and a great one: "RAII means the destructor cleans up" vs "when this `unique_ptr` goes out of scope, the stack unwinds, the destructor fires, and the file descriptor is closed — even if an exception was thrown."

---

## Step 3 — Answer interview questions

These Q&A files are interview-format: question → concise answer. Cover them until the answers are automatic.

→ [[../Domains/03 - C++/Interview/01 - C++ Language Q&A]]
— RAII, move semantics, vtables, templates, smart pointers, Rule of Five, noexcept

→ [[../Domains/05 - Concurrency/Interview/01 - Concurrency Q&A]]
— mutex, race conditions, deadlock, condition variables, atomic, memory ordering

→ [[../Domains/04 - Linux/Interview/01 - Linux Q&A]]
— fork/exec, signals, file descriptors, mmap, inotify

→ [[../Domains/06 - Networking/Interview/01 - Networking Q&A]]
— epoll vs select, TCP sockets, TCP framing, byte ordering, UDP vs TCP

→ [[../Domains/08 - Algorithms/Interview/01 - Data Structures Q&A]]
— Big-O, heap/priority queue, hash table, trie, system design

---

## Step 4 — Know the tradeoffs

Interviewers ask "why" questions constantly. "Why epoll?" "Why UDP?" "Why a thread pool?"

→ [[03 - Study Tradeoffs]] — generic engineering tradeoffs with full context
→ LDS/Decisions/ — LDS-specific decisions with full rationale (use when explaining the project)

---

## Step 5 — Practice explaining the LDS project

The project is the anchor for every abstract concept you know.

→ LDS/Interview/01 - Interview Guide — 3-minute pitch, cold Q&A, bugs to mention honestly
→ LDS/Interview/02 - main() Wiring Explained — how to walk through the wiring from memory

The pattern: interviewers ask about epoll → explain the Reactor in LDS → show you know both the pattern and a real implementation.

---

## Quick reference during prep

→ [[../Tracks/02 - Interview Prep Track]] — interview stages and what each one tests
→ [[../Tracks/01 - Learning Curriculum]] — full ordered curriculum to track coverage
