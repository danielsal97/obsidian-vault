# Client-Server Architecture — Mac Client ↔ Linux Master

**Added:** Phase 2A | **Status:** Design (implementation pending)

---

## Overview

Phase 2A adds a real network layer between two physical machines. A Mac client communicates with the Linux master over TCP to read and write storage blocks. The Linux master exposes both its existing NBD interface (to the kernel) and a new TCP interface (to network clients) — handled by the same Reactor event loop.

```
┌──────────────────────────────────────────────────────────────────┐
│  Mac (Client)                                                    │
│                                                                  │
│  ./ldsclient 192.168.1.5 7800 write 0 hello.txt                  │
│         │                                                        │
│  ┌──────────────┐                                                │
│  │  BlockClient  │  Connect / Read / Write                       │
│  └──────┬───────┘                                                │
│         │ TCP socket                                             │
└─────────┼────────────────────────────────────────────────────────┘
          │  Ethernet / Wi-Fi
          │ (real network, real IP)
┌─────────┼────────────────────────────────────────────────────────┐
│  Linux (Master)                                                  │
│         │                                                        │
│  ┌──────▼────────┐      ┌──────────────┐                        │
│  │  TCPServer    │─────▶│ LocalStorage │                        │
│  │  port 7800    │      └──────────────┘                        │
│  └───────────────┘                                               │
│         │                                                        │
│  ┌──────────────────────────────────────┐                       │
│  │  Reactor (epoll)                     │                       │
│  │  ├── NBD fd  → InputMediator         │                       │
│  │  ├── TCP listen fd → TCPServer       │                       │
│  │  └── TCP client fd → TCPServer       │                       │
│  └──────────────────────────────────────┘                       │
│                                                                  │
│  (NBD fd still works — kernel mounts /dev/nbd0 as before)       │
└──────────────────────────────────────────────────────────────────┘
```

---

## TCP vs NBD — Two Parallel Interfaces

TCP does **not** replace NBD and does **not** go through NBD. They are two independent input paths into the same LocalStorage:

```
Linux kernel (/dev/nbd0)
      │ socketpair
      ▼
NBDDriverComm → InputMediator ──→ LocalStorage
                                       ▲
TCPServer ─────────────────────────────┘
      ▲
Mac (BlockClient / Python script)
```

- **NBD** — for the Linux kernel. Mounts `/dev/nbd0` as a real block device (`mkfs`, `mount`, `cp`).
- **TCP** — for remote clients (Mac). Sends read/write requests over the network.

Same storage, two independent front doors.

---

## Network Setup — Tailscale

Both machines use Tailscale. Each machine gets a stable `100.x.x.x` IP that works from anywhere, no same-LAN requirement.

Get the Linux machine's Tailscale IP:
```bash
tailscale ip
```

The Mac client connects to that IP on port 7800. No router config, no firewall rules, no IP changes when switching networks.

---

## Connection Model

End-to-end. No middleman, no broker, no relay.

```
Mac  ←——— one persistent TCP connection ———→  Linux
```

The Mac opens one connection, keeps it open for the whole session, sends requests one at a time, gets replies. When done, closes the connection.

---

## Client Language

The client can be written in any language — the protocol is just bytes over TCP.

- **C++ BlockClient** — for CV, production use
- **Python script** — faster to test, good for demos and interviews

Both speak the same wire format.

---

## Why the Reactor Handles TCP Clients

The Reactor already watches file descriptors with epoll. A TCP client socket is just another file descriptor. By registering each client socket with the Reactor, we get:

- **No second thread** — the same epoll loop handles NBD and TCP with zero additional threads
- **Consistent event model** — all I/O goes through one dispatch point
- **Natural backpressure** — if a client stops reading, the Reactor simply stops firing for that fd

This required upgrading the Reactor from a single global handler to a per-fd handler map.

---

## The Reactor Upgrade

```
Before:  Add(fd)  +  SetHandler(fn)  →  fn called for every fd, no distinction
After:   Add(fd, fn)                 →  fn stored per fd, called only for that fd
```

Internally: `std::unordered_map<int, std::function<void(int)>> m_handlers`

When `TCPServer::OnAccept()` runs, it calls `reactor.Add(client_fd, handler)` — adding the new connection dynamically without any restart or reconfiguration.

---

## TCP Wire Protocol

TCP is a byte stream, not a packet protocol. A single `send()` on the sender may arrive as multiple `recv()` calls on the receiver. The fix: always send a fixed-size header first, then exactly `header.length` bytes. The receiver reads in two steps and never assumes it gets everything in one call.

### Client → Server: Request

```
Offset  Size   Field    Notes
──────  ────   ──────   ──────────────────────────────
0       1B     type     0x00=READ, 0x01=WRITE
1       8B     offset   byte offset into storage (big-endian)
9       4B     length   number of bytes (big-endian)
13      ?B     data     present only for WRITE, exactly `length` bytes
```

**Total header size:** 13 bytes (fixed, always sent first)

### Server → Client: Response

```
Offset  Size   Field    Notes
──────  ────   ──────   ──────────────────────────────
0       1B     status   0x00=OK, 0x01=ERROR
1       4B     length   byte count of following data (big-endian)
5       ?B     data     present only for READ response, exactly `length` bytes
```

**Total header size:** 5 bytes (fixed, always sent first)

### Why Big-Endian

Multi-byte integers are sent in network byte order (big-endian). Mac (ARM64) and Linux (x86-64) are both little-endian natively, so both sides must convert:

- **Send:** `htobe64(offset)`, `htonl(length)`
- **Receive:** `be64toh(offset)`, `ntohl(length)`

This is standard practice. Without it, a 4-byte integer `0x00001000` on the sender arrives as `0x10000000` on the receiver — a 268 MB offset instead of 4 KB.

---

## Connection Lifecycle

```
Mac                                     Linux

Connect(ip, 7800)  ─── TCP SYN ──────▶ accept() → add client_fd to Reactor
                   ◀── SYN+ACK ────────

Write(0, data)     ─── [Request hdr]──▶ OnClientData(fd)
                   ─── [data bytes] ──▶   RecvAll(hdr) → RecvAll(data)
                                           storage.Write(...)
                   ◀── [Response hdr] ─   SendAll(response)

Read(0, 16)        ─── [Request hdr]──▶ OnClientData(fd)
                                           RecvAll(hdr)
                                           storage.Read(...)
                   ◀── [Response hdr] ─   SendAll(response_hdr + data)
                   ◀── [data bytes] ────

Disconnect()       ─── TCP FIN ───────▶ recv() returns 0
                                         reactor.Remove(client_fd)
                                         close(client_fd)
```

---

## Shared Files

`services/network/include/NetworkProtocol.hpp` is included by **both** the Linux server and the Mac client. It defines the structs and constants that both sides agree on. Changing this file is a protocol breaking change — both sides must be updated together.

---

## What This Covers (CV Story)

| Subject | Concrete |
|---|---|
| Network programming | TCP `socket/bind/listen/accept/connect/send/recv` |
| Protocol design | Custom binary wire format, length-prefix framing, byte ordering |
| Cross-platform | Mac (ARM64) client ↔ Linux (x86-64) server |
| Reactor pattern | Dynamic fd registration, per-fd dispatch |
| Client-server architecture | Clean separation of transport, storage, and application layers |
| Existing: Linux syscalls | epoll, inotify, NBD ioctl, signalfd |
| Existing: Design patterns | Observer, Factory, Singleton, Command, Reactor |

---

## Related Notes

- [[Components/TCPServer]]
- [[Components/BlockClient]]
- [[Decisions/Why TCP for Client]]
- [[Phase 2A - Mac Client TCP Bridge]]
- [[Wire Protocol Spec]] (UDP protocol for master ↔ minion — different from this TCP protocol)
- [[Reactor]]
