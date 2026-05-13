# TCP Sockets — The Machine

## The Model
A bidirectional pipe between two processes with guaranteed delivery and ordering. You hold one end (a file descriptor). The remote process holds the other end. Data you write flows through the pipe to the remote. Data the remote writes flows back. The kernel manages the pipe's internals: buffers, acknowledgments, retransmits, flow control.

## How It Moves

```
Server side:                          Client side:
─────────────                         ────────────
socket(AF_INET, SOCK_STREAM, 0)       socket(AF_INET, SOCK_STREAM, 0)
bind(fd, port=7800)
listen(fd, backlog=128)
                    ←── SYN ─────────── connect(fd, "127.0.0.1", 7800)
   ──── SYN+ACK ───→                    (blocks until connected)
                    ←── ACK ───────────
accept(fd) ← returns new_fd            (connect returns)
  new_fd = dedicated pipe to this client

send(new_fd, buf, len, 0)  ────────→  recv(new_fd, buf, len, 0)
recv(new_fd, buf, len, 0)  ←────────  send(new_fd, buf, len, 0)
close(new_fd)               ────────→  recv returns 0 (EOF)
```

**The RecvAll requirement:** `recv(fd, buf, n, 0)` may return LESS than `n` bytes even on a healthy connection. The kernel gives you whatever is in the receive buffer right now. Always loop:
```cpp
ssize_t RecvAll(int fd, char* buf, size_t n) {
    size_t total = 0;
    while (total < n) {
        ssize_t r = recv(fd, buf + total, n - total, 0);
        if (r <= 0) return r;   // 0=closed, -1=error
        total += r;
    }
    return total;
}
```

## The Blueprint

```cpp
// Server setup:
int server_fd = socket(AF_INET, SOCK_STREAM, 0);
int opt = 1;
setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));   // avoid "Address in use"

sockaddr_in addr = {};
addr.sin_family = AF_INET;
addr.sin_port = htons(7800);
addr.sin_addr.s_addr = INADDR_ANY;
bind(server_fd, (sockaddr*)&addr, sizeof(addr));
listen(server_fd, 128);

// Accept loop:
while (true) {
    sockaddr_in client_addr;
    socklen_t len = sizeof(client_addr);
    int client_fd = accept(server_fd, (sockaddr*)&client_addr, &len);
    // handle client_fd in a thread or via epoll
}
```

**`SO_REUSEADDR`**: without this, if LDS crashes and restarts, the port is in `TIME_WAIT` state for ~60 seconds — the OS refuses to rebind. `SO_REUSEADDR` allows rebinding immediately.

## Where It Breaks

- **Single `recv` for fixed-size message**: message arrives in 2 packets → you read half, think you read all → parse corrupted data. Always use RecvAll.
- **`close` without draining**: if you close before the remote sends its last bytes → remote gets `ECONNRESET` → data loss.
- **`send` blocking on full buffer**: `send` blocks if the kernel send buffer is full (remote is slow). Use non-blocking + epoll to handle this without blocking the Reactor.

## In LDS

`services/communication_protocols/tcp/src/TCPDriverComm.cpp`

`TCPDriverComm::RecvRequest` uses a `RecvAll`-style loop to read exactly 28 bytes (NBD request header). `SendReply` writes exactly 16 bytes. The LDS TCP server uses `SO_REUSEADDR` so it can be restarted immediately after a crash without waiting for `TIME_WAIT`.

The Reactor registers the listening socket with `EPOLLIN`. When a new connection arrives, `accept()` is called to get the client fd, which is also registered with epoll. This is the standard epoll server pattern.

## Validate

1. LDS reads an NBD header with `RecvAll(fd, buf, 28)`. The first call to `recv` returns 10 bytes. What does `RecvAll` do next, and what does it pass as the buffer pointer?
2. LDS crashes and immediately restarts. Without `SO_REUSEADDR`, `bind` fails. What kernel state causes this, and for how long?
3. A client connects to LDS and immediately sends 1000 requests without waiting for replies. Where do these requests accumulate, and what happens when they overflow?

## Connections

**Theory:** [[Core/Theory/Networking/02 - Sockets TCP]]  
**Mental Models:** [[epoll — The Machine]], [[File Descriptors — The Machine]], [[IPC Overview — The Machine]], [[UDP Sockets — The Machine]], [[Serialization — The Machine]]  
**Tradeoffs:** [[Why UDP vs TCP]]  
**LDS Implementation:** [[LDS/Linux Integration/TCPServer]], [[LDS/Decisions/Why TCP for Client]]  
**Runtime Machines:** [[LDS/Runtime Machines/TCPDriverComm — The Machine]]  
**Glossary:** [[TCP]], [[socketpair]]
