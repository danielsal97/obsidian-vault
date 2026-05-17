# Why UDP vs TCP

## Context
You are sending messages between processes or machines and must choose a transport protocol.

## The Core Tradeoff

| | TCP | UDP |
|---|---|---|
| Delivery guarantee | Yes — retransmits lost packets | No — fire and forget |
| Ordering | Yes — in-order delivery | No — may arrive out of order |
| Connection | Yes — handshake, state | No — stateless |
| Head-of-line blocking | Yes — later packets wait for dropped one | No — each packet independent |
| Overhead | Higher — ACK, congestion control | Lower — no overhead |

## When to choose TCP

- You need guaranteed delivery and order
- The connection is long-lived (client ↔ server session)
- You cannot tolerate message loss
- You can afford the head-of-line blocking cost

## When to choose UDP

- You implement your own reliability (retry, ACK, MSG_ID tracking)
- Messages are independent — a retry of msg #5 doesn't need to wait for msg #4
- You need lower latency and head-of-line blocking would hurt you
- You are sending to multiple destinations (broadcast, multicast)

## The "implement your own reliability" pattern

UDP + application-layer reliability = you get exactly the guarantees you need and no more.
Example: fire-and-forget PUT with MSG_ID → ResponseManager matches ACK → Scheduler retries on deadline.
This avoids TCP's head-of-line blocking when one minion is slow.

## See also
→ [[02 - Sockets TCP]] — TCP API and theory
→ [[03 - UDP Sockets]] — UDP API and theory
→ LDS/Decisions/Why UDP not TCP — how LDS applies this for minion communication
→ LDS/Decisions/Why TCP for Client — why LDS uses TCP for the Mac client link
