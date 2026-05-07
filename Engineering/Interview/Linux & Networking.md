# Interview — Linux & Networking

Systems programming questions: processes, signals, I/O multiplexing, sockets, byte ordering.

---

## Processes

**Q: What does `fork()` do?**

Creates an exact copy of the current process. The parent gets the child's PID; the child gets 0. Both run independently from the next instruction. Copy-on-write: pages are shared until either side writes, then copied.

```c
pid_t pid = fork();
if (pid == 0) {
    // child
    execv("/usr/bin/watchdog", argv);
} else if (pid > 0) {
    // parent — pid is the child's PID
    waitpid(pid, &status, 0);
} else {
    // fork failed
}
```

**Q: What does `exec()` do?**

Replaces the current process image with a new program. After `execv`, the process becomes the new program — same PID, new code, new stack, new heap.

`fork()` + `exec()` is the Unix way to launch a new program.

**Q: What is `waitpid()`?**

Waits for a child process to change state (exit, stop, continue). Without it, a dead child becomes a **zombie** — the OS keeps its exit status in the process table until the parent reads it.

**Where is this in LDS?**  
The C Watchdog (`ds/src/wd.c`) uses `fork()` + `execv()` to spawn the guardian process. When the guarded process dies, the guardian calls `fork()` + `execv()` to restart it.

---

## Signals

**Q: What is a signal? How do you handle one safely?**

A signal is an asynchronous notification sent to a process by the OS or another process. The process suspends its current execution and runs the signal handler.

**`sigaction` vs `signal`:**  
`sigaction` is the POSIX way — portable, predictable. `signal()` is obsolete and behavior is implementation-defined.

```c
struct sigaction sa = {0};
sa.sa_handler = my_handler;
sigemptyset(&sa.sa_mask);
sigaction(SIGUSR1, &sa, NULL);
```

**Q: What functions are async-signal-safe?**

A signal can interrupt any instruction, including malloc, printf, and mutex lock. Only async-signal-safe functions (e.g., `write`, `sem_post`, `atomic ops`) may be called inside a handler. `printf`, `malloc`, `std::cout` are **not** safe.

```c
// Safe: write to pipe or set a volatile sig_atomic_t flag
volatile sig_atomic_t g_got_signal = 0;
void handler(int) { g_got_signal = 1; }  // safe — just a store
```

**Q: What is `signalfd`?**

`signalfd` converts signals into file descriptors. You `read()` from the fd to receive signal info. This makes signals compatible with `epoll` — the event loop handles signals the same way as I/O events, no async-signal-safety problem.

```cpp
sigset_t mask;
sigemptyset(&mask);
sigaddset(&mask, SIGINT);
sigprocmask(SIG_BLOCK, &mask, NULL);   // block the signal from async delivery
int sfd = signalfd(-1, &mask, SFD_NONBLOCK);
// now add sfd to epoll — read signalfd_siginfo when it fires
```

**Where is this in LDS?**  
`Reactor` uses `signalfd` for SIGINT/SIGTERM — adds the signalfd to epoll alongside the NBD fd. When `Ctrl+C` is pressed, epoll returns the signalfd as ready; Reactor reads it and sets `m_stop = true`.

**Where is this in the C Watchdog?**  
The Watchdog uses `sigaction` for SIGUSR1/SIGUSR2 — the watchdog and the guarded process ping each other. `sig_atomic_t g_who` tracks who sent the last signal. `sem_timedwait` blocks waiting for the next ping with a timeout, so a missed ping triggers revival.

---

## I/O Multiplexing — epoll vs select vs poll

**Q: What is I/O multiplexing? Why do you need it?**

Watch multiple file descriptors simultaneously and act only when one is ready. Without it you'd need one thread per fd, or busy-poll each one.

| Mechanism | Scale | Complexity | OS |
|---|---|---|---|
| `select` | O(n) per call, max 1024 fds | Simple | POSIX |
| `poll` | O(n) per call, no fd limit | Slightly better | POSIX |
| `epoll` | O(1) per event, no fd limit | More setup | Linux only |

**Q: How does epoll work?**

1. `epoll_create1(0)` — creates an epoll instance (returns a fd)
2. `epoll_ctl(epfd, EPOLL_CTL_ADD, fd, &event)` — register an fd
3. `epoll_wait(epfd, events, max, timeout)` — block until an fd is ready; returns only the ready ones

```cpp
int epfd = epoll_create1(0);
struct epoll_event ev;
ev.events = EPOLLIN;
ev.data.fd = target_fd;
epoll_ctl(epfd, EPOLL_CTL_ADD, target_fd, &ev);

struct epoll_event events[16];
int n = epoll_wait(epfd, events, 16, -1);   // -1 = block forever
for (int i = 0; i < n; ++i) {
    handle(events[i].data.fd);
}
```

`EPOLLET` — edge-triggered mode. Only fires once when state changes (data arrives), not on every `epoll_wait` while data is available. Requires non-blocking fds and draining the fd completely each time.

**Where is this in LDS?**  
`Reactor` is the epoll wrapper. Currently watches the NBD fd and the signalfd. Phase 2A adds TCP client fds to the same epoll instance.

---

## TCP Sockets — the API

**Q: Walk me through a TCP server setup.**

```c
// 1. Create socket
int sfd = socket(AF_INET, SOCK_STREAM, 0);

// 2. Allow port reuse after restart
int opt = 1;
setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

// 3. Bind to address + port
struct sockaddr_in addr = {0};
addr.sin_family = AF_INET;
addr.sin_addr.s_addr = INADDR_ANY;
addr.sin_port = htons(7800);
bind(sfd, (struct sockaddr*)&addr, sizeof(addr));

// 4. Listen (backlog = pending connection queue size)
listen(sfd, 5);

// 5. Accept — blocks until a client connects
struct sockaddr_in client_addr;
socklen_t len = sizeof(client_addr);
int cfd = accept(sfd, (struct sockaddr*)&client_addr, &len);

// 6. Read/write on cfd like any fd
send(cfd, buf, n, 0);
recv(cfd, buf, n, 0);
```

**Q: Walk me through a TCP client setup.**

```c
int cfd = socket(AF_INET, SOCK_STREAM, 0);
struct sockaddr_in server = {0};
server.sin_family = AF_INET;
server.sin_port = htons(7800);
inet_pton(AF_INET, "192.168.1.100", &server.sin_addr);
connect(cfd, (struct sockaddr*)&server, sizeof(server));
// connected — now send/recv
```

**Where is this in LDS?**  
Phase 2A: `TCPServer` wraps the server-side setup; `BlockClient` wraps the client-side. The listening fd is added to Reactor's epoll; `OnAccept` calls `accept()` and adds the client fd to epoll dynamically.

---

## TCP Framing — the partial-read problem

**Q: Why can't you just call `recv()` once and trust you got the full message?**

TCP is a byte stream, not a message protocol. A single `send(buf, 13)` may arrive as three `recv()` calls returning 5 + 5 + 3 bytes. You must loop until you have all the bytes you expect.

```cpp
bool RecvAll(int fd, char* buf, size_t n) {
    size_t received = 0;
    while (received < n) {
        ssize_t r = recv(fd, buf + received, n - received, 0);
        if (r <= 0) return false;   // disconnect or error
        received += r;
    }
    return true;
}
```

**LDS wire protocol header (13 bytes):**

```
[type: 1B][offset: 8B big-endian][length: 4B big-endian]
```

Receiver always calls `RecvAll(fd, header, 13)` first, then `RecvAll(fd, data, length)` for a write payload.

---

## Byte Ordering

**Q: What is network byte order? What functions convert it?**

Network byte order is big-endian. Intel x86/x64 is little-endian. When sending multi-byte integers over a socket, convert them so both sides agree.

| Function | Direction | Size |
|---|---|---|
| `htons` / `ntohs` | host ↔ network | 16-bit |
| `htonl` / `ntohl` | host ↔ network | 32-bit |
| `htobe64` / `be64toh` | host ↔ big-endian | 64-bit |

```cpp
uint64_t offset_net = htobe64(offset);    // before sending
uint64_t offset_host = be64toh(offset_net); // after receiving
```

**macOS note:** `htobe64` may require `<machine/endian.h>` or use `OSSwapHostToBigInt64(x)` as an alternative.

**Where is this in LDS?**  
`BlockClient` converts offset and length before `send()`. `TCPServer` converts back with `be64toh` / `ntohl` after `RecvAll`.

---

## UDP vs TCP

**Q: When do you use UDP instead of TCP?**

| Property | TCP | UDP |
|---|---|---|
| Reliability | Guaranteed delivery + ordering | Best-effort, no guarantees |
| Overhead | Connection setup, ACKs, flow control | Minimal |
| Use case | File transfer, HTTP, LDS client link | DNS, video stream, LDS master↔minion |

LDS uses TCP for the Mac client link (reliability matters — you can't lose a write request). LDS uses UDP for master↔minion (bounded latency matters; loss is handled by the retry scheduler).

---

## inotify

**Q: How does inotify work?**

inotify watches filesystem paths for changes. Events: `IN_CREATE`, `IN_DELETE`, `IN_CLOSE_WRITE`, `IN_MOVED_TO`, etc.

```c
int ifd = inotify_init();
int wd = inotify_add_watch(ifd, "/path/to/dir", IN_CLOSE_WRITE);
// read from ifd — returns inotify_event structs
```

**Q: Why `IN_CLOSE_WRITE` instead of `IN_CREATE`?**

`IN_CREATE` fires when the file appears in the directory, but the file may still be open for writing — reading it at that point gets a partial file. `IN_CLOSE_WRITE` fires only after the writing process calls `close()`, so the file is complete.

**Where is this in LDS?**  
`DirMonitor` watches the plugin directory with `IN_CLOSE_WRITE`. When a new `.so` plugin is dropped in, DirMonitor fires; the `PNP` component calls the plugin loading callback.

---

## mmap

**Q: What is `mmap`?**

Maps a file or anonymous memory into the process's virtual address space. The mapped region looks like a regular array. The OS page-faults in data on demand.

```c
void* p = mmap(NULL, size, PROT_READ | PROT_WRITE,
               MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
// p is now usable memory
munmap(p, size);
```

Useful for: large file access without read() loops, IPC shared memory, zero-copy techniques. The NBD kernel module internally uses mmap-like page sharing when transferring block data.

---

## File Descriptors

**Q: What is a file descriptor?**

A small non-negative integer (per-process) that the kernel uses to refer to an open resource: file, socket, pipe, epoll instance, signalfd, inotify fd, eventfd. They're all "fds" and all work with `read`/`write`/`close`/`epoll_ctl`.

This uniformity is why `Reactor` can watch an NBD fd, a signalfd, and future TCP client fds with the same epoll loop — they're all just fds.

**Q: What happens if you don't close an fd?**

You leak a kernel resource. Each process has a limit (`ulimit -n`, typically 1024 or 65535). Too many open fds → `accept()` and `open()` fail with `EMFILE`.

**Where is this in LDS?**  
`NBDDriverComm` destructor closes the NBD fd. `TCPServer::CloseClient(fd)` removes the fd from epoll and calls `close(fd)` to prevent leaks when a client disconnects.
