# UDP Sockets — The Machine

## The Model
A postal service that throws envelopes over the wall. No handshake, no delivery confirmation, no ordering. Each `sendto()` is a single independent throw. Fast because there is no state to maintain — no connection, no ack, no retransmit. If the envelope lands, great. If not, nobody knows.

## How It Moves

```
Sender:                              Receiver:
─────────                            ────────────
socket(AF_INET, SOCK_DGRAM, 0)       socket(AF_INET, SOCK_DGRAM, 0)
                                     bind(fd, port=9000)

sendto(fd, buf, len, 0,
       &dest_addr, sizeof(dest))  ──→  recvfrom(fd, buf, len, 0, &src_addr, &src_len)
                                        returns: bytes received, src_addr = sender's IP:port

sendto(...)   ──→  [lost]            // gone — nobody knows
sendto(...)   ──→  recvfrom(...)     // arrives out of order — recvfrom returns it anyway
```

**No RecvAll needed:** UDP is message-based. `recvfrom` returns exactly ONE datagram, exactly as sent. If the datagram was 28 bytes, you get 28 bytes — not 14+14. Unlike TCP (stream), UDP is a message queue.

**Why UDP for LDS minion commands:**
- Minion commands are small (< 100 bytes): "write block X"
- Minions are local network (low loss rate)
- LDS implements its own ACK with MSG_ID + timeout + retry
- UDP overhead is ~8 bytes vs TCP's ~20 bytes + connection state per minion

## The Blueprint

```cpp
// Sender:
int fd = socket(AF_INET, SOCK_DGRAM, 0);
sockaddr_in dest = {};
dest.sin_family = AF_INET;
dest.sin_port = htons(9000);
inet_pton(AF_INET, "192.168.1.10", &dest.sin_addr);

sendto(fd, cmd_buf, cmd_len, 0, (sockaddr*)&dest, sizeof(dest));

// Receiver:
int fd = socket(AF_INET, SOCK_DGRAM, 0);
sockaddr_in addr = {};
addr.sin_family = AF_INET;
addr.sin_port = htons(9000);
addr.sin_addr.s_addr = INADDR_ANY;
bind(fd, (sockaddr*)&addr, sizeof(addr));

sockaddr_in src;
socklen_t src_len = sizeof(src);
ssize_t n = recvfrom(fd, buf, sizeof(buf), 0, (sockaddr*)&src, &src_len);
// n = bytes of one complete datagram
// src = who sent it — use for reply
```

**MSG_ID pattern (LDS's reliability layer):**
```
Manager → Minion: {msg_id: 42, type: WRITE, offset: 0, len: 512}
Manager starts timer for msg_id=42

Minion → Manager: {msg_id: 42, status: OK}
Manager cancels timer for msg_id=42

If timer expires: retransmit same msg_id=42
Minion ignores duplicate msg_id=42 (already applied)
```

## Where It Breaks

- **Datagram too large**: UDP datagrams > 65507 bytes are fragmented by IP. Any fragment loss = whole datagram lost. Keep datagrams < 1400 bytes (below Ethernet MTU).
- **Buffer too small for recvfrom**: if your buffer is smaller than the datagram, the excess is silently discarded — no error, just truncation.
- **Port not bound**: `sendto` succeeds even if nobody is listening — UDP doesn't tell you. The sender gets an ICMP "port unreachable" which may appear as `ECONNREFUSED` on the next `recvfrom`.

## In LDS

`services/communication_protocols/nbd/include/IDriverComm.hpp`

The interface's `SendReply` and `RecvRequest` are designed for a request-response protocol. For minion communication, UDP datagrams carry the operation code, MSG_ID, offset, and length. The ResponseManager (Phase 2 LDS component) tracks outstanding MSG_IDs and their timeouts, implementing the reliability layer on top of UDP that TCP would otherwise provide.

## Validate

1. LDS sends a WRITE command to a minion via UDP. The minion is offline. What does `sendto` return? When does LDS discover the failure?
2. LDS receives a UDP datagram with `recvfrom(fd, buf, 64, ...)` but the datagram was 128 bytes. What does `recvfrom` return, and what happened to the other 64 bytes?
3. The minion receives the same WRITE command twice (duplicate due to retry). How does MSG_ID prevent the block from being written twice?

## Connections

**Theory:** [[Core/Theory/Networking/03 - UDP Sockets]]  
**Mental Models:** [[TCP Sockets — The Machine]], [[IPC Overview — The Machine]], [[Serialization — The Machine]]  
**Tradeoffs:** [[Why UDP vs TCP]]  
**LDS Implementation:** [[LDS/Linux Integration/BlockClient]], [[LDS/Decisions/Why UDP not TCP]]  
**Runtime Machines:** [[LDS/Runtime Machines/TCPDriverComm — The Machine]]  
**Glossary:** [[UDP]], [[MSG_ID]], [[Fire and Forget]], [[Exponential Backoff]]
