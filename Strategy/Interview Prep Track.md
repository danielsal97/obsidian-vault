# Interview Prep Track

Separate from the Learning Curriculum. This is interview-first order — what gets tested, how often, and in what round.

**Rule:** You don't need to finish the full curriculum before applying. Start applying Week 1. Prep runs in parallel.

---

## Stage 0 — Before You Send a Single Application
*Takes 1–2 days. Do this once.*

- [ ] Memorise the 3-minute LDS pitch — [[LDS/Engineering/Interview Guide]]
- [ ] Record yourself saying it. Listen back. Is it clear to someone who doesn't know LDS?
- [ ] CV updated with LDS bullet points — [[LDS/Manager/Job Search Plan]]
- [ ] GitHub repo polished — README done ✅, branches clean ✅
- [ ] gtest unit tests added (shows professional, not student)
- [ ] GitHub Actions CI — green checkmark on every commit

---

## Stage 1 — Phone Screen / HR Screen
*"Tell me about yourself. What did you build?"*

This is a pitch + background conversation. No coding yet.

**What you need ready:**
- [ ] LDS pitch — 3 minutes, hits: epoll, RAID01, TCP, UDP, async, plugin system, C++20
- [ ] One technical challenge story — pick from [[LDS/Engineering/Known Bugs]]
  - Format: "I noticed X → I traced it to Y → I fixed it by Z"
- [ ] Why you want this specific company/role — research it before each call
- [ ] Salary expectations — know your number

**Practice:**
- Say the pitch out loud 10 times until it's fluent
- Answer "what was the hardest bug you fixed?" without hesitation

---

## Stage 2 — Coding Round
*"Write a function that..."*

**This is the gating factor.** Fail here and nothing else matters. Study this first.

### Data Structures (must know cold)
- [ ] [[Engineering/Algorithms/Data Structures]] — read the file
- [ ] Array / vector — know push_back amortised O(1), insert O(n)
- [ ] Hash map (`unordered_map`) — O(1) avg lookup, `at()` vs `[]` difference
- [ ] Priority queue (heap) — O(log n) push/pop, O(1) top — LDS WPQ uses this
- [ ] Linked list — O(1) insert at known position, O(n) access
- [ ] BST / `std::map` — O(log n) guaranteed, sorted iteration

### Complexity (must recognise on sight)
- [ ] [[Engineering/Algorithms/Big-O and Complexity]] — read the file
- [ ] Identify O(n²) nested loops, O(n log n) sort+scan, O(log n) halving
- [ ] Know: `std::sort` is O(n log n), hash lookup is O(1) avg, binary search is O(log n)

### Coding Patterns (practice these)
- [ ] **Two pointers** — sorted array pair sum, removing duplicates
- [ ] **Sliding window** — max subarray, longest substring without repeat
- [ ] **Hash map for O(1) lookup** — two sum, frequency count, anagram check
- [ ] **Binary search** — find target in sorted array, `lo + (hi-lo)/2`
- [ ] **Heap for top-k** — k largest elements, merge k sorted lists

### Practice Rule
Every pattern above: write the code from scratch, no notes. Time yourself. If you can't do it in 10 minutes, you need more practice.

**Resources:** LeetCode Easy → Medium. Focus on arrays + hash maps first, then strings, then trees.

---

## Stage 3 — C++ Technical Round
*"Explain RAII. What's the difference between unique_ptr and shared_ptr? What does virtual do?"*

### Must Know Cold (explain without notes)
- [ ] [[Engineering/C++/RAII]] — what it is, why it matters, what happens without it
- [ ] [[Engineering/C++/Smart Pointers]] — unique_ptr vs shared_ptr vs weak_ptr, when to use each
- [ ] [[Engineering/C++/Move Semantics]] — lvalue vs rvalue, what std::move does, Rule of Five
- [ ] [[Engineering/C++/Virtual Functions]] — vtable, override, pure virtual, virtual destructor
- [ ] [[Engineering/C++/Templates]] — why implementation is in headers, SFINAE basics
- [ ] [[Engineering/C++/Effective C++ - Meyers]] — the non-obvious rules

### Common C++ Interview Questions
- [ ] "What is RAII?" → resource lifetime tied to object lifetime, stack unwinding calls destructor
- [ ] "unique_ptr vs shared_ptr?" → sole ownership vs ref-counted shared ownership
- [ ] "What happens if you don't declare a virtual destructor?" → derived destructor not called on delete via base pointer, memory/resource leak
- [ ] "What is object slicing?" → assigning derived to base by value loses the derived part
- [ ] "What does std::move do?" → just a cast to rvalue reference, enables move constructor
- [ ] "Why are templates in headers?" → compiler needs the full definition to instantiate
- [ ] "What is the Rule of Five?" → if you define any of {destructor, copy ctor, copy=, move ctor, move=}, define all five

### Full reference: [[LDS/Engineering/Interview - C++ Language]]

---

## Stage 4 — Concurrency Round
*"How do you prevent a race condition? What's a deadlock? Explain condition_variable."*

- [ ] [[Engineering/Concurrency/Multithreading Patterns]] — thread pool, producer/consumer
- [ ] [[Engineering/Linux/Threads - pthreads]] — mutex, condition variable, why `while` loop
- [ ] [[Engineering/Concurrency/Memory Ordering]] — atomic, acquire/release basics

### Common Concurrency Interview Questions
- [ ] "What is a race condition?" → two threads access shared data, at least one writes, no synchronisation
- [ ] "What is a deadlock?" → thread A holds lock 1, waits for lock 2; thread B holds lock 2, waits for lock 1
- [ ] "How do you prevent deadlock?" → always acquire locks in the same order; use `std::lock()` for multiple locks
- [ ] "Why does condition_variable need a while loop?" → spurious wakeups — the condition may be false even after waking
- [ ] "What is the LDS ThreadPool?" → fixed pool of worker threads, WPQ feeds work with WRITE > READ > FLUSH priority

### Full reference: [[LDS/Engineering/Interview - Concurrency]]

---

## Stage 5 — Systems Round
*"How does epoll work? What's a file descriptor? Explain the LDS architecture."*

This comes in later rounds, often at systems-focused companies.

- [ ] [[Engineering/Networking/epoll]] — select vs poll vs epoll, O(1), level vs edge triggered
- [ ] [[Engineering/Linux/File Descriptors]] — everything is a file, fd lifecycle, CLOEXEC
- [ ] [[Engineering/Linux/Processes]] — fork, exec, wait, copy-on-write
- [ ] [[Engineering/Networking/Sockets TCP]] — socket lifecycle, RecvAll loop
- [ ] [[Engineering/Kernel]] — syscalls, virtual memory, scheduling

### Common Systems Interview Questions
- [ ] "Why epoll instead of select?" → epoll is O(1) per event vs O(n) scan; scales to thousands of fds
- [ ] "What is a file descriptor?" → small integer per-process handle to a kernel resource
- [ ] "What happens on fork()?" → child gets a copy of parent's virtual address space (copy-on-write, cheap)
- [ ] "Walk me through a write() to /dev/nbd0 in LDS" → [[LDS/Request Lifecycle]]

### Full reference: [[LDS/Engineering/Interview - Linux & Networking]]

---

## Stage 6 — Design Round
*"How would you design X? Walk me through your LDS architecture."*

- [ ] [[LDS/System Overview]] — be able to draw the architecture from memory
- [ ] [[LDS/Request Lifecycle]] — trace a read/write request end-to-end
- [ ] For each design pattern in LDS: why you chose it, what the alternative was
  - Reactor → why not thread-per-connection?
  - Strategy (IDriverComm) → why not if/else on mode?
  - Observer (Dispatcher<T>) → why templates not virtual?
  - Factory → why not direct instantiation?

---

## The Pitch (Memorise This)

> "I built a distributed NAS system in C++20 on Linux. The core is an epoll Reactor loop that handles both NBD kernel requests and TCP client connections. Data is distributed across storage nodes using RAID01 — every block goes to two nodes for redundancy. I implemented the full stack: the event loop, a plugin system using dlopen for runtime extensibility, a TCP server as a drop-in replacement for the NBD kernel interface so remote clients can read and write blocks over the network, and async UDP with message IDs and exponential backoff for minion communication."

**Hit these words: epoll, RAID01, TCP, UDP, async, plugin system, C++20.**

---

## Weekly Interview Prep Checklist

Run through this every week once you're applying:

- [ ] Pitch said out loud at least once today
- [ ] One coding problem solved (LeetCode Easy/Medium)
- [ ] One C++ concept explained to yourself without notes
- [ ] Applications sent today: ___
- [ ] Follow-ups sent on pending applications

---

## Related
- [[LDS/Engineering/Interview Guide]] — cold Q&A, pitch variants
- [[LDS/Engineering/Interview - Data Structures]] — DS interview Q&A
- [[LDS/Manager/Job Search Plan]] — application tracker, where to apply
- [[Strategy/Progress Tracker]] — full study checklist
