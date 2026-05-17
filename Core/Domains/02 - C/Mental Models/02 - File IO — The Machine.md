# File IO — The Machine

## The Model
A numbered pipe between your process and a kernel resource. You hold a ticket (the file descriptor integer). The kernel holds the actual resource. Every operation — read, write, seek — goes through the ticket. The kernel buffers data on both sides so you don't pay a full disk seek for every byte.

## How It Moves

```
Your process                 Kernel                    Disk/Network
───────────                  ──────                    ───────────
fwrite(buf, 1, n, fp) ──→  [stdio buffer]
                                │ (when full or fflush)
                                ↓
                           write(fd, ...) ──→  [kernel page cache]
                                                      │ (async, when dirty)
                                                      ↓
                                                   actual disk write

fread(buf, 1, n, fp) ←──  [stdio buffer]
                                ↑ (when empty)
                           read(fd, ...) ←──   [kernel page cache]
                                                      ↑ (if not cached)
                                                   disk read
```

**TWO levels of buffering:**
1. **stdio buffer** (userspace, inside your process): `fread/fwrite` batch operations here before hitting the kernel
2. **Kernel page cache**: the kernel buffers disk data in RAM — repeated reads of the same file are served from RAM

**WHY buffering:** Each `write()` syscall costs ~100ns (mode switch to ring 0). Writing one byte at a time would make 1 million syscalls for 1MB. Buffering batches them into a few large calls.

## The Blueprint

```c
// Buffered (stdio) — higher level:
FILE* f = fopen("data.bin", "rb");
fread(buf, sizeof(char), 1024, f);
fwrite(buf, sizeof(char), 1024, f);
fflush(f);     // force stdio buffer → kernel now
fclose(f);     // flush + close fd

// Unbuffered (POSIX) — direct syscall:
int fd = open("data.bin", O_RDONLY);
ssize_t n = read(fd, buf, 1024);   // returns bytes actually read (may be < 1024)
write(fd, buf, 1024);
close(fd);
```

**`read()` may return less than asked** — always loop:
```c
ssize_t total = 0;
while (total < n) {
    ssize_t r = read(fd, buf + total, n - total);
    if (r <= 0) break;
    total += r;
}
```

## Where It Breaks

- **Ignoring return value of `read()`**: partial reads are normal on sockets and slow disks
- **Not `fflush`ing**: data sits in stdio buffer — appears lost on crash, or out of order in logs
- **File descriptor leak**: `open()` without `close()` — process runs out of fds (default limit ~1024)
- **`fclose` on NULL**: instant crash — always check `fopen` return value

## In LDS

`services/communication_protocols/tcp/src/TCPDriverComm.cpp`

`TCPDriverComm::RecvAll` uses `recv()` (the socket version of `read()`) in a loop — exactly because a single `recv()` may return fewer bytes than the full NBD header (28 bytes). The loop accumulates bytes until the full message is received. This is the direct application of the "read() may return less" rule.

## Validate

1. LDS calls `recv(fd, buf, 28, 0)` to read an NBD header. The kernel has only 10 bytes ready. What does `recv` return, and what is `RecvAll`'s next action?
2. You use `fprintf` to log every request in LDS. The process crashes. Some log entries are missing. Why, and how do you fix it?
3. `open()` returns fd=7 for a socket. Your process spawns a child with `fork()`. The child also has fd=7. They both call `close(7)`. What happens?

## Connections

**Theory:** [[05 - File IO]]  
**Mental Models:** [[File Descriptors — The Machine]], [[mmap — The Machine]], [[RAII — The Machine]], [[Kernel — The Machine]]  
**LDS Implementation:** [[LDS/Linux Integration/TCPServer]] — RecvAll loop  
**Runtime Machines:** [[LDS/Runtime Machines/TCPDriverComm — The Machine]]
