# Networking

A bottom-up journey from physical wire to your application code. Each layer builds on the one below it.

---

## Layer 1 — Physical

Bits on a wire (or air). Electrical signals, light pulses, radio waves. The NIC (network interface card) converts digital bits to/from the physical medium.

You never interact with this layer in software. It's handled entirely by hardware.

---

## Layer 2 — Data Link (Ethernet / WiFi)

Moves **frames** between two directly connected devices on the same local network.

```
Ethernet Frame:
[Dst MAC: 6B][Src MAC: 6B][EtherType: 2B][Payload: 46–1500B][CRC: 4B]
```

**MAC address** — hardware address burned into the NIC (e.g. `aa:bb:cc:dd:ee:ff`). Unique per device on the local network. Used for delivery within a single network segment.

**ARP** — maps IP → MAC. Before sending to `192.168.1.5`, your machine broadcasts "who has 192.168.1.5?" and the owner replies with its MAC address.

**Switch** — a Layer 2 device. Learns which MAC is on which port and forwards frames only to the right port.

MTU (Maximum Transmission Unit) for Ethernet: **1500 bytes**. Anything larger must be fragmented.

---

## Layer 3 — Network (IP)

Moves **packets** across networks, routing hop-by-hop from source to destination.

```
IPv4 Packet Header (20 bytes minimum):
[Version][IHL][DSCP/ECN][Total Length]
[Identification][Flags][Fragment Offset]
[TTL][Protocol][Header Checksum]
[Source IP: 4B]
[Destination IP: 4B]
[Options (variable)]
[Payload]
```

Key fields:
- **TTL** (Time To Live) — decremented at each router. Reaches 0 → packet dropped (prevents infinite loops).
- **Protocol** — what's inside: 6=TCP, 17=UDP, 1=ICMP.
- **Fragmentation** — if packet > MTU of a link, IP fragments it. Any fragment lost = whole datagram lost.

**Router** — a Layer 3 device. Reads the destination IP, consults its routing table, forwards toward the next hop.

**ICMP** — control messages. `ping` uses ICMP Echo Request/Reply. `traceroute` uses ICMP TTL Exceeded.

### IP Addresses

```
IPv4: 32-bit, dotted decimal — 192.168.1.100
IPv6: 128-bit, hex colon    — fe80::1

Special:
  127.0.0.1        loopback (same machine)
  0.0.0.0          any interface (bind)
  255.255.255.255  broadcast

Private (not internet-routable):
  10.0.0.0/8
  172.16.0.0/12
  192.168.0.0/16

Tailscale assigns stable 100.x.x.x addresses — reachable from anywhere via VPN tunnel.
```

### Byte Ordering — Endianness

Network byte order is **big-endian** (most significant byte first). x86/x86_64 CPUs are little-endian. Always convert when writing integers to packets.

```c
#include <arpa/inet.h>

// Host to Network:
uint16_t htons(uint16_t);   // 16-bit — for port numbers
uint32_t htonl(uint32_t);   // 32-bit
uint64_t htobe64(uint64_t); // 64-bit (Linux)

// Network to Host:
uint16_t ntohs(uint16_t);
uint32_t ntohl(uint32_t);
uint64_t be64toh(uint64_t);

// Wire encoding:
struct Header {
    uint32_t msg_id;
    uint64_t offset;
    uint32_t length;
} __attribute__((packed));

hdr.msg_id = htonl(42);
hdr.offset = htobe64(1024);
// ... send ...
uint32_t id  = ntohl(hdr.msg_id);
uint64_t off = be64toh(hdr.offset);
```

See [[../C/Serialization]] — full wire protocol design.

---

## Layer 4 — Transport (TCP / UDP)

Adds **ports** — multiple services on the same IP. Identifies which process gets the data.

A connection is uniquely identified by: `(protocol, src_ip, src_port, dst_ip, dst_port)`.

```
Port ranges:
  0–1023    Well-known (root required): HTTP=80, HTTPS=443, SSH=22, DNS=53
  1024–49151 Registered: MySQL=3306, Redis=6379
  49152–65535 Ephemeral — OS assigns to clients automatically
```

---

### TCP — Transmission Control Protocol

Reliable, ordered, stream-based. Built on top of IP.

```
3-Way Handshake (connect):
  Client ──SYN──────────▶ Server
  Client ◀──SYN+ACK────── Server
  Client ──ACK──────────▶ Server
  [connection established]

4-Way Close:
  Client ──FIN──────────▶ Server
  Client ◀──ACK─────────  Server
  Client ◀──FIN─────────  Server
  Client ──ACK──────────▶ Server
```

Key guarantees:
- **Reliable** — retransmits lost segments (via ACKs + timeout)
- **Ordered** — data arrives in send order (sequence numbers)
- **Flow control** — receiver advertises how much buffer it has (window size)
- **Congestion control** — detects network congestion, slows down

**Stream — no message boundaries.** TCP is a byte pipe. One `send(100)` may arrive as two `recv(50)` calls. You must frame your own messages.

```c
// Always RecvAll — loop until you have all expected bytes:
ssize_t RecvAll(int fd, void* buf, size_t len) {
    size_t received = 0;
    while (received < len) {
        ssize_t n = recv(fd, (char*)buf + received, len - received, 0);
        if (n <= 0) return n;   // 0 = peer closed, -1 = error
        received += n;
    }
    return received;
}
```

Full TCP socket API → [[Sockets TCP]]

---

### UDP — User Datagram Protocol

Connectionless, unreliable, message-preserving. No handshake, no ACK.

- **Message boundaries preserved** — one `sendto` = one `recvfrom`
- **No retransmit** — lost packets gone forever
- **Low overhead** — 8-byte header vs TCP's 20+
- **Use cases** — DNS, video/audio streaming, game state, LDS master↔minion

Max safe payload: **1472 bytes** (1500 MTU − 20 IP header − 8 UDP header). Larger datagrams are fragmented at IP layer — any fragment lost = whole datagram lost.

Full UDP socket API → [[UDP Sockets]]

---

## Layer 5/6 — Session / Presentation (TLS)

In TCP/IP, these are mostly handled by **TLS** (Transport Layer Security).

TLS sits between TCP and the application. After the TCP handshake, a TLS handshake runs:

```
TCP connect
  ── ClientHello (TLS version, supported ciphers)
  ◀─ ServerHello + Certificate
  ── (verify cert against trusted CAs)
  ── Key exchange (ECDH — both sides derive same session key)
  ── Finished
  [all data now encrypted + authenticated]
```

- **Asymmetric crypto** (RSA/ECDH) — used during handshake to exchange keys
- **Symmetric crypto** (AES-GCM) — used for all data after handshake (fast)
- **MAC** — every record has a tag ensuring it wasn't tampered with

HTTPS = HTTP over TLS.

---

## Layer 7 — Application

Your protocol. Examples:

### DNS

Translates hostnames to IPs. UDP port 53 (small queries), TCP for large responses.

```
Resolution order:
  1. /etc/hosts (local override)
  2. Local DNS cache
  3. Query DNS server (e.g. 8.8.8.8)
     → root nameserver → .com TLD → authoritative nameserver
  4. Returns IP, cached with TTL

In C:
struct addrinfo hints = {.ai_family = AF_INET, .ai_socktype = SOCK_STREAM};
struct addrinfo* res;
getaddrinfo("example.com", "80", &hints, &res);
// res->ai_addr is ready to pass to connect()
freeaddrinfo(res);
```

### HTTP/1.1

Text-based request/response over TCP.

```
Request:
GET /path HTTP/1.1\r\n
Host: example.com\r\n
\r\n

Response:
HTTP/1.1 200 OK\r\n
Content-Length: 42\r\n
\r\n
<body>
```

Status codes: `2xx` success, `3xx` redirect, `4xx` client error, `5xx` server error.  
HTTP/2: binary framing, multiplexed streams, header compression — all over one TCP connection.

### Custom Binary Protocol

What LDS uses for master↔minion UDP and (planned) TCP client:

```
Request:  [MSG_ID: 4B][OP: 1B][OFFSET: 8B][LEN: 4B][DATA: var]
Response: [MSG_ID: 4B][STATUS: 1B][LEN: 4B][DATA: var]
```

MSG_ID lets `ResponseManager` match replies to pending requests even out-of-order.

See [[../C/Serialization]] for how to build and parse binary wire protocols.

---

## Multiplexing — Many Connections, One Thread

Without multiplexing: one thread per connection, blocks on `recv`. Doesn't scale.

With `epoll`: one thread watches thousands of fds, wakes only when data arrives.

```
epoll_create → epoll_ctl (register fds) → epoll_wait (blocks)
→ returns list of ready fds → dispatch to handlers
```

Full epoll API and Reactor pattern → [[epoll]]

---

## Socket API — Full Lifecycle

```c
// TCP server:
socket(AF_INET, SOCK_STREAM, 0)
setsockopt(SO_REUSEADDR)           // avoid "address already in use" on restart
bind(addr)
listen(backlog)
accept()                           // returns new fd per client
recv() / send()                    // on the per-client fd
close()

// TCP client:
socket(AF_INET, SOCK_STREAM, 0)
connect(server_addr)
send() / recv()
close()

// UDP:
socket(AF_INET, SOCK_DGRAM, 0)
bind() (server)                    // optional for client
sendto() / recvfrom()
close()
```

Useful socket options:
```c
SO_REUSEADDR   // reuse port in TIME_WAIT
SO_KEEPALIVE   // detect dead connections
TCP_NODELAY    // disable Nagle — send small packets immediately
SO_RCVTIMEO    // receive timeout (struct timeval)
O_NONBLOCK     // non-blocking via fcntl(fd, F_SETFL, O_NONBLOCK)
```

---

## Network Diagnostic Tools

```bash
ping 192.168.1.1               # reachability + round-trip time
traceroute google.com          # path and latency per hop
nslookup google.com            # DNS lookup
dig google.com A               # detailed DNS query

ss -tlnp                       # listening TCP ports + which process
ss -tnp                        # established connections
tcpdump -i eth0 port 9000      # capture packets (needs root)
tcpdump -i any -w cap.pcap     # save capture to file (open in Wireshark)
nc -zv 192.168.1.100 9000      # test TCP connection
nc -l 9000                     # listen on port (quick server)
ip addr show                   # interfaces and IPs
ip route show                  # routing table
```

---

## Common Bugs

| Bug | Cause | Fix |
|---|---|---|
| "Address already in use" | Socket in TIME_WAIT after restart | `SO_REUSEADDR` |
| Partial recv | TCP stream, not message-based | RecvAll loop |
| Wrong byte order | Forgot `htonl`/`htons` | Always convert multi-byte integers |
| Blocks forever | No timeout | `SO_RCVTIMEO` or non-blocking + epoll |
| SIGPIPE crash | Write to closed socket | `signal(SIGPIPE, SIG_IGN)` |
| 200ms Nagle delay | Small writes batched | `TCP_NODELAY` |
| Fragmentation loss | UDP payload > 1472 bytes | Split at application level |

---

## LDS Networking Map

| Path | Protocol | Layer | Why |
|---|---|---|---|
| Kernel NBD ↔ LDS userspace | `socketpair` | Local | Zero-copy, same machine |
| LDS master ↔ Minion | UDP | L4 | Fast block ops, app-level retry |
| AutoDiscovery | UDP broadcast | L3/L4 | Minion announces itself on LAN |
| Mac client ↔ Linux server (planned) | TCP over Tailscale | L4+VPN | Reliable, cross-machine |

---

## Related Notes

- [[Sockets TCP]] — TCP socket API in depth, RecvAll loop
- [[UDP Sockets]] — UDP socket API, message boundaries, broadcast, multicast
- [[epoll]] — multiplexing many connections, Reactor pattern
- [[IPC Overview]] — local IPC: pipes, socketpair, unix sockets, shared memory
- [[../C/Serialization]] — binary wire protocol design and byte ordering
- [[../Linux/Signals]] — SIGPIPE when writing to a closed socket
