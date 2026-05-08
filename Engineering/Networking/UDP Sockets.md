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

---

## Understanding Check

> [!question]- Why does calling connect() on a UDP socket not establish a connection, and what concrete benefit does it give the LDS master when talking to a known minion?
> UDP is connectionless — connect() on a UDP socket only sets the kernel's default destination address and filters incoming packets to that source. No handshake occurs, no SYN is sent, and the minion doesn't know anything happened. The benefit for LDS is twofold: the master can use send()/recv() instead of sendto()/recvfrom(), and the socket will silently discard UDP datagrams from any source other than that minion's address, reducing the risk of rogue or stale packets from a different minion being interpreted as responses to the current request.

> [!question]- What goes wrong if the LDS ResponseManager's receive buffer is smaller than the actual datagram the minion sent?
> UDP truncates silently. recvfrom() returns at most buf_size bytes and discards the rest — there is no error, no EAGAIN, and no way to retrieve the truncated portion. If the response header fits but the data payload is cut off, the ResponseManager would parse a valid-looking header but act on incomplete block data — partial writes or incorrect reads. The fix is to size receive buffers to at least the maximum possible datagram the protocol can produce, which for LDS is bounded by the block size plus header overhead.

> [!question]- Why does LDS use application-level retry with exponential backoff over UDP rather than just switching to TCP for master↔minion communication?
> TCP's reliability comes at a cost: per-connection state, head-of-line blocking, congestion control, and a full handshake before any data flows. For block storage operations where the master talks to many minions simultaneously and a single slow minion should not delay others, UDP's model fits better. Application-level retry with MSG_ID tracking lets the master pipeline many in-flight requests, retry only the specific lost ones, and apply custom timeout policies (exponential backoff, max retries, then error propagation). TCP would force a retry of all in-flight data for that connection if a segment is lost, and the 3-way handshake cost per connection adds latency that matters when operations are frequent and small.

> [!question]- Why is UDP broadcast unsuitable for LDS AutoDiscovery once the cluster spans multiple network subnets?
> Broadcast (255.255.255.255 or the subnet broadcast address) is confined to a single Layer 2 network segment. Routers do not forward broadcast packets between subnets by design, to prevent broadcast storms. If LDS minions and the master are on different VLANs or subnets — as would happen in a datacenter or across a Tailscale VPN — the broadcast "Hello I'm here" from a new minion would never reach the master. The solution is either multicast (routers can be configured to forward specific multicast groups) or a unicast registration mechanism where minions send a directed UDP packet to a known master address.

> [!question]- If two UDP datagrams are sent back-to-back from a minion to the master, can the master's recvfrom() calls receive them in reverse order, and how does LDS handle this?
> Yes. UDP makes no ordering guarantees — datagrams are routed independently at the IP layer and can arrive in any order or not at all. The master's recvfrom() calls would return them in whichever order the OS received them. LDS handles this via the MSG_ID field in every response header: the ResponseManager matches each incoming response to its pending request by MSG_ID rather than assuming sequential arrival. The Scheduler can therefore process out-of-order responses correctly, retiring whichever request completed first regardless of submission order.
