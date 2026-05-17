---
name: TCP — Transmission Control Protocol
type: networking
---

# TCP — Transmission Control Protocol

**[Wikipedia →](https://en.wikipedia.org/wiki/Transmission_Control_Protocol)** | **[RFC 793 →](https://www.rfc-editor.org/rfc/rfc793)**

A connection-oriented, reliable transport protocol. Guarantees that all bytes arrive, arrive in order, and are not duplicated. The kernel's TCP stack handles retransmission, flow control, and congestion avoidance automatically.

## Why LDS Does NOT Use TCP for Minions

| Concern | TCP behaviour | Problem for LDS |
|---------|---------------|-----------------|
| Timeout | Fixed kernel retransmit (exponential, up to ~2 min) | We need fast failover to replica — can't wait 2 min |
| Retry logic | Opaque — app can't control retransmit count/interval | We need custom backoff and a clear "give up" point |
| Connection state | Per-minion TCP connection with kernel state machine | Overhead per minion; connection teardown on failure |
| Head-of-line blocking | Packets on same connection are ordered | One slow minion blocks unrelated requests on that connection |

LDS implements its own lightweight retry/failover on top of UDP ([[Scheduler]]), which gives precise control over timeouts and replica fallback — something TCP doesn't expose to userspace.

## Where TCP Is Appropriate

TCP is the right choice when:
- You need byte-stream ordering (HTTP, SSH, databases)
- You don't want to write retry logic yourself
- Latency tolerance is high (WAN links, user-facing services)

## Connections

**Theory:** [[02 - Sockets TCP]]  
**Mental Models:** [[TCP Sockets — The Machine]], [[IPC Overview — The Machine]], [[File Descriptors — The Machine]]  
**Tradeoffs:** [[Why UDP vs TCP]]  
**LDS Implementation:** [[LDS/Linux Integration/TCPServer]] — LDS TCP server; [[Decisions/Why TCP for Client]] — why client uses TCP  
**Runtime Machines:** [[TCPDriverComm — The Machine]]  
**Related Glossary:** [[UDP]], [[socketpair]]
