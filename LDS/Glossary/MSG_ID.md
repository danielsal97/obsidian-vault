---
name: MSG_ID — Message Identifier
type: protocol
---

# MSG_ID — Message Identifier

A 4-byte unsigned integer assigned to every outgoing UDP request by [[MinionProxy]]. It is echoed back verbatim by the minion in its reply, allowing [[ResponseManager]] to match asynchronous responses to the correct waiting command.

## Why It's Needed

UDP is connectionless — there is no persistent channel between master and minion. Multiple commands may be in-flight simultaneously (one worker sends to Minion A while another sends to Minion B). Without MSG_ID, when a UDP response arrives, there is no way to know which request it answers.

```
Without MSG_ID:
  Worker 1 sends PUT to Minion A  ─┐
  Worker 2 sends PUT to Minion B  ─┤  response arrives... which one?
  Worker 3 sends GET from Minion A─┘  impossible to tell

With MSG_ID:
  Worker 1 sends PUT, msg_id=101  →  Minion A replies msg_id=101
  Worker 2 sends PUT, msg_id=102  →  Minion B replies msg_id=102
  Worker 3 sends GET, msg_id=103  →  Minion A replies msg_id=103
  ResponseManager looks up 101/102/103 → calls correct callback
```

## Wire Position

```
Master → Minion:
[ MSG_ID: 4B ][ OP: 1B ][ OFFSET: 8B ][ LEN: 4B ][ DATA: variable ]
   ↑ first field

Minion → Master:
[ MSG_ID: 4B ][ STATUS: 1B ][ LEN: 4B ][ RESERVED: 4B ][ DATA: variable ]
   ↑ echoed back unchanged
```

## Lifecycle

```
MinionProxy::SendPutBlock()
  → generate unique msg_id (atomic counter)
  → serialize into packet
  → sendto(udp_fd, packet)
  → ResponseManager.RegisterCallback(msg_id, callback)
  → Scheduler.Track(msg_id, deadline)
  → return msg_id to caller

ResponseManager receiver thread
  → recvfrom() arrives
  → parse msg_id from first 4 bytes
  → look up callback map
  → call callback(status, data)
  → Scheduler.OnResponse(msg_id)
```

## Related
- [[Wire Protocol Spec]] — full packet format
- [[MinionProxy]] — generates MSG_IDs and sends packets
- [[ResponseManager]] — receives and matches by MSG_ID
- [[Scheduler]] — tracks MSG_IDs for timeout detection
