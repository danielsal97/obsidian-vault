# LDS System — The Machine

## The Model
A distributed block device factory. On one end: the Linux kernel hands you raw read/write requests. On the other end: Raspberry Pi nodes store the actual bytes. In the middle: a pipeline that receives requests, prioritizes them, distributes data to two storage nodes simultaneously (RAID01), and sends back acknowledgments — all without blocking the kernel.

## How It Moves

```
KERNEL
  write(fd, buf, 512)
       │ socketpair / TCP socket
       ▼
┌──────────────────────────────────────────────────────┐
│  REACTOR (main thread — never blocks)                │
│  epoll_wait → m_io_handler(fd)                       │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  INPUTMEDIATOR                                       │
│  ReceiveRequest() → DriverData{WRITE, offset, buf}   │
│  m_handlers[WRITE](data) → push to ThreadPool WPQ    │
└──────────────────────┬───────────────────────────────┘
                       │ (main thread returns to epoll)
                       ▼
┌──────────────────────────────────────────────────────┐
│  THREADPOOL (N worker threads)                       │
│  WPQ.Pop() → Execute()                               │
│  Priority: WRITE(Admin) > READ(High) > FLUSH(Med)    │
└───────────┬────────────────────────────┬─────────────┘
            │ Phase 1                    │ Phase 2+
            ▼                            ▼
┌───────────────────┐       ┌────────────────────────┐
│  LocalStorage     │       │  RAID01Manager         │
│  memcpy to        │       │  GetBlockLocation()     │
│  m_storage vector │       │  → (minionA, minionB)  │
└───────────┬───────┘       └────────────┬───────────┘
            │                            │ UDP
            ▼                            ▼
┌───────────────────┐       ┌────────────────────────┐
│  IDriverComm      │       │  MinionProxy           │
│  SendReply()      │       │  sendto() × 2          │
│  ← kernel unblocks│       │  wait for both ACKs    │
└───────────────────┘       └────────────────────────┘
```

## The Two Modes

**Phase 1 (current):**
- Driver: `NBDDriverComm` (kernel socketpair) OR `TCPDriverComm` (network clients)
- Storage: `LocalStorage` (in-memory vector)
- Single process, single machine

**Phase 2+ (target):**
- Storage: `RAID01Manager` → 2 Raspberry Pi minions per block
- UDP for minion commands with MSG_ID + retry
- Multiple threads: main (Reactor) + N workers + 1 receiver

## The Five Design Decisions

| Decision | What was chosen | Why |
|---|---|---|
| I/O model | epoll Reactor (single thread) | No per-connection thread overhead — scales to thousands |
| Work execution | ThreadPool + WPQ | Priority ordering, parallel execution, non-blocking Reactor |
| Storage abstraction | `IStorage` interface | Swap LocalStorage for RAID01Manager without changing Reactor |
| Transport abstraction | `IDriverComm` interface | Same Mediator works with NBD kernel interface or TCP clients |
| Reliability layer | MSG_ID + ResponseManager | UDP fire-and-forget + application-level ack instead of TCP per-minion |

## In LDS Code

Entry point: `app/LDS.cpp` (or equivalent main)
```
main() creates:
  NBDDriverComm driver(deviceName, storageSize)   ← or TCPDriverComm(port)
  LocalStorage  storage(storageSize)              ← or RAID01Manager
  InputMediator mediator(&driver, &storage)
  Reactor       reactor
  
  reactor.Add(driver.GetFD())
  reactor.SetHandler([&mediator](int fd){ mediator.Notify(fd); })
  reactor.Run()   ← blocks here until SIGINT/SIGTERM
```

## Validate

1. The kernel sends a WRITE request. Trace exactly which objects are touched and in which order, naming the method called at each step.
2. The Reactor is single-threaded but LDS handles requests concurrently. How?
3. `IDriverComm` and `IStorage` are both interfaces. What does this enable that concrete types would not?

---

## Core Vault Cross-Links

→ [[Linux Runtime — The Machine]] — the full kernel subsystem map behind this pipeline
→ [[Networking Stack — The Machine]] — NIC DMA → epoll → the Reactor you just traced
→ [[Concurrency Runtime — The Machine]] — thread lifecycle behind the ThreadPool
→ [[00 - Traversal Paths]] — 5 explicit runtime walks through this system
