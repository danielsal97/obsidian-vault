# Request Lifecycle — The Machine

## The Model

A write request enters LDS as raw bytes from the kernel's NBD driver. By the time it exits, it has been decoded, validated, split across two minionservers via UDP, and confirmed — or retried — via a deadline-monitored response window. Every stage is asynchronous: no thread sits blocked waiting; work is queued, events wake the right component at the right time.

This note is the full-stack view of a single write request through LDS.

## How It Moves

```
[1] NBD kernel driver writes to /dev/nbd0 (e.g. filesystem writes a block)
      │  socketpair fd becomes readable
      ▼
[2] Reactor (epoll_wait returns on NBD fd)
  → calls NBDDriverComm::onReadable()
  → reads NBD request header (28 bytes)
  → decodes: magic + type=WRITE + handle + offset + length
      │
      ▼
[3] InputMediator (Observer dispatch)
  → NBDDriverComm fires event: "write request received"
  → InputMediator creates WriteCommand(handle, offset, length, data)
  → posts WriteCommand to ThreadPool WPQ
      │
      ▼
[4] Worker thread dequeues WriteCommand::execute()
  → RAID01Manager::write(block_number, data):
      → maps block_number → two minionserver IDs (striping)
      → for each minion:
          → MinionProxy::send(msg_id, minion_addr, write_packet)
          → sends UDP datagram (fire and forget)
          → registers (msg_id, deadline, retry_callback) with Scheduler
      │
      ▼
[5] Reactor (epoll_wait returns on UDP response socket)
  → reads UDP response from minionserver
  → ResponseManager::onResponse(msg_id, status)
  → marks msg_id complete, cancels deadline in Scheduler
  → when BOTH minions respond: WriteCommand is complete
      │
      ▼
[6] NBDDriverComm::sendReply(handle, status=0)
  → writes 16-byte NBD reply to socketpair
  → kernel unblocks the filesystem write that was waiting
```

## What Fails and How It's Handled

**Minion doesn't respond before deadline:**
- Scheduler fires retry callback
- MinionProxy resends the UDP packet
- Up to N retries before marking the write as failed

**Minion is unhealthy (watchdog):**
- Watchdog tracks last-seen timestamp per minion
- If minion goes silent, Watchdog fires "minion down" event
- RAID01Manager re-maps writes to healthy minionservers

**Response arrives for unknown msg_id:**
- ResponseManager ignores it (stale retry acknowledgment)

## Threads Involved

| Thread | Blocked on | Woken by |
|---|---|---|
| Reactor | epoll_wait | NBD fd or UDP socket becomes readable |
| Worker 0..N | sem_wait (WPQ) | Reactor posts work item |
| Scheduler | sleep/timer | Deadline expires |

The Reactor thread NEVER blocks on I/O (always non-blocking reads). It never executes work directly — it only dispatches to the thread pool. This is the core of the Reactor pattern.

## Links

→ LDS/Flows/01 - Write Request — End to End — full LDS-specific walk-through
→ LDS/Runtime Machines/02 - Request Lifecycle — The Machine — LDS detail
→ [[../Domains/07 - Design Patterns/Theory/01 - Reactor]] — Reactor pattern
→ [[../Domains/07 - Design Patterns/Mental Models/01 - Reactor Pattern — The Machine]]
→ [[Concurrency Runtime — The Machine]] — thread pool internals
→ [[Networking Stack — The Machine]] — epoll and UDP receive path
