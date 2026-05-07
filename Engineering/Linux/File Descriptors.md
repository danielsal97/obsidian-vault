# File Descriptors

---

## What is a File Descriptor

A file descriptor (fd) is a small non-negative integer that acts as a handle to a kernel resource. The kernel maintains a table per process mapping fd numbers to kernel objects.

```
Process fd table:
  0 → stdin  (keyboard)
  1 → stdout (terminal)
  2 → stderr (terminal)
  3 → open file "data.txt"
  4 → TCP socket
  5 → epoll instance
  6 → inotify fd
  7 → signalfd
```

Every `open()`, `socket()`, `accept()`, `epoll_create1()`, `inotify_init()` returns a new fd number.

---

## Everything is a File

Unix's core design: all resources look like files. They all support `read()`, `write()`, `close()`. This uniformity is why `epoll` can watch files, sockets, pipes, signalfd, inotify — they're all just fds.

| Resource | How created | fd behavior |
|---|---|---|
| Regular file | `open()` | `read`/`write` at offset |
| Directory | `open()` | `read` returns directory entries |
| Pipe | `pipe()` | `read`/`write` byte stream |
| TCP socket | `socket()` + `accept()` | `read`/`write` byte stream |
| UDP socket | `socket()` | `read`/`write` datagrams |
| Unix socket | `socket(AF_UNIX)` | Like TCP but same-machine |
| epoll instance | `epoll_create1()` | `epoll_wait` |
| signalfd | `signalfd()` | `read` returns signal info |
| inotify | `inotify_init()` | `read` returns filesystem events |
| timerfd | `timerfd_create()` | `read` when timer fires |
| eventfd | `eventfd()` | `write` to signal, `read` to consume |

---

## fd Lifecycle

```c
// Acquire:
int fd = open("file.txt", O_RDONLY);
int fd = socket(AF_INET, SOCK_STREAM, 0);

// Use:
read(fd, buf, n);
write(fd, buf, n);

// Release:
close(fd);   // always close when done — fd is a limited resource
```

After `close(fd)`, the fd number can be reused by the next `open()`/`socket()`/etc. This is why double-close is dangerous:

```c
close(fd);   // fd=5 released
// ... some other code opens a file, gets fd=5 ...
close(fd);   // closes the new, unrelated file — silent bug
```

---

## fd Limits

Each process has a limit on open fds:
```bash
ulimit -n        # show soft limit (default: 1024 or 65535)
ulimit -n 65535  # set limit for current shell session

# System-wide limit:
cat /proc/sys/fs/file-max
```

Hitting the limit causes `accept()`, `open()`, `socket()` to fail with `EMFILE` (too many open files). A server that leaks fds will eventually stop accepting connections.

---

## Checking Open FDs

```bash
ls -la /proc/PID/fd      # list all open fds for a process
lsof -p PID              # detailed info about each fd
```

---

## File Status Flags

```c
int flags = fcntl(fd, F_GETFL);
fcntl(fd, F_SETFL, flags | O_NONBLOCK);  // make non-blocking
fcntl(fd, F_SETFL, flags | O_APPEND);   // writes always append
```

---

## FD_CLOEXEC — Close on Exec

By default, fds are inherited by child processes after `fork()`/`exec()`. This can cause leaks — the child holds the parent's sockets open.

```c
// Set close-on-exec at creation:
int sfd = socket(AF_INET, SOCK_STREAM, SOCK_CLOEXEC);
int efd = epoll_create1(EPOLL_CLOEXEC);

// Or set after creation:
fcntl(fd, F_SETFD, FD_CLOEXEC);
```

`FD_CLOEXEC` closes the fd automatically when `exec()` is called. Best practice: always set it on fds you don't intend to inherit.

---

## dup / dup2 — Duplicate FDs

```c
int new_fd = dup(old_fd);        // new fd refers to same open file
dup2(old_fd, new_fd);            // new_fd becomes a copy of old_fd (closes new_fd first if open)

// Classic use — redirect stdout to a file:
int log = open("log.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
dup2(log, STDOUT_FILENO);        // stdout now writes to log.txt
close(log);                       // original fd no longer needed
```

Used in shell pipe implementation and daemon setup.

---

## Pipe

A unidirectional byte stream between two fds:

```c
int pipefd[2];
pipe(pipefd);
// pipefd[0] = read end
// pipefd[1] = write end

write(pipefd[1], "hello", 5);
char buf[5];
read(pipefd[0], buf, 5);
```

Typically used with `fork()`: parent writes to one end, child reads from the other (or vice versa).

---

## socketpair

Creates two connected sockets — both ends are readable and writable:

```c
int sv[2];
socketpair(AF_UNIX, SOCK_STREAM, 0, sv);
// sv[0] and sv[1] are connected
// write to sv[0] → readable at sv[1], and vice versa
```

**LDS:** `NBDDriverComm` uses `socketpair(AF_UNIX, SOCK_STREAM)` — the kernel NBD driver writes to one end (via `ioctl(NBD_SET_SOCK)`), our process reads from the other.

---

## LDS fd Map

| fd | What it is | Who owns it |
|---|---|---|
| socketpair[0] | NBD server end (kernel writes here) | Set with ioctl(NBD_SET_SOCK) |
| socketpair[1] | NBD client end (we read/write here) | NBDDriverComm |
| epfd | epoll instance | Reactor |
| signalfd | signal notifications | Reactor |
| listen_fd | TCP listen socket | TCPServer (Phase 2A) |
| client_fd | TCP client connection | TCPServer (Phase 2A, dynamic) |
