# IPC Overview — The Machine

## The Model
Five pipes connecting processes, each built for a different distance and volume. Pipe: a narrow hallway between parent and child. Named pipe: a hallway any process can find by name. Socket: a full telephone line — works across the network. Shared memory: a shared room (no pipe needed). Message queue: a PO box with priority sorting.

## How It Moves

```
PIPE (anonymous):
  parent ──write──→ [kernel buffer, 65KB] ──read──→ child only
  one-directional, only between related processes

NAMED PIPE (FIFO):
  /tmp/lds_cmd  ←── any process can open by path
  still one-directional, same kernel buffer

SOCKET (Unix domain):
  /tmp/lds.sock ←── any process, bi-directional
  same API as TCP socket but stays in kernel (no network stack)
  fastest IPC for local processes after shared memory

SHARED MEMORY:
  two processes map same physical page — reads/writes are instant
  requires external synchronization (semaphore)
  fastest possible IPC — zero copies

MESSAGE QUEUE (POSIX):
  /lds_queue ←── named, persists after process exit
  supports message priorities
  messages delivered atomically (not fragmented like pipes)
```

## The Blueprint

| Mechanism | Latency | Bandwidth | Direction | Sync needed |
|---|---|---|---|---|
| Pipe | Low | Medium | One-way | No (blocks naturally) |
| Unix socket | Low | High | Both ways | No |
| TCP socket | Medium | High | Both ways | No |
| Shared memory | Minimal | Maximum | Both ways | Yes (semaphore/mutex) |
| Message queue | Low | Medium | Both ways | No (atomic messages) |

**When to use each:**
- Same machine, same user: Unix domain socket (simplest, no network overhead)
- Need zero-copy for large data: shared memory
- Need to span machines: TCP socket
- Simple parent→child data flow: pipe (or just use threads)
- LDS manager → minion: TCP (reliable, same API as remote minions)

## Where It Breaks

- **Pipe capacity**: pipe buffers are ~64KB. Writer blocks if full; reader blocks if empty. Deadlock if both processes try to write before reading.
- **Unix socket vs TCP**: Unix socket is 2-3x faster (no IP/TCP headers) but only works locally. LDS uses TCP to keep the same code path for local and remote minions.
- **Shared memory without synchronization**: the fastest way to corrupt data.

## In LDS

`services/communication_protocols/tcp/src/TCPDriverComm.cpp`

LDS chose TCP sockets for both the NBD-replacement interface and minion communication. TCP was chosen over Unix sockets to keep the minion protocol identical whether minions are local or remote — the same `TCPDriverComm` code works for both cases. This is the Strategy pattern at the architecture level: the TCP transport is interchangeable with a future Unix socket transport by swapping the driver.

## Validate

1. LDS manager and a local minion are on the same machine. You switch from TCP to Unix domain sockets. What changes in the code? What gets faster?
2. A pipe has 64KB kernel buffer. LDS writes 128KB in one write. What happens?
3. You use shared memory for manager-minion communication. Manager writes 512 bytes, then sets a flag. Minion polls the flag, then reads 512 bytes. What synchronization guarantee do you need and why?

## Connections

**Theory:** [[Core/Theory/Networking/IPC Overview]]  
**Mental Models:** [[TCP Sockets — The Machine]], [[UDP Sockets — The Machine]], [[Shared Memory — The Machine]], [[Semaphores — The Machine]], [[File Descriptors — The Machine]]  
**LDS Implementation:** [[LDS/Architecture/Concurrency Model]], [[LDS/Linux Integration/TCPServer]]  
**Glossary:** [[TCP]], [[UDP]], [[socketpair]]
