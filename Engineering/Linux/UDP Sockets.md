# UDP Sockets

UDP is connectionless — no handshake, no guaranteed delivery, no ordering. Fire and forget. Faster and simpler than TCP for cases where occasional loss is acceptable.

---

## UDP vs TCP

| | UDP | TCP |
|---|---|---|
| Connection | None — just send | 3-way handshake |
| Reliability | No — packets may be lost, duplicated, reordered | Yes — guaranteed delivery and order |
| Overhead | Minimal header (8 bytes) | Large header, ACKs, flow control |
| Latency | Low | Higher |
| Use case | DNS, video/audio streaming, game state, LDS master↔minion | HTTP, file transfer, LDS client link |
| Message boundaries | Preserved — one send = one recv | Stream — RecvAll loop required |

---

## Server Setup

```c
// 1. Create UDP socket:
int sfd = socket(AF_INET, SOCK_DGRAM, 0);

// 2. Bind to port:
struct sockaddr_in addr = {0};
addr.sin_family      = AF_INET;
addr.sin_addr.s_addr = INADDR_ANY;
addr.sin_port        = htons(9000);
bind(sfd, (struct sockaddr*)&addr, sizeof(addr));

// 3. Receive — recvfrom gives sender's address:
struct sockaddr_in client;
socklen_t client_len = sizeof(client);
char buf[1024];
ssize_t n = recvfrom(sfd, buf, sizeof(buf), 0,
                     (struct sockaddr*)&client, &client_len);

// 4. Reply to sender:
sendto(sfd, reply, reply_len, 0,
       (struct sockaddr*)&client, client_len);
```

---

## Client Setup

```c
int sfd = socket(AF_INET, SOCK_DGRAM, 0);

struct sockaddr_in server = {0};
server.sin_family = AF_INET;
server.sin_port   = htons(9000);
inet_pton(AF_INET, "192.168.1.100", &server.sin_addr);

// Send — no connect() needed:
sendto(sfd, msg, msg_len, 0, (struct sockaddr*)&server, sizeof(server));

// Receive response:
struct sockaddr_in from;
socklen_t from_len = sizeof(from);
char buf[1024];
recvfrom(sfd, buf, sizeof(buf), 0, (struct sockaddr*)&from, &from_len);

close(sfd);
```

---

## Connected UDP

`connect()` on UDP doesn't create a connection — it just sets the default destination so you can use `send()`/`recv()` instead of `sendto()`/`recvfrom()`:

```c
connect(sfd, (struct sockaddr*)&server, sizeof(server));

// Now use send/recv:
send(sfd, buf, n, 0);
recv(sfd, buf, sizeof(buf), 0);

// Also filters: only receives from that specific address
```

---

## Message Boundaries

Unlike TCP, UDP preserves message boundaries. One `sendto` = one `recvfrom`. No RecvAll loop needed.

```c
// Sender sends 100 bytes:
sendto(sfd, data, 100, ...);

// Receiver:
char buf[1500];
n = recvfrom(sfd, buf, sizeof(buf), ...);
// n == 100 — got the whole message at once
```

**But:** if your buffer is too small, the message is **truncated** — extra bytes are silently discarded:
```c
char buf[50];
n = recvfrom(sfd, buf, 50, ...);  // sender sent 100 — you only get 50, rest gone
```

---

## Packet Loss and Retries

UDP gives no delivery guarantees. LDS handles this at the application layer:

```
MinionProxy::SendPutBlock() → sends UDP → returns MSG_ID
Scheduler tracks MSG_ID with deadline
ResponseManager listens for ACK on UDP port
If deadline exceeded → retry (exponential backoff: 1s, 2s, 4s)
After max retries → propagate error
```

This is the application-level reliability layer on top of unreliable UDP.

---

## MTU and Fragmentation

Maximum Transmission Unit (MTU) for Ethernet: **1500 bytes**.  
UDP header: 8 bytes. IP header: 20 bytes.  
Max safe UDP payload: **1472 bytes**.

Larger datagrams are fragmented by IP layer — any fragment lost = whole datagram lost. Reassembly overhead.

**Best practice:** keep UDP payloads under 1472 bytes. For larger data, split at application level.

---

## Broadcast

Send to all hosts on the local network:

```c
int opt = 1;
setsockopt(sfd, SOL_SOCKET, SO_BROADCAST, &opt, sizeof(opt));

struct sockaddr_in bcast = {0};
bcast.sin_family      = AF_INET;
bcast.sin_port        = htons(9000);
bcast.sin_addr.s_addr = INADDR_BROADCAST;  // 255.255.255.255

sendto(sfd, msg, len, 0, (struct sockaddr*)&bcast, sizeof(bcast));
```

Used in LDS AutoDiscovery — new minion broadcasts "Hello I'm here" and master receives it.

---

## Multicast

Send to a group of hosts (more targeted than broadcast):

```c
// Join a multicast group:
struct ip_mreq mreq;
inet_pton(AF_INET, "224.0.0.1", &mreq.imr_multiaddr);
mreq.imr_interface.s_addr = INADDR_ANY;
setsockopt(sfd, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq));

// Send to group:
struct sockaddr_in mcast_addr;
inet_pton(AF_INET, "224.0.0.1", &mcast_addr.sin_addr);
sendto(sfd, msg, len, 0, (struct sockaddr*)&mcast_addr, sizeof(mcast_addr));
```

---

## LDS Wire Protocol (UDP)

```
Master → Minion request:
[MSG_ID: 4B][OP: 1B][OFFSET: 8B][LEN: 4B][DATA: var]

Minion → Master response:
[MSG_ID: 4B][STATUS: 1B][LEN: 4B][RESERVED: 4B][DATA: var]
```

MSG_ID allows ResponseManager to match responses to pending requests even when they arrive out of order.
