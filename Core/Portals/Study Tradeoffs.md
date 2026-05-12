# Study Tradeoffs

Tradeoffs answer: "why was this chosen over the alternatives?"

These notes are for interview prep and design discussions.
Each note states the context, options considered, and the concrete reason for the choice.

---

## I/O and Event Loop

→ [[../Tradeoffs/Why epoll over select and poll]]
→ [[../Tradeoffs/Why Reactor over thread-per-connection]]
→ [[../Theory/Networking/epoll]] — full epoll theory (the what)
→ [[../Mental Models/epoll — The Machine]] — the runtime intuition (the feel)
→ [[../Mental Models/Reactor Pattern — The Machine]] — how Reactor executes

---

## Transport Protocol

→ [[../Tradeoffs/Why UDP vs TCP]]
→ [[../Theory/Networking/Sockets TCP]] — TCP theory
→ [[../Theory/Networking/UDP Sockets]] — UDP theory

---

## Threading and Work Queues

→ [[../Tradeoffs/Why ThreadPool over inline execution]]
→ [[../Theory/Concurrency/Multithreading Patterns]] — thread pool theory
→ [[../Mental Models/Multithreading Patterns — The Machine]] — how it executes

---

## LDS-specific decisions → LDS vault

For decisions specific to the LDS project (not generic engineering):
→ LDS/Decisions/Why UDP not TCP
→ LDS/Decisions/Why TCP for Client
→ LDS/Decisions/Why signalfd not sigaction
→ LDS/Decisions/Why RAII
→ LDS/Decisions/Why Observer Pattern
→ LDS/Decisions/Why Templates not Virtual Functions
→ LDS/Decisions/Why IN_CLOSE_WRITE not IN_CREATE
