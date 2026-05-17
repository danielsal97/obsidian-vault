# Study Tradeoffs

Tradeoffs answer: **"why was this chosen over the alternatives?"**

The right answer in an interview is never just "X is faster." It's: here was the context, here were the options, here is the concrete reason X was chosen, here is what you give up.

---

## Level 0 — Where These Tradeoffs Live in the System

Every tradeoff below is a decision at a specific layer of the stack. Understanding which layer clarifies the constraints:

```
[source.cpp] → [ELF binary] → [process]
                                   │
              ┌────────────────────┴──────────────────────┐
              │                                           │
        [Reactor thread]                         [Worker threads]
         epoll_wait()                            process requests
              │                                           │
              │← I/O Model tradeoff (epoll vs select) ──→│
              │                                           │
              │← Threading Model (inline vs ThreadPool) →│
              │
         socket fd
              │← Transport Protocol (TCP vs UDP) ────────→[NIC → wire]
```

| Tradeoff | Layer | The question |
|---|---|---|
| epoll over select/poll | Networking (Layer 6) | How does the Reactor wait for events without blocking? |
| Reactor over thread-per-conn | Design Patterns (Layer 7) | How do we serve many connections with one thread? |
| UDP over TCP | Networking (Layer 6) | Who controls reliability: kernel (TCP) or application? |
| ThreadPool over inline | Concurrency (Layer 8) | Where does CPU work run relative to I/O completion? |

---

## I/O Model

**Why epoll over select/poll?**
→ [[01 - Why epoll over select and poll]] — O(1) per-event cost vs O(n) fd scanning; kernel maintains ready list

Context: [[04 - epoll]] — full epoll API and internals
Runtime: [[04 - epoll — The Machine]] — how the ready list is populated and drained

**Why Reactor over thread-per-connection?**
→ [[01 - Reactor]] — one thread, one epoll loop, no per-connection stack cost
Runtime: [[01 - Reactor Pattern — The Machine]] — how epoll becomes a dispatch table

---

## Transport Protocol

**Why UDP not TCP for storage I/O?**
→ [[02 - Why UDP vs TCP]] — application controls retry/timeout; TCP retransmit delay unacceptable for block storage SLA

Context: [[02 - Sockets TCP]] · [[03 - UDP Sockets]]
Runtime: [[03 - UDP Sockets — The Machine]] · [[02 - TCP Sockets — The Machine]]

---

## Threading Model

**Why ThreadPool over inline execution?**
→ [[01 - Why ThreadPool over inline execution]] — decouple I/O from CPU; bounded thread count; work queued not blocked

Context: [[01 - Multithreading Patterns]] — thread pool, WPQ, producer/consumer
Runtime: [[01 - Multithreading Patterns — The Machine]] — how threads idle, wake, steal, and complete work

---

## LDS-specific decisions → LDS vault

For decisions specific to the LDS implementation (not generic engineering tradeoffs):
→ LDS/Decisions/04 - Why UDP not TCP
→ LDS/Decisions/05 - Why TCP for Client
→ LDS/Decisions/06 - Why signalfd not sigaction
→ LDS/Decisions/01 - Why RAII
→ LDS/Decisions/02 - Why Observer Pattern
→ LDS/Decisions/03 - Why Templates not Virtual Functions
→ LDS/Decisions/07 - Why IN_CLOSE_WRITE not IN_CREATE
