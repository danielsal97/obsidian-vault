# Why ThreadPool over inline execution

## Context
You receive work items (commands, requests) on a hot path (event loop, main thread).
You must choose where to execute them.

## Options

**Inline execution** — run the work directly on the thread that received it.
**ThreadPool** — push work to a queue, worker threads pick it up.

## The Problem with Inline Execution

If the main thread (e.g., the Reactor's epoll loop) runs the work directly:
- A 200ms storage operation blocks the loop for 200ms
- No other fd is serviced during that time
- New connections cannot be accepted
- Signal handling is delayed — SIGTERM may not be processed
- The system's throughput is bounded by the slowest single operation

## Why ThreadPool

- The hot path (event loop, network receive) stays non-blocking and fast
- Work executes concurrently across N worker threads
- Priority queuing (WPQ) gives you control over execution order
- The hot path is never stalled waiting for slow work

## The Pattern

```
Event arrives on epoll → handler reads data (non-blocking) → creates Command → pushes to WPQ → returns immediately
Worker thread (blocking on WPQ) → pops Command → executes (may block) → sends reply
```

The two responsibilities are separated: *routing* (fast, hot path) and *execution* (potentially slow, off-path).

## When inline is correct

- The work is guaranteed fast (< 1ms, no I/O, no syscalls)
- You have only one source of work (no multiplexed event loop)
- Concurrency would introduce ordering bugs worse than the latency cost

## See also
→ [[../../05 - Concurrency/Theory/01 - Multithreading Patterns]] — thread pool theory
→ [[../../05 - Concurrency/Mental Models/01 - Multithreading Patterns — The Machine]]
→ LDS/Infrastructure/ThreadPool — LDS's ThreadPool + WPQ implementation
→ LDS/Runtime Machines/ThreadPool and WPQ — The Machine
