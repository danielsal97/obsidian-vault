# Interview — Linux

Systems programming questions: processes, signals, file descriptors, mmap, inotify.

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

## File Descriptors

**Q: What is a file descriptor?**

A small non-negative integer (per-process) that the kernel uses to refer to an open resource: file, socket, pipe, epoll instance, signalfd, inotify fd, eventfd. They're all "fds" and all work with `read`/`write`/`close`/`epoll_ctl`.

This uniformity is why `Reactor` can watch an NBD fd, a signalfd, and future TCP client fds with the same epoll loop — they're all just fds.

**Q: What happens if you don't close an fd?**

You leak a kernel resource. Each process has a limit (`ulimit -n`, typically 1024 or 65535). Too many open fds → `accept()` and `open()` fail with `EMFILE`.

**Where is this in LDS?**  
`NBDDriverComm` destructor closes the NBD fd. `TCPServer::CloseClient(fd)` removes the fd from epoll and calls `close(fd)` to prevent leaks when a client disconnects.

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

## Related

→ [[01 - Networking Q&A]]
→ [[10 - Context Switch — The Machine]]
→ [[11 - Scheduler — The Machine]]
→ [[01 - Processes — The Machine]]
→ [[03 - Signals — The Machine]]
