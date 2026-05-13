# Networking Overview — The Machine

## The Model
A series of envelopes, each nested inside the next. Your data goes in the innermost envelope. Each layer of the network stack adds its own outer envelope with its own header. At the destination, each layer peels off its envelope and passes the inner payload up. Each layer only reads its own envelope and is blind to the others.

## How It Moves

```
Your data: "READ offset=0 len=512"
      │
      ▼ TCP layer adds:
[TCP header | "READ offset=0 len=512"]
  - source port, dest port
  - sequence number (ensures ordered delivery)
  - checksum
      │
      ▼ IP layer adds:
[IP header | TCP header | data]
  - source IP, dest IP
  - TTL (hop limit)
      │
      ▼ Ethernet layer adds:
[Ethernet header | IP header | TCP header | data]
  - source MAC, dest MAC
  → sent as electrical signals / radio waves
      │
      ▼ At destination, unwrapped in reverse:
"READ offset=0 len=512"
```

**WHY layering:** Each layer is independently replaceable. TCP can run over WiFi, Ethernet, or fiber — it doesn't know which. IP routes over any physical medium. Your application doesn't know if it's on WiFi or Ethernet. This is the same reason LDS uses `IDriverComm` — the interface hides the transport.

## The Blueprint

**The four layers that matter:**
| Layer | Protocol | Your code touches |
|---|---|---|
| Application | HTTP, NBD, your protocol | Yes — you design this |
| Transport | TCP, UDP | Yes — `socket()`, `connect()`, `send()` |
| Network | IP | OS handles it |
| Link | Ethernet, WiFi | OS + driver handles it |

**TCP vs UDP:**
| | TCP | UDP |
|---|---|---|
| Connection | Handshake required | None |
| Delivery | Guaranteed, ordered | Best effort, unordered |
| Speed | Slower (acks, retransmits) | Faster (fire and forget) |
| LDS use | TCP server for clients | UDP for minion commands |

## Where It Breaks

- **MTU fragmentation**: if your packet exceeds the Maximum Transmission Unit (~1500 bytes on Ethernet), IP fragments it. TCP handles this transparently; UDP fragments silently and the receiver must reassemble.
- **Firewall drops**: UDP packets are often blocked by firewalls; TCP is usually allowed.
- **NAT**: source IP is rewritten by the router — the destination sees the NAT's IP, not yours.

## In LDS

`services/communication_protocols/tcp/src/TCPDriverComm.cpp` — TCP for client connections.
`services/communication_protocols/nbd/src/NBDDriverComm.cpp` — direct kernel interface (not a network socket — `/dev/nbd0` is a block device, but the NBD protocol is designed for network use).

LDS uses TCP for the client-facing interface because clients need reliable, ordered delivery of block data. A single bit flip in a 512-byte block read is catastrophic — TCP's checksum and retransmit prevent this. UDP would require LDS to implement its own reliability layer for data blocks.

## Validate

1. A client sends a 1MB read request via TCP. IP fragments it into multiple packets. Does TCP need to reassemble them in order? Who actually does the reassembly?
2. LDS uses UDP for minion commands (not data blocks). Why is UDP acceptable for "hey, write this block" but not for the block data itself?
3. The LDS client connects to `127.0.0.1:7800`. The packet travels through the Ethernet layer? No — why?

## Connections

**Theory:** [[Core/Domains/06 - Networking/Theory/01 - Overview]]  
**Mental Models:** [[TCP Sockets — The Machine]], [[UDP Sockets — The Machine]], [[IPC Overview — The Machine]], [[File Descriptors — The Machine]]  
**Tradeoffs:** [[Why UDP vs TCP]]  
**LDS Implementation:** [[LDS/Linux Integration/TCPServer]] — TCP for clients; [[LDS/Linux Integration/NBDDriverComm]] — kernel block device interface  
**Runtime Machines:** [[LDS/Runtime Machines/TCPDriverComm — The Machine]], [[LDS/Runtime Machines/NBDDriverComm — The Machine]]  
**Glossary:** [[TCP]], [[UDP]]
