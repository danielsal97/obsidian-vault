# Study Tradeoffs

Tradeoffs answer: **"why was this chosen over the alternatives?"**

The right answer in an interview is never just "X is faster." It's: here was the context, here were the options, here is the concrete reason X was chosen, here is what you give up.

---

## I/O Model

**Why epoll over select/poll?**
→ [[../Domains/06 - Networking/Tradeoffs/01 - Why epoll over select and poll]] — O(1) per-event cost vs O(n) fd scanning; kernel maintains ready list

Context: [[../Domains/06 - Networking/Theory/04 - epoll]] — full epoll API and internals
Runtime: [[../Domains/06 - Networking/Mental Models/04 - epoll — The Machine]] — how the ready list is populated and drained

**Why Reactor over thread-per-connection?**
→ [[../Domains/07 - Design Patterns/Theory/01 - Reactor]] — one thread, one epoll loop, no per-connection stack cost
Runtime: [[../Domains/07 - Design Patterns/Mental Models/01 - Reactor Pattern — The Machine]] — how epoll becomes a dispatch table

---

## Transport Protocol

**Why UDP not TCP for storage I/O?**
→ [[../Domains/06 - Networking/Tradeoffs/02 - Why UDP vs TCP]] — application controls retry/timeout; TCP retransmit delay unacceptable for block storage SLA

Context: [[../Domains/06 - Networking/Theory/02 - Sockets TCP]] · [[../Domains/06 - Networking/Theory/03 - UDP Sockets]]
Runtime: [[../Domains/06 - Networking/Mental Models/03 - UDP Sockets — The Machine]] · [[../Domains/06 - Networking/Mental Models/02 - TCP Sockets — The Machine]]

---

## Threading Model

**Why ThreadPool over inline execution?**
→ [[../Domains/05 - Concurrency/Tradeoffs/01 - Why ThreadPool over inline execution]] — decouple I/O from CPU; bounded thread count; work queued not blocked

Context: [[../Domains/05 - Concurrency/Theory/01 - Multithreading Patterns]] — thread pool, WPQ, producer/consumer
Runtime: [[../Domains/05 - Concurrency/Mental Models/01 - Multithreading Patterns — The Machine]] — how threads idle, wake, steal, and complete work

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
