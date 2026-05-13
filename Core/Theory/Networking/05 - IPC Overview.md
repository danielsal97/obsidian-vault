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

LDS uses `socketpair` for the NBD kernel↔userspace connection (`NBDDriverComm`). Works with `epoll` unlike regular pipes. See [[../Linux/02 - File Descriptors]].

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

- [[../Linux/05 - Shared Memory]] — zero-copy data sharing
- [[../Linux/06 - Semaphores]] — synchronizing access to shared resources
- [[../Linux/07 - mmap]] — memory-mapped files and anonymous mappings
- [[Sockets TCP]] — full TCP socket API
- [[UDP Sockets]] — UDP socket API
- [[../Linux/02 - File Descriptors]] — fd-based IPC, `socketpair`, `dup`

---

## Understanding Check

> [!question]- Why does LDS use socketpair instead of a regular pipe for NBD kernel↔userspace communication?
> pipe() creates two unidirectional fds — one read end and one write end. For NBD, the kernel sends requests and receives responses on the same channel, requiring bidirectional communication. socketpair() creates two fully connected bidirectional socket fds: writing to fds[0] is readable on fds[1] and vice versa. The other critical advantage is that socketpair fds are actual sockets — they work natively with select/poll/epoll, whereas Linux pipes before kernel 2.6.17 did not support poll correctly in all configurations. The Reactor's epoll_wait can watch a socketpair fd directly without special handling.

> [!question]- What goes wrong if you use shared memory between LDS master and minion processes without any synchronization?
> Shared memory provides the address space mapping but zero ordering guarantees. If the master writes a block offset and the minion reads it concurrently, the minion could see a torn write — half the old value and half the new — on 64-bit integers that are not naturally atomic on the bus. Even without tearing, the compiler or CPU can reorder writes so the minion sees the length field updated before the offset field, reading an inconsistent state. Shared memory requires an explicit synchronization layer — typically a POSIX semaphore or a mutex in shared memory — to guarantee that a complete message is visible before the reader consumes it.

> [!question]- Why can UNIX domain sockets pass an open file descriptor between processes, and what security use case does this enable?
> UNIX domain sockets transmit ancillary data alongside the normal byte stream via sendmsg()/recvmsg() with a cmsg of type SCM_RIGHTS. The kernel duplicates the fd into the receiving process's fd table — the receiver gets its own copy that refers to the same underlying file description, including its position, flags, and access rights. The key security use case is privilege separation: a privileged root process opens a raw socket or a device file that an unprivileged worker is not allowed to open, then passes the open fd to the worker over a UNIX socket. The worker can now use the fd without ever having the permission to open it directly.

> [!question]- When would you choose a POSIX message queue over a socketpair for IPC between two processes on the same host?
> POSIX message queues are a better fit when you need message priorities — the kernel delivers higher-priority messages before lower ones regardless of arrival order, which is hard to implement correctly over a socketpair. They also impose a configurable max-message-size and max-depth at creation time, providing natural backpressure without the producer having to implement its own bounded-queue logic. A socketpair is better when you need to multiplex the channel with other fds in an epoll loop, pass large variable-length data efficiently, or transfer file descriptors — none of which message queues support. For LDS's use case (low-latency block operations), socketpair with epoll is the right choice.

> [!question]- What happens if the LDS NBD userspace process crashes without closing its end of the socketpair?
> When a process exits or crashes, the OS closes all its open file descriptors. The kernel detects that the last reference to the socketpair endpoint is gone and sends an EOF (or EPOLLHUP) event to the other end — in this case, the NBD kernel module holding the other fd. The NBD driver will treat this as a device disconnection and fail any pending or future block I/O with an I/O error, which propagates up to the filesystem and any application using the NBD block device. From a recovery standpoint, this is correct behavior — it's far better than leaving the kernel waiting indefinitely on an orphaned fd.
