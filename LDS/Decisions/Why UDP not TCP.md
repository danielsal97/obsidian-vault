# Decision: Why UDP (not TCP) for Master-Minion Communication

## Decision

Use **UDP** for all master ↔ minion communication.

---

## Reasoning

### TCP Problems in This Context

| Problem | Detail |
|---|---|
| Connection overhead | Each minion needs a persistent TCP connection — 10 minions = 10 connections to manage |
| Head-of-line blocking | A slow minion blocks all requests on that connection |
| Retransmission is too smart | TCP retries forever internally; LDS needs to control retry logic itself (fail fast, try replica) |
| Latency | SYN/ACK handshake adds latency for short messages |

### UDP Advantages for LDS

| Advantage | Detail |
|---|---|
| Stateless | No per-minion connection state to maintain |
| Fire-and-forget | MinionProxy sends and returns immediately; ResponseManager handles the reply |
| LDS controls retry | Scheduler does exponential backoff — exactly what LDS needs |
| Multicast support | One UDP send can reach multiple minions for replication |
| Low latency | No connection setup, kernel handles at L4 |

---

## The Trade-off

UDP is unreliable — packets can be lost or reordered. LDS explicitly handles this:

```
MinionProxy sends → Scheduler tracks deadline
                 → ResponseManager waits for reply
                 → On timeout: Scheduler triggers retry (up to 3x)
                 → After max retries: failover to replica
```

This gives LDS **more control** than TCP's automatic retry, which is exactly right for a storage system where "fail fast and use the replica" is better than "keep retrying the same dead minion for 30 seconds."

---

## When TCP Would Be Better

If LDS needed ordered streams (e.g. streaming large sequential transfers), TCP would be better. For random-access block storage with small fixed-size messages (4KB blocks), UDP is the right tool.

---

## Related Notes
- [[MinionProxy]]
- [[Scheduler]]
- [[ResponseManager]]
