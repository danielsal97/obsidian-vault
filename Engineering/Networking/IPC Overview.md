# IPC Overview — Inter-Process Communication

Processes have isolated address spaces. IPC is how they exchange data or synchronize.

---

## Mechanism Comparison

| Mechanism | Scope | Direction | Latency | Copy | Notes |
|---|---|---|---|---|---|
| **Pipe** | Same host, related processes | Unidirectional | ~1 µs | Yes | `pipe()` — parent↔child |
| **socketpair** | Same host | Bidirectional | ~1 µs | Yes | Like pipe but full-duplex; works with select/epoll |
| **FIFO (named pipe)** | Same host, any process | Unidirectional | ~1 µs | Yes | Has a filename in filesystem |
| **POSIX shm + mmap** | Same host | Both | ~50 ns | No | Fastest; needs separate sync |
| **UNIX domain socket** | Same host | Both | ~2 µs | Yes | File path as address; supports `sendmsg` + fd passing |
| **TCP socket** | Same or different hosts | Both | ~5–20 µs | Yes | Standard; works over network |
| **UDP socket** | Same or different hosts | Both | ~5–20 µs | Yes | No connection; message boundaries preserved |
| **Semaphore** | Same host | Signal only | ~100 ns | No | Synchronization, not data transfer |
| **Signal** | Same host | One direction | ~1 µs | No | Very limited payload (sigqueue has 1 int) |
| **Message queue** | Same host | Both | ~2 µs | Yes | POSIX: `mq_open` — ordered, bounded |

---

## Pipes

```c
int fds[2];
pipe(fds);   // fds[0] = read end, fds[1] = write end

pid_t pid = fork();
if (pid == 0) {
    close(fds[1]);
    char buf[64];
    read(fds[0], buf, sizeof(buf));   // child reads
} else {
    close(fds[0]);
    write(fds[1], "hello", 5);        // parent writes
}
```

Pipes have a kernel buffer (~64KB). `write` blocks when full; `read` blocks when empty.

---

## socketpair

```c
int fds[2];
socketpair(AF_UNIX, SOCK_STREAM, 0, fds);  // bidirectional pipe
// fds[0] and fds[1] are connected — write to one, read from the other
```

LDS uses `socketpair` for the NBD kernel↔userspace connection (`NBDDriverComm`). Works with `epoll` unlike regular pipes. See [[../Linux/File Descriptors]].

---

## UNIX Domain Sockets

Like TCP sockets but in the filesystem namespace:

```c
// Server:
int sfd = socket(AF_UNIX, SOCK_STREAM, 0);
struct sockaddr_un addr = {.sun_family = AF_UNIX};
strcpy(addr.sun_path, "/tmp/myapp.sock");
bind(sfd, (struct sockaddr*)&addr, sizeof(addr));
listen(sfd, 5);

// Client:
int cfd = socket(AF_UNIX, SOCK_STREAM, 0);
connect(cfd, (struct sockaddr*)&addr, sizeof(addr));
```

Advantages over TCP loopback:
- No port number needed
- Permission via file permissions
- Can pass open file descriptors between processes via `sendmsg` + `SCM_RIGHTS`

---

## Passing File Descriptors

UNIX sockets can send an open fd from one process to another — the receiving process gets its own copy:

```c
// Sender:
struct msghdr msg = {0};
struct cmsghdr* cmsg;
char buf[CMSG_SPACE(sizeof(int))];
// ... fill msg with target fd ...
sendmsg(sfd, &msg, 0);

// Receiver:
recvmsg(rfd, &msg, 0);
int received_fd = *(int*)CMSG_DATA(cmsg);
```

Used in privilege separation (pass socket to worker, worker has no bind permission).

---

## POSIX Message Queue

```c
#include <mqueue.h>

mqd_t mq = mq_open("/myqueue", O_CREAT | O_RDWR, 0666, NULL);
mq_send(mq, "hello", 5, 0);    // priority 0

char buf[1024];
unsigned prio;
mq_receive(mq, buf, sizeof(buf), &prio);

mq_close(mq);
mq_unlink("/myqueue");
```

Messages are ordered and bounded. Supports `select`/`epoll` via the `mqd_t` fd.

---

## When to Use What

| Situation | Use |
|---|---|
| Parent↔child, unidirectional, simple | `pipe` |
| Parent↔child, bidirectional | `socketpair` |
| Any two processes, same host | UNIX domain socket |
| Maximum throughput, large data, same host | Shared memory + semaphore |
| Cross-machine | TCP or UDP |
| Send fd between processes | `sendmsg` over UNIX socket |
| Bounded message queue, priorities | POSIX message queue |

---

## LDS Context

| Path | Mechanism |
|---|---|
| NBD kernel ↔ LDS userspace | `socketpair` (inside `NBDDriverComm`) |
| Master ↔ Minion (different machines) | UDP |
| LDS client ↔ LDS server (planned TCP) | TCP |
| `AutoDiscovery` new minion announcement | UDP broadcast |

---

## Related Notes

- [[../Linux/Shared Memory]] — zero-copy data sharing
- [[../Linux/Semaphores]] — synchronizing access to shared resources
- [[../Linux/mmap]] — memory-mapped files and anonymous mappings
- [[Sockets TCP]] — full TCP socket API
- [[UDP Sockets]] — UDP socket API
- [[../Linux/File Descriptors]] — fd-based IPC, `socketpair`, `dup`
