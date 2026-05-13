# File Descriptors — The Machine

## The Model
A coat check at a venue: you hand over your coat (open a file/socket/pipe), the attendant stores it and gives you back a small numbered ticket (integer 3, 4, 5...). Every time you want your coat, you hand back the ticket — you never touch the storage room directly.

## How It Moves

```
Process A                  Kernel
─────────────────────────────────────────────────────
fd = open("file", O_RDWR)
  └─► syscall ──────────►  allocates inode reference
                            finds lowest free slot in
                            fd table
  ◄──────────── returns ─── integer (e.g. 5)

read(5, buf, 100)
  └─► syscall ──────────►  looks up fd 5 in table
                            finds file description
                            reads bytes from inode
  ◄──────────── returns ─── bytes copied to buf

close(5)
  └─► syscall ──────────►  decrements ref count
                            if ref == 0: frees resource
                            marks slot 5 as free
```

**The fd table — per process:**
```
Process fd table:
  [0] → stdin   (keyboard)
  [1] → stdout  (terminal)
  [2] → stderr  (terminal)
  [3] → your file
  [4] → your socket
  [5] → (free)
```

**Why constraints exist:**
- The integer is just an index. The real resource lives in kernel space, inaccessible from ring 3.
- `close()` does NOT immediately destroy the resource — it decrements a reference count. If two fds point to the same underlying file (via `dup()`), the resource lives until the last one closes.
- The kernel always assigns the **lowest free slot** — so after `close(3)`, the next `open()` gets 3 back. This is why accidental double-close is catastrophic: you close fd 3 (your file), 3 gets reused for a new socket, then the second `close(3)` kills the socket.

## The Blueprint

- **0, 1, 2 are pre-wired:** stdin, stdout, stderr. Set up by the shell before `main()` runs.
- **fd table is per-process:** `fork()` copies it. Parent and child share the same underlying file descriptions (same seek position).
- **`close()`:** decrements the kernel reference count. The description is freed only when count hits zero.
- **`O_CLOEXEC` / `SFD_CLOEXEC`:** marks the fd so the kernel automatically closes it on `exec()`. Without this, every `exec()`'d child inherits all your open fds — including network sockets, device files, secrets.
- **`dup2(src, dst)`:** makes dst point to the same description as src. This is how shells implement `>` redirection: `dup2(file_fd, 1)` replaces stdout.
- **`/proc/self/fd/`:** on Linux, lists every open fd as a symlink to the actual resource. Use this to debug fd leaks.
- **Max fds:** per-process limit (`ulimit -n`, default 1024 soft). System-wide limit separate. Exhaust them → `EMFILE` / `ENFILE` errors.

```cpp
// CLOEXEC example: signalfd in reactor
m_signal_fd = signalfd(-1, &mask, SFD_CLOEXEC);
// If LDS ever exec()s a subprocess, this fd won't leak into it
```

## Where It Breaks

**Double close:** fd 3 closes → kernel marks slot free → another `open()` claims slot 3 → second `close(3)` kills the NEW resource. Silent corruption — no crash until the new fd holder tries to use it.

**Fd leak:** open file never closed → slot stays occupied forever → under load, process hits `EMFILE` → all subsequent `open()`/`socket()`/`accept()` calls return -1 → system appears to hang.

**Forgot `O_CLOEXEC`:** `fork()` + `exec()` child inherits your TCP socket fd. The child holds the socket open even after the parent closes it — remote peer never sees EOF. The connection appears frozen.

**Use after close:** fd slot reused, code holds the old integer and calls `read(old_fd)` — now reading from a completely different resource. Data corruption, no warning.

## In LDS

**`/Users/danielsa/Desktop/lds-project/Igit/projects/lds/services/communication_protocols/nbd/src/NBDDriverComm.cpp`**
- Line 99: `socketpair(AF_UNIX, SOCK_STREAM, 0, sp)` — creates two connected fds (`m_serverFd`, `m_clientFd`)
- Line 105: `open(dev_.c_str(), O_RDWR)` — opens `/dev/nbd0`, returns `m_nbdFd`
- Lines 108–129: every error path calls `close()` on all allocated fds before throwing — correct RAII-style fd management
- Line 264: `GetFD()` returns `m_serverFd` — this integer is then handed to `epoll_ctl` in the Reactor

**`/Users/danielsa/Desktop/lds-project/Igit/projects/lds/design_patterns/reactor/src/reactor.cpp`**
- Line 10: `epoll_create1(0)` — the epoll itself is an fd (`m_epoll_fd`)
- Line 36: `signalfd(-1, &mask, SFD_CLOEXEC)` — `SFD_CLOEXEC` set intentionally; signal fd won't leak across exec

## Validate

1. LDS calls `socketpair()` and gets back `sp[0]` and `sp[1]`. Both are 5 and 6. Then `open("/dev/nbd0")` returns 7. What integer does the next `open()` call return if nothing else has run? Trace through the fd table.
2. Why does the `Reactor` destructor close `m_signal_fd` before `m_epoll_fd`, and does the order matter? What happens if you close `m_epoll_fd` first while `m_signal_fd` is still registered in it?
3. `NBDDriverComm::Disconnect()` sets `m_nbdFd = -1` after closing it. Why is the assignment to -1 necessary? What happens on the next call to `Disconnect()` if you skip it?

## Connections

**Theory:** [[Core/Domains/04 - Linux/Theory/02 - File Descriptors]]  
**Mental Models:** [[epoll — The Machine]], [[TCP Sockets — The Machine]], [[Processes — The Machine]], [[RAII — The Machine]], [[File IO — The Machine]]  
**LDS Implementation:** [[LDS/Linux Integration/NBDDriverComm]] — socketpair fd lifecycle; [[LDS/Infrastructure/Reactor]] — epoll fd  
**Runtime Machines:** [[LDS/Runtime Machines/NBDDriverComm — The Machine]]  
**Glossary:** [[epoll]], [[socketpair]]
