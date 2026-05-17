# Interview Questions Bank

Every question you are likely to be asked. Use as a checklist — tick off what you can answer cold.
Answers live in the domain Q&A files linked at each section.

**Answering pattern**: API level → kernel/hardware level → tradeoff. One sentence each.

---

## Level 0 — The System Under Test

Every section below probes a different part of the runtime:

```
 ┌─ C++ Language ─── object lifetime: ctor → vptr → use → move → dtor
 │
 ├─ Concurrency ──── shared state: mutex → futex → acquire/release fence
 │
 ├─ Linux & OS ───── process model: fork/exec → fd table → scheduler → signals
 │
 ├─ Networking ───── packet path: NIC DMA → epoll → Reactor → ThreadPool
 │
 └─ Algorithms ───── complexity: Big-O → heap → hash → system design
```

---

## C++ Language
*Machine: [[C++ Object Lifetime — The Machine]] · [[Virtual Dispatch — The Machine]]*
→ Full answers: [[01 - C++ Language Q&A]]

**Memory & allocation**
- What's the difference between stack and heap allocation?
- What is RAII? Give a concrete example.
- What is a memory leak? How does RAII prevent it?
- What is use-after-free? How do you catch it?
- What does `valgrind` / ASan catch?

**Smart pointers**
- When do you use `unique_ptr` vs `shared_ptr`?
- What is `weak_ptr` for? When does `lock()` return null?
- What is the control block in `shared_ptr`? How is the refcount managed?
- What happens when the last `shared_ptr` to an object is destroyed?

**Move semantics**
- What is the difference between an lvalue and an rvalue?
- What does `std::move` actually do?
- What is the Rule of Five?
- Why must move constructors be `noexcept`?
- What is copy elision / RVO?

**Virtual functions & vtables**
- What is a vtable? How is a virtual call dispatched?
- What is object slicing? When does it happen?
- What is a pure virtual function? What is an abstract class?
- Why should destructors be virtual in a base class?

**Templates**
- What is the difference between a function template and a class template?
- What is template specialization?
- What is SFINAE?

**Exceptions**
- What are the exception safety levels (basic, strong, nothrow)?
- What does `noexcept` do? What happens if a `noexcept` function throws?
- How does stack unwinding work? When do destructors run?

---

## Concurrency
*Machine: [[Concurrency Runtime — The Machine]] · [[04 - Atomics — The Machine]] · [[03 - False Sharing — The Machine]]*
→ Full answers: [[01 - Concurrency Q&A]]

**Mutual exclusion**
- What is a race condition? Give an example.
- What is a mutex? What is a deadlock?
- What are the four conditions for deadlock (Coffman conditions)?
- What is a condition variable? How do you use it with a mutex?
- What is a spurious wakeup? How do you defend against it?

**Atomics & memory ordering**
- What is an atomic operation? How is it different from a mutex?
- What is `memory_order_relaxed`? When is it safe?
- What is acquire/release semantics? What guarantee does it give?
- What is a happens-before relationship?
- What is a memory barrier / fence?

**Concurrency patterns**
- What is a thread pool? How does the work queue work?
- What is the producer/consumer pattern? How do you implement it?
- What is false sharing? How do you fix it?
- What is a CAS loop? When would you use one?

---

## Linux & OS
*Machine: [[Linux Runtime — The Machine]] · [[Fork and Exec — The Machine]] · [[Page Fault — The Machine]]*
→ Full answers: [[01 - Linux Q&A]]

**Processes**
- What does `fork()` do? What is copy-on-write?
- What is the difference between `fork()` and `exec()`?
- What is a zombie process? How do you prevent it?
- What is `waitpid()`? What is `WNOHANG`?

**File descriptors**
- What is a file descriptor? What does the kernel store per fd?
- What happens to fds on `fork()`?
- What is `CLOEXEC`? Why do you want it?

**Signals**
- What is a signal? How do you install a signal handler?
- What is async-signal-safety? Why does it matter?
- What is `signalfd`? Why is it better for event loops?
- What is `SIGPIPE`? When is it sent? How do you suppress it?

**Memory mapping**
- What is `mmap()`? What is the difference between `MAP_PRIVATE` and `MAP_SHARED`?
- What is a page fault? What happens in the kernel when one occurs?
- What is `inotify`? What events does LDS watch for?

**Threads**
- What is the difference between a process and a thread?
- What does `pthread_create()` do at the kernel level?
- What is thread-local storage (TLS)?

---

## Networking
*Machine: [[Networking Stack — The Machine]] · [[04 - epoll — The Machine]] · [[02 - TCP Sockets — The Machine]]*
→ Full answers: [[01 - Networking Q&A]]

**I/O multiplexing**
- What is the difference between `select`, `poll`, and `epoll`?
- What is level-triggered vs edge-triggered epoll?
- What is `EPOLLET`? What bug does it introduce if you don't drain the buffer?
- What does `epoll_wait()` return? What does the kernel put in the ready list?

**TCP**
- What is the TCP three-way handshake?
- What is a RecvAll loop? Why is it necessary?
- What is TCP framing? How do you know where a message ends?
- What is the TCP receive window?
- What is `TIME_WAIT`? When does it occur?

**UDP**
- What is the difference between UDP and TCP?
- Does UDP preserve message boundaries? Does TCP?
- What is MTU? What happens if a UDP datagram exceeds it?

**Byte ordering**
- What is endianness? What is the network byte order?
- What do `htons` / `ntohl` do?

**Sockets**
- What does `SO_REUSEADDR` do?
- What is a non-blocking socket? How do you detect `EAGAIN`?

---

## Data Structures & Algorithms
*Machine: [[09 - Cache Hierarchy — The Machine (deep)]] — why vector beats list 100x*
→ Full answers: [[01 - Data Structures Q&A]]

**Complexity**
- What is Big-O notation? Give the complexity of common operations.
- What is the difference between O(n log n) and O(n²) in practice?
- What is amortised complexity? Example: `std::vector::push_back`.

**Data structures**
- When do you use a heap / priority queue? How is it implemented?
- How does a hash table work? What is a collision? Open addressing vs chaining?
- What is a trie? When is it better than a hash map?
- What is the difference between a stack and a queue?
- What is a deque?

**System design**
- How would you design a rate limiter?
- How would you design a cache with LRU eviction?
- How would you handle 10,000 concurrent connections?
- How would you scale a service that is CPU-bound? I/O-bound?

---

## LDS Project
→ Full answers: [[01 - Interview Guide]]
→ Wiring walkthrough: [[02 - main() Wiring Explained]]

**Project overview**
- What does LDS do in one sentence?
- What is the end-to-end flow from file change to client delivery?
- How many threads does LDS run? What does each one do?

**Design decisions**
- Why did you choose UDP over TCP for delivery?
- Why did you use `inotify` + `IN_CLOSE_WRITE` instead of `IN_CREATE`?
- Why `signalfd` instead of `sigaction`?
- Why the Reactor pattern? Why not one thread per connection?
- Why templates instead of virtual functions in the serializer?

**Show you know the machine**
- Walk me through what happens when a file is written to disk.
- What happens between `epoll_wait()` returning and the handler firing?
- How does RAII protect you when an exception is thrown mid-request?
- What bugs have you found in LDS? How did you debug them?

---

## Tradeoffs (expect "why" questions on everything above)
→ [[03 - Study Tradeoffs]]

- Why epoll over select?
- Why a thread pool over spawning a thread per request?
- Why `unique_ptr` over raw pointer?
- Why UDP if you need reliability?
- Why RAII over manual cleanup?
