---
name: UDP — User Datagram Protocol
type: networking
---

# UDP — User Datagram Protocol

**[Wikipedia →](https://en.wikipedia.org/wiki/User_Datagram_Protocol)** | **[RFC 768 →](https://www.rfc-editor.org/rfc/rfc768)**

A connectionless, unreliable transport protocol. Each packet (`sendto`) is independent. No handshake, no guaranteed delivery, no ordering, no congestion control.

## UDP vs TCP in One Line

| | UDP | TCP |
|---|---|---|
| Connection | None (fire and forget) | 3-way handshake required |
| Delivery | Not guaranteed | Guaranteed (or error) |
| Ordering | Not guaranteed | In-order delivery |
| Retransmit | Application's job | Kernel's job |
| Overhead | 8-byte header | 20+ byte header + state |
| Latency | Lower | Higher (ACK wait) |

## Why LDS Uses UDP for Minion Communication

1. **No connection overhead** — no handshake per request, RPi responds immediately
2. **Application-controlled retry** — [[Scheduler]] implements exactly the retry policy we want (exponential backoff, max 3 attempts, fallback to replica)
3. **Local network** — on a LAN, packet loss is rare; the complexity of TCP buys little
4. **Fire-and-forget** — MinionProxy sends and returns immediately; ResponseManager picks up replies asynchronously

→ Full reasoning: [[Why UDP not TCP]]

## The Risk

UDP packets can be lost, duplicated, or reordered. LDS handles this with:
- **MSG_ID** — each packet tagged with a unique 4-byte ID to detect duplicates and match responses
- **Scheduler** — detects lost packets via deadline timeout and retransmits
- **Replica fallback** — if primary times out after retries, ReadCommand falls back to replica minion

## Connections

**Theory:** [[Core/Domains/06 - Networking/Theory/03 - UDP Sockets]]  
**Mental Models:** [[UDP Sockets — The Machine]], [[IPC Overview — The Machine]]  
**Tradeoffs:** [[Why UDP vs TCP]]  
**LDS Implementation:** [[MinionProxy]] — sends UDP packets; [[ResponseManager]] — receives UDP packets; [[Decisions/Why UDP not TCP]]  
**Related Glossary:** [[TCP]], [[MSG_ID]], [[Fire and Forget]], [[Exponential Backoff]]
