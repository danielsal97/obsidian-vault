---
name: Fire-and-Forget
type: pattern
---

# Fire-and-Forget

A sending pattern where the sender dispatches a request and returns immediately — without waiting for a response. The response is handled separately, asynchronously.

## Contrast with Request-Response (Blocking)

```
Blocking (request-response):
  send(packet)
  wait...        ← worker thread blocked during entire network round-trip
  response = recv()
  continue

Fire-and-forget:
  msg_id = send(packet)    ← returns immediately
  register callback(msg_id, handler)
  continue doing other work...

  [later, on ResponseManager thread]
  recv() arrives → lookup msg_id → call handler()
```

## Why LDS Uses Fire-and-Forget

A WRITE command sends to **two** minions (RAID01 mirroring). With fire-and-forget, both sends happen in parallel:

```
t=0ms   SendPutBlock(minionA)  → packet in flight
t=0ms   SendPutBlock(minionB)  → packet in flight  (parallel!)
t=1ms   ACK from minionA arrives → callback
t=1ms   ACK from minionB arrives → callback
t=1ms   both done → 2× faster than sequential blocking
```

## Connections

**Mental Models:** [[UDP Sockets — The Machine]], [[TCP Sockets — The Machine]], [[Multithreading Patterns — The Machine]]  
**Tradeoffs:** [[Why UDP vs TCP]]  
**LDS Implementation:** [[MinionProxy]] — the sender; [[ResponseManager]] — async receiver; [[Scheduler]] — timeout detection  
**Related Glossary:** [[MSG_ID]], [[UDP]], [[Exponential Backoff]]
