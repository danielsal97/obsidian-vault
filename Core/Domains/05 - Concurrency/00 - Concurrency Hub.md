# Concurrency — Hub

Shared state, ordering guarantees, and the primitives that make parallel code safe.

## Place in Runtime

```
thread spawn → clone() → scheduler → mutex/futex → acquire/release → worker executes
```

→ [[Concurrency Runtime — The Machine]] — full thread lifecycle (start here)
→ [[00 - VAULT MAP]] — vault root
→ [[Core/00 START HERE|Core Start Here]]

## The Machine

→ [[01 - Multithreading Patterns — The Machine]] — thread pool WPQ, work stealing, idle/wake cycle
→ [[02 - Memory Ordering — The Machine]] — when a write on thread A is visible on thread B
→ [[04 - Atomics — The Machine]] — LOCK prefix, MESI exclusive ownership, ~5ns vs 300ns contended
→ [[03 - False Sharing — The Machine]] — two atomics on the same cache line thrash the bus
→ [[06 - Semaphores — The Machine]] — counting semaphore blocks/wakes threads

## Theory

→ [[01 - Multithreading Patterns]] — thread pool, producer/consumer WPQ, futures
→ [[02 - Memory Ordering]] — happens-before, acquire/release, CAS, memory barriers

## Interview Q&A

→ [[01 - Concurrency Q&A]] — mutex, race conditions, deadlock, condition variables, atomic, memory ordering

## Glossary

→ [[10 - WPQ]] · [[17 - pthreads]]
