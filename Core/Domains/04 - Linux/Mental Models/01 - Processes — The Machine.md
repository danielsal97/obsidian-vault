# Processes — The Machine

## The Model
A sealed container running in the OS. Its own virtual address space, its own fd table, its own CPU register state. `fork()` photocopies the entire container instantly — the copy shares physical pages with the original until either writes (copy-on-write). `exec()` replaces the container's program while keeping the container itself (pid, fds, environment).

## How It Moves

```
Parent process
  pid=100, fd table: [0,1,2,5,7], memory: [code|data|heap|stack]
        |
        v fork()
        
Parent (pid=100)          Child (pid=101)
  fork() returns 101        fork() returns 0
  fd table: copy            fd table: copy (same underlying files)
  memory: shared pages      memory: shared pages (copy-on-write)
  
Child writes to memory:
  kernel creates private copy of that page for child
  parent's page unchanged
  
exec("/usr/bin/ls"):
  replaces child's code/data/heap/stack with ls's program
  pid stays 101, fds stay open (unless O_CLOEXEC)
```

**Copy-on-write:** `fork()` is fast even for a 1GB process because no actual copying happens. Physical pages are marked read-only and shared. Only when a page is written does the kernel create a private copy — and only for that one page.

## The Blueprint

```c
pid_t pid = fork();
if (pid == 0) {
    // Child: pid == 0
    execl("/bin/ls", "ls", "-la", NULL);   // replace with ls
    // If exec fails, we're still here:
    exit(1);
} else if (pid > 0) {
    // Parent: pid = child's pid
    int status;
    waitpid(pid, &status, 0);   // prevent zombie
    if (WIFEXITED(status)) printf("child exited: %d\n", WEXITSTATUS(status));
} else {
    // fork failed (too many processes)
    perror("fork");
}
```

**Zombie process:** child exits but parent never calls `wait()` — child's entry stays in the process table (just the exit code, no memory). Accumulates until parent exits or calls `wait`.

**Orphan process:** parent exits before child — child is re-parented to `init` (pid=1), which automatically reaps it.

## Where It Breaks

- **Forgetting `waitpid`**: zombie processes accumulate, eventually exhaust the process table limit
- **fd inheritance**: child inherits all open fds from parent. If parent has a socket open, child also has it. Use `O_CLOEXEC` on fds you don't want inherited.
- **Double-close after fork**: parent and child both `close(fd)` the same underlying file description — first close succeeds, second may close an unrelated fd if the number was reused

## In LDS

`services/communication_protocols/nbd/src/NBDDriverComm.cpp`

LDS does not fork — it uses a single-process multi-threaded architecture. But `fork()` is the mechanism Linux uses to launch the NBD userspace helper (`nbd-client`) that connects `/dev/nbd0` to LDS. Understanding fork/exec is how you understand how that external process interacts with the LDS process via a Unix socket.

## Validate

1. `fork()` returns twice. How does the child know it's the child?
2. LDS opens fd=7 (a TCP socket). It forks to launch a subprocess. The subprocess doesn't use TCP. What problem does fd inheritance cause, and how do you prevent it?
3. Parent calls `fork()` when its vector has 1000 elements. The child modifies element[0]. Parent reads element[0]. What does the parent see? What physical memory event happened?

## Connections

**Theory:** [[01 - Processes]]  
**Mental Models:** [[File Descriptors — The Machine]], [[Process Memory Layout — The Machine]], [[Signals — The Machine]], [[Shared Memory — The Machine]]  
**LDS Implementation:** [[LDS/Linux Integration/NBDDriverComm]] — fork/exec for nbd-client subprocess  
**Glossary:** [[pthreads]], [[VFS]]
