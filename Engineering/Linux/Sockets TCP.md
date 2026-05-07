# Sockets — TCP

---

## What is a Socket

A socket is a file descriptor representing one end of a communication channel. Both sides use `read`/`write` (or `send`/`recv`) on it like any fd.

```
Process A          Network          Process B
  socket ─────── TCP stream ─────── socket
  fd=5                               fd=7
```

---

## Address Family and Type

```c
int fd = socket(domain, type, protocol);

// Most common:
socket(AF_INET,  SOCK_STREAM, 0);   // TCP over IPv4
socket(AF_INET6, SOCK_STREAM, 0);   // TCP over IPv6
socket(AF_INET,  SOCK_DGRAM,  0);   // UDP over IPv4
socket(AF_UNIX,  SOCK_STREAM, 0);   // Unix domain socket (same machine, no network)
```

---

## Server Setup — Full Sequence

```c
// 1. Create socket
int sfd = socket(AF_INET, SOCK_STREAM, 0);
if (sfd < 0) { perror("socket"); exit(1); }

// 2. Allow reuse of port after restart
int opt = 1;
setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

// 3. Bind to address + port
struct sockaddr_in addr = {0};
addr.sin_family      = AF_INET;
addr.sin_addr.s_addr = INADDR_ANY;   // accept on all interfaces
addr.sin_port        = htons(7800);  // convert to network byte order

if (bind(sfd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
    perror("bind"); exit(1);
}

// 4. Start listening (backlog = max pending connections in queue)
listen(sfd, 10);

// 5. Accept a connection — blocks until client connects
struct sockaddr_in client_addr;
socklen_t client_len = sizeof(client_addr);
int cfd = accept(sfd, (struct sockaddr*)&client_addr, &client_len);
// cfd is the connected socket — use it to communicate with this client
// sfd continues to accept new connections

// 6. Communicate
send(cfd, buf, n, 0);
recv(cfd, buf, n, 0);

// 7. Close
close(cfd);
close(sfd);
```

---

## Client Setup — Full Sequence

```c
// 1. Create socket
int fd = socket(AF_INET, SOCK_STREAM, 0);

// 2. Set server address
struct sockaddr_in server = {0};
server.sin_family = AF_INET;
server.sin_port   = htons(7800);
inet_pton(AF_INET, "100.x.x.x", &server.sin_addr);   // IP string → binary

// 3. Connect — completes TCP handshake
if (connect(fd, (struct sockaddr*)&server, sizeof(server)) < 0) {
    perror("connect"); exit(1);
}

// 4. Communicate
send(fd, buf, n, 0);
recv(fd, buf, n, 0);

// 5. Close
close(fd);
```

---

## The Partial Read Problem — RecvAll

TCP is a **byte stream** — not a message protocol. A single `send(fd, buf, 100)` may arrive as multiple `recv()` calls returning 60 + 40 bytes. You must loop until all bytes are received.

```c
bool recv_all(int fd, void* buf, size_t n) {
    size_t received = 0;
    char* p = (char*)buf;
    
    while (received < n) {
        ssize_t r = recv(fd, p + received, n - received, 0);
        
        if (r == 0) return false;   // connection closed cleanly
        if (r < 0) return false;    // error
        
        received += r;
    }
    return true;
}
```

**Same applies to send** — `send()` may not send all bytes at once:
```c
bool send_all(int fd, const void* buf, size_t n) {
    size_t sent = 0;
    const char* p = (const char*)buf;
    
    while (sent < n) {
        ssize_t s = send(fd, p + sent, n - sent, 0);
        if (s <= 0) return false;
        sent += s;
    }
    return true;
}
```

---

## Byte Ordering

Multi-byte integers must be converted to network byte order (big-endian) before sending:

```c
// Sending:
uint16_t port   = htons(7800);     // host → network 16-bit
uint32_t length = htonl(512);      // host → network 32-bit
uint64_t offset = htobe64(4096);   // host → big-endian 64-bit

// Receiving:
uint16_t port   = ntohs(net_port);
uint32_t length = ntohl(net_length);
uint64_t offset = be64toh(net_offset);
```

Both Mac (ARM64) and Linux (x86-64) are little-endian natively — both sides must convert.

---

## Detecting Disconnect

```c
ssize_t n = recv(fd, buf, sizeof(buf), 0);

if (n == 0) {
    // Client closed connection gracefully (sent TCP FIN)
    close(fd);
}
if (n < 0) {
    if (errno == EAGAIN || errno == EWOULDBLOCK) {
        // Non-blocking fd, no data available right now — not an error
    } else {
        // Real error
        close(fd);
    }
}
```

---

## Non-Blocking Sockets

By default, `recv()` blocks until data arrives and `accept()` blocks until a client connects. With non-blocking mode, they return immediately with `EAGAIN` if no data/connection is ready.

```c
int flags = fcntl(fd, F_GETFL, 0);
fcntl(fd, F_SETFL, flags | O_NONBLOCK);
```

Use with epoll: `epoll_wait` tells you when the fd is ready, then `recv()` reads all available data without blocking. For edge-triggered mode, you must read until `EAGAIN`.

---

## Useful Socket Options

```c
// Reuse address immediately after restart (don't wait for TIME_WAIT):
setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

// Reuse port — multiple sockets can bind same port (load balancing):
setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, &opt, sizeof(opt));

// Disable Nagle algorithm — send small packets immediately (lower latency):
setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &opt, sizeof(opt));

// Keep connection alive with probes:
setsockopt(fd, SOL_SOCKET, SO_KEEPALIVE, &opt, sizeof(opt));

// Send/receive timeout:
struct timeval tv = {5, 0};   // 5 seconds
setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
```

---

## TCP Handshake (3-way)

```
Client                    Server
  │── SYN ──────────────▶│   "I want to connect"
  │◀─ SYN+ACK ───────────│   "OK, I'm ready"
  │── ACK ──────────────▶│   "Acknowledged"
  │  ← connection established →  │
```

`connect()` on client triggers the SYN. `accept()` on server completes after the handshake. Both sides now have a full-duplex byte stream.

---

## LDS Wire Protocol

```
Request header (13 bytes):
[op: 1B][offset: 8B big-endian][length: 4B big-endian]

Response header (5 bytes):
[status: 1B][length: 4B big-endian]

Op codes: 0x00=READ, 0x01=WRITE
Status:   0x00=OK,   0x01=ERROR
```

RecvAll(13 bytes) → parse → if WRITE: RecvAll(length bytes) → process → send response.
