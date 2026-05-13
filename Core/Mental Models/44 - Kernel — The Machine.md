# Kernel — The Machine

## The Model
A trusted supervisor running in a locked room (CPU ring 0). Your process runs in the hallway (ring 3) — it cannot touch hardware directly. Every syscall is a controlled knock on the supervisor's door: you package your request, ring the bell (software interrupt), the supervisor checks your ID, executes the request in the locked room, passes the result back through a slot in the door.

## How It Moves

```
User space (ring 3)              Kernel space (ring 0)
────────────────────             ─────────────────────
write(fd, buf, n)                   
  → packs: syscall #1, args      
  → INT 0x80 / SYSCALL           
                    ────────────→ validate fd is valid
                                  validate buf is readable  
                                  copy buf to kernel buffer
                                  schedule device write
                                  return bytes_written
  ← result in rax                
```

**The mode switch cost:** ~100ns per syscall. Switching from ring 3 to ring 0 requires saving all CPU registers, changing the page table (or switching stacks), validating arguments, doing the work, restoring. This is why LDS batches operations — avoiding 1000 tiny `write()` calls per second in favor of fewer large ones.

## The Blueprint

**Virtual memory:** Every process sees its own 0→N address space. The kernel maintains a page table for each process mapping virtual → physical addresses. The same virtual address in two processes maps to different physical addresses. The same virtual address in two threads of one process maps to the SAME physical addresses (shared address space).

**Scheduling:** The kernel preempts running threads every ~4ms (default timer tick) to give other threads CPU time. Your thread can also voluntarily yield by blocking on I/O, sleeping, or waiting for a mutex — the kernel schedules another thread immediately.

**Syscall vs library call:**
- `malloc()` is a library call — runs in ring 3, no mode switch
- `brk()` (called by malloc when out of heap) is a syscall — ring 3 → ring 0 → ring 3
- `read()` is always a syscall — data comes from the kernel, cannot bypass it

**Key syscalls in LDS:**
| Syscall | Use |
|---|---|
| `epoll_wait` | Block until an fd has data |
| `accept` | Accept a TCP connection |
| `read`/`recv` | Read from socket or device |
| `write`/`send` | Write to socket or device |
| `mmap` | Map memory or files |

## Where It Breaks

- **Syscall in a tight loop**: each `write(fd, &byte, 1)` is a full mode switch — catastrophic for throughput. Buffer first.
- **Blocking syscall**: `read()` on an empty socket blocks — the kernel suspends your thread. The LDS Reactor uses `epoll` to avoid this.
- **OOM kill**: kernel kills processes when RAM is exhausted — LDS can be killed by the OOM killer if it holds large storage buffers

## In LDS

`design_patterns/reactor/src/reactor.cpp`

The entire LDS event loop revolves around `epoll_wait` — a single syscall that blocks until one or more fds are ready. This batches the mode-switch cost: instead of calling `read()` on every fd and getting `EAGAIN` (another syscall per fd), one `epoll_wait` tells you exactly which fds have data. At 1000 events/second with 100 fds, this is the difference between 100,000 syscalls/second and ~1,000.

## Validate

1. LDS calls `epoll_wait(epfd, events, 64, -1)`. The timeout is -1 (infinite). What is the kernel doing while LDS waits? Is it burning CPU?
2. `malloc(1MB)` inside LDS — does this involve a syscall? What if you call `malloc(100MB)`?
3. Two LDS worker threads access the same `LocalStorage` object simultaneously. They have different virtual addresses for their stacks. Do they share the `LocalStorage` object's physical memory? How does the kernel enforce this?

## Connections

**Theory:** [[Core/Theory/Linux/08 - Kernel]]  
**Mental Models:** [[Processes — The Machine]], [[File Descriptors — The Machine]], [[Signals — The Machine]], [[mmap — The Machine]], [[Process Memory Layout — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Reactor]] — syscall batching via epoll_wait  
**Glossary:** [[epoll]], [[VFS]], [[socketpair]]
