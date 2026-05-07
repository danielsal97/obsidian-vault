# Processes — fork, exec, wait

---

## What is a Process

A process is an independent execution unit with its own:
- Virtual address space (code, stack, heap, data)
- File descriptor table
- PID (process ID)
- Signal handlers
- Working directory, environment variables

The kernel schedules processes to run on CPU cores. Each process thinks it owns the entire machine — virtual memory provides the illusion.

---

## fork()

Creates an exact copy of the current process. Both parent and child continue executing from the next instruction after `fork()`.

```c
pid_t pid = fork();

if (pid < 0) {
    // fork failed — too many processes, out of memory
    perror("fork");

} else if (pid == 0) {
    // CHILD — pid == 0 is the signal
    // has a copy of parent's memory, file descriptors, etc.
    printf("I am child, my pid = %d\n", getpid());

} else {
    // PARENT — pid = child's PID
    printf("I spawned child %d\n", pid);
}
```

**Copy-on-write:** the kernel doesn't actually copy all memory pages on fork. Pages are shared until one side writes — then the kernel copies just that page. Makes fork() fast even for large processes.

**What's inherited:** memory, open fds, signal handlers, working directory, environment.  
**What's NOT inherited:** pending signals, timers, memory locks.

---

## exec family

Replaces the current process image with a new program. After exec, the process runs a different program but keeps the same PID.

```c
// execv — path + argv array
char* args[] = { "/bin/ls", "-la", NULL };   // NULL-terminated
execv("/bin/ls", args);

// execvp — searches PATH for the program
execvp("ls", args);

// execlp — variadic args (l = list)
execlp("ls", "ls", "-la", NULL);
```

`exec` does NOT return on success — the current program is gone. If it returns, something failed.

**fork + exec = Unix way to launch a new program:**
```c
pid_t pid = fork();
if (pid == 0) {
    // child: replace with new program
    execv("/usr/bin/watchdog", argv);
    // if we get here, exec failed
    perror("exec");
    exit(1);
}
// parent continues
```

---

## wait / waitpid

Parent waits for a child to change state (exit, stop, killed by signal).

```c
int status;
pid_t child = waitpid(pid, &status, 0);   // block until pid exits

// Check how child ended:
if (WIFEXITED(status)) {
    int exit_code = WEXITSTATUS(status);   // 0 = success
}
if (WIFSIGNALED(status)) {
    int sig = WTERMSIG(status);   // which signal killed it
}
```

**Zombie process:** when a child exits, its entry stays in the process table until the parent calls `wait`. A zombie holds only its PID and exit status — minimal overhead, but PID is occupied. If parent never waits, the zombie accumulates.

**Orphan process:** parent exits before the child. The child is adopted by `init` (PID 1), which periodically calls `wait`.

---

## exit() and _exit()

```c
exit(0);     // flush stdio buffers, call atexit handlers, then exit
_exit(0);    // exit immediately — no cleanup. Use in child after fork/exec failure
```

In the child after `fork()`, always use `_exit()` if not calling `exec`. Using `exit()` in the child can flush the parent's stdio buffers.

---

## Process Groups and Sessions

**Process group:** set of related processes (e.g., a pipeline `ls | grep foo`). All receive signals together.

**Session:** set of process groups. Has a controlling terminal.

```c
setsid();    // create new session — detach from terminal (daemonize)
```

---

## /proc Filesystem

Kernel exposes process info as files:

```bash
/proc/PID/maps      # virtual memory map
/proc/PID/fd/       # open file descriptors
/proc/PID/status    # process status, memory usage
/proc/PID/cmdline   # command line arguments
cat /proc/self/maps # view your own process
```

---

## Daemon Process

A background process with no controlling terminal:

```c
pid_t pid = fork();
if (pid > 0) exit(0);    // parent exits
setsid();                 // new session, no controlling terminal
chdir("/");               // don't hold a directory open
close(STDIN_FILENO);
close(STDOUT_FILENO);
close(STDERR_FILENO);
// redirect 0,1,2 to /dev/null
// now run as daemon
```

---

## LDS Context

The C Watchdog (`ds/src/wd.c`) uses `fork()` + `execv()` to spawn the guardian process. The guardian watches the main process via SIGUSR1/SIGUSR2 ping-pong. If the main process stops responding, the guardian calls `fork()` + `execv()` to restart it.

`waitpid` with `WNOHANG` is used to check if a child exited without blocking:
```c
waitpid(child_pid, &status, WNOHANG);   // returns 0 if child still running
```
