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
  wait...
  wait...        ← worker thread blocked during entire network round-trip
  wait...
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

A WRITE command sends to **two** minions (RAID01 mirroring). If it blocked on the first send, the second send would be delayed by the full network round-trip of the first. With fire-and-forget:

```
t=0ms   SendPutBlock(minionA)  → packet in flight
t=0ms   SendPutBlock(minionB)  → packet in flight  (parallel!)
t=1ms   ACK from minionA arrives → callback
t=1ms   ACK from minionB arrives → callback
t=1ms   both done → SendReply to kernel
```

vs. sequential blocking:
```
t=0ms   send to minionA
t=1ms   ACK from minionA
t=1ms   send to minionB
t=2ms   ACK from minionB
t=2ms   done     ← twice as slow
```

## Components Involved

- [[MinionProxy]] — the sender (fire-and-forget)
- [[ResponseManager]] — the asynchronous receiver
- [[Scheduler]] — detects if the "forget" went too far (timeout)
- [[MSG_ID]] — the correlation key between sent packet and async response

## Related
- [[UDP]] — the transport that makes fire-and-forget natural
- [[Concurrency Model]] — how threads are arranged around this pattern
