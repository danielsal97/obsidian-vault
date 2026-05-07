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

The [[Scheduler]] tracks each pending MSG_ID with a deadline. When the deadline expires without a response from a minion:

```
Retry 1: deadline = now + 1s
Retry 2: deadline = now + 2s
Retry 3: deadline = now + 4s
After 3 retries with no response → error
```

On error:
- **ReadCommand** → try the replica minion (same backoff)
- **WriteCommand** → if at least 1 copy succeeded, report success; otherwise propagate error to NBD (kernel returns `EIO` to user)

## Why Exponential (Not Fixed Interval)?

```
Fixed 1s retry:
  1s, 1s, 1s, 1s, ...
  → floods a struggling minion with constant retries
  → if 50 clients retry at 1s each, 50× load on minion trying to recover

Exponential:
  1s, 2s, 4s → give up
  → gives the minion time to recover
  → load on minion decreases over time
  → total wait time bounded (7s maximum before failover)
```

## Related
- [[Scheduler]] — implements exponential backoff in LDS
- [[ResponseManager]] — the trigger (timeout detection)
- [[RAID01 Manager]] — the fallback (replica minion)
- [[EIO]] — what the user sees on total failure
