---
name: Exponential Backoff
type: algorithm
---

# Exponential Backoff

**[Wikipedia →](https://en.wikipedia.org/wiki/Exponential_backoff)**

A retry strategy where each successive retry waits twice as long as the previous one, up to a maximum retry count. Prevents hammering a temporarily unavailable resource.

## Pattern

```
Attempt 1 → fails → wait 1s
Attempt 2 → fails → wait 2s
Attempt 3 → fails → wait 4s
Attempt 4 → give up → propagate error
```

General formula: `wait = base_delay × 2^(attempt - 1)`

## In LDS — Scheduler

The [[Scheduler]] tracks each pending MSG_ID with a deadline. When the deadline expires without a response:

```
Retry 1: deadline = now + 1s
Retry 2: deadline = now + 2s
Retry 3: deadline = now + 4s
After 3 retries with no response → error (EIO)
```

On error:
- **ReadCommand** → try the replica minion (same backoff)
- **WriteCommand** → if at least 1 copy succeeded, report success; otherwise propagate EIO

## Why Exponential (Not Fixed Interval)?

Fixed 1s retry floods a struggling minion with constant retries. Exponential gives the minion time to recover while bounding total wait time (7s maximum before failover).

## Connections

**Mental Models:** [[Threads and pthreads — The Machine]], [[UDP Sockets — The Machine]]  
**LDS Implementation:** [[Scheduler]] — implements exponential backoff; [[ResponseManager]] — timeout trigger; [[RAID01 Manager]] — replica fallback  
**Related Glossary:** [[MSG_ID]], [[EIO]], [[Fire and Forget]]
