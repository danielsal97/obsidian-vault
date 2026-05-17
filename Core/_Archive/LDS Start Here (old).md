# Start Here — LDS Top-Down Overview

> This is the single entry point to the project. Read this first, then follow the links. Everything else is a detail of what's described here.

---

## What Is This System?

LDS (Local Drive Storage) is a **distributed NAS**. From the user's perspective it is a regular Linux block device — you mount it, read files, write files. Under the hood, every block of data is distributed across storage nodes with RAID01 redundancy.

The system is built in two layers:

**Phase 2A (active) — Client-Server link:**
A Mac client communicates with the Linux master over TCP. Real sockets, real network, two physical machines.

```
┌─────────────────────┐
│  Mac (Client)        │  ← ./ldsclient write 0 data.bin
│  C++20 BlockClient   │
└──────────┬──────────┘
           │ TCP over real network
           ▼
┌──────────────────────┐
│  Linux (Master)      │  ← LDS process, port 7800
│  TCPServer + Reactor │
│  LocalStorage        │
└──────────────────────┘
```

**Phase 2+ (planned) — RAID across minion nodes:**
```
┌──────────────────────┐
│     MASTER NODE      │  ← Linux, running LDS
│  (C++20 process)     │
└──────────┬───────────┘
           │ UDP over network
    ┌──────┴──────┐──────┐
    ▼             ▼      ▼
 Minion 1     Minion 2  Minion N
 (RPi)        (RPi)     (RPi)
 stores        stores
 blocks        replica blocks
```

---

> New to a term? → [[Glossary/Key Terms]]

---

## The Story: What Happens When You Write a File

This is the journey of a single `write()` call — top to bottom, through every layer of the system.

### Step 1 — User Space to Kernel

```
user process:  write(fd, buf, 512)
                    │
                    ▼
             Linux VFS → Block Layer
                    │
                    ▼
             NBD kernel driver
             encodes: nbd_request { WRITE, handle=0xABCD, offset=4096, len=512 }
             writes to socketpair fd
             ★ user's write() is now BLOCKED waiting for our reply ★
```

**What this means:** The Linux kernel acts as a bridge. The user writes to what looks like a disk. The NBD (Network Block Device) driver packages that write into a struct and hands it to our process through a socketpair. The user's call is blocked until we send a reply.

→ See [[NBD Layer]] and [[NBD Protocol Deep Dive]] for the kernel protocol details.

---

### Step 2 — Reactor Wakes Up

```
             socketpair fd has data
                    │
                    ▼
             Reactor (epoll loop)
             epoll_wait() fires on the NBD fd
             calls: io_handler(fd)
```

The **Reactor** is the heartbeat of the master process. It's an `epoll`-based event loop — it sits idle with zero CPU usage until an fd becomes readable, then dispatches the registered handler. It never blocks on I/O itself; it just routes events.

→ See [[Reactor]] for the epoll implementation.

---

### Step 3 — InputMediator Converts Event to Command

```
             io_handler(fd)
                    │
                    ▼
             InputMediator::HandleEvent(fd)
             reads DriverData { WRITE, handle, offset, buffer }
                    │
                    ▼
             Factory::Create("WRITE", driverData)
             → returns shared_ptr<WriteCommand>
                    │
                    ▼
             ThreadPool.Enqueue(cmd)
             ★ main thread returns to epoll immediately ★
```

**InputMediator** is the bridge between the event world (raw file descriptors) and the command world (typed objects). It reads the raw `DriverData` struct off the NBD fd, inspects the type (READ / WRITE / FLUSH / DISCONNECT), and asks the Factory to create the right command. The command is pushed to the priority queue and the main thread returns to `epoll_wait()` instantly — never blocking.

→ See [[InputMediator]], [[Factory]], [[Command]].

---

### Step 4 — ThreadPool Executes the Command

```
             ThreadPool worker thread (sleeping on WPQ)
             WPQ.Pop() → WriteCommand
                    │
                    ▼
             WriteCommand::Execute()
```

The **ThreadPool** holds N worker threads, all blocking on the **WPQ** (Waitable Priority Queue). When a command is pushed, one thread wakes and pops it. Priority matters: `WRITE (High) > READ (Med) > FLUSH (Low)` — data integrity operations run before reads.

→ See [[Utilities Framework]] for ThreadPool + WPQ details.

---

### Step 5 — RAID01Manager Finds the Minions

```
             WriteCommand::Execute()
                    │
                    ▼
             RAID01Manager::GetBlockLocation(block_num)
             primary = block_num % num_minions
             replica = (block_num + 1) % num_minions
             → returns { minionA_id, minionB_id }
```

**RAID01Manager** is pure mapping logic — no networking, no I/O. It maintains a registry of known minions (id, ip, port, status) and for any block number returns exactly two minion IDs: the primary and the replica. If a minion is marked `FAILED`, it is skipped and the next healthy one is used.

→ See [[RAID01 Manager]] and [[RAID01 Explained]].

---

### Step 6 — MinionProxy Sends UDP Packets

```
             WriteCommand::Execute() continues
                    │
                    ▼
             MinionProxy::SendPutBlock(minionA, offset, data) → msg_id_A
             MinionProxy::SendPutBlock(minionB, offset, data) → msg_id_B

             Wire format:
             [ MSG_ID: 4B ][ OP: 1B ][ OFFSET: 8B ][ LEN: 4B ][ DATA: var ]

             Fire and forget — returns immediately
```

**MinionProxy** wraps the UDP socket abstraction. It serializes the request into the wire format and fires it off — no waiting. It returns a `MSG_ID` that identifies this request. The pairing of request to response is handled separately by ResponseManager.

→ See [[MinionProxy]] and [[Wire Protocol Spec]].

---

### Step 7 — ResponseManager + Scheduler Handle the Async Response

```
             ResponseManager (background thread, blocking on recvfrom)
                    │
                    ▼
             UDP packet arrives from Minion A
             parse: [ MSG_ID=msg_id_A ][ STATUS=OK ]
             lookup callback for msg_id_A
             call callback → WriteCommand notified

             Scheduler (parallel)
             tracks msg_id_A with deadline = now + 1s
             if deadline exceeded with no response → retry
             exponential backoff: 1s → 2s → 4s, max 3 retries
             max retries exceeded → propagate error
```

**ResponseManager** listens on the master's UDP port and matches incoming packets back to pending requests using `MSG_ID`. **Scheduler** is the watchdog for individual requests — it tracks deadlines and drives retry logic independently of the main flow.

→ See [[ResponseManager]], [[Scheduler]].

---

### Step 8 — Reply Goes Back to Kernel

```
             Both ACKs received (or enough to proceed)
                    │
                    ▼
             WriteCommand calls: driver.SendReply(driverData)
             encodes: nbd_reply { magic, error=0, handle=0xABCD }
             writes to socketpair

             Kernel receives reply, matches handle 0xABCD
             ★ user's write() unblocks, returns 512 ★
```

The kernel's user process has been blocked this entire time. The moment the reply arrives on the socketpair, the kernel unblocks the `write()` call and returns the byte count to the user. If `error != 0`, the user sees `EIO`.

→ See [[Request Lifecycle]] for the complete timing diagram.

---

## System Layers (Top-Down)

The system is organized into three layers. Each layer depends only on the one below — never upward.

```
┌────────────────────────────────────────────────────────────────┐
│  LAYER 3: APPLICATION                                          │
│  app/LDS.cpp — wires all components, starts the system         │
│  Plugins — dynamically loaded .so files for extensibility      │
└────────────────────────────────────────────────────────────────┘
                              ▲ uses
┌────────────────────────────────────────────────────────────────┐
│  LAYER 2: FRAMEWORK                                            │
│  Business logic + design patterns                              │
│                                                                │
│  Event routing:   Reactor, Dispatcher, CallBack                │
│  Command system:  ICommand, Factory, ThreadPool + WPQ          │
│  Storage logic:   RAID01Manager, InputMediator                 │
│  Network:         MinionProxy, ResponseManager, Scheduler      │
│  Reliability:     Watchdog, AutoDiscovery                      │
│  Observability:   Logger (Singleton)                           │
└────────────────────────────────────────────────────────────────┘
                              ▲ uses
┌────────────────────────────────────────────────────────────────┐
│  LAYER 1: OS / LINUX APIs                                      │
│  epoll, inotify, dlopen/dlclose, pthreads, UDP sockets,        │
│  socketpair AF_UNIX, ioctl(NBD_*), signalfd                    │
└────────────────────────────────────────────────────────────────┘
```

→ See [[Three-Tier Architecture]] for detail.

---

## All Components — Where They Live and What They Do

### Phase 1 — Core Framework

> ✅ = built | ❌ = not yet built

| Component | Actual path | Status | Role |
|-----------|------------|--------|------|
| [[Reactor]] | `design_patterns/reactor/` | ✅ | epoll event loop — entry point for all I/O |
| [[NBDDriverComm]] | `services/communication_protocols/nbd/` | ✅ | Reads nbd_request, writes nbd_reply to kernel |
| [[LocalStorage]] | `services/local_storage/` | ✅ | In-memory storage backend |
| [[InputMediator]] | `services/mediator/` | ✅ | Reads DriverData, dispatches READ/WRITE/FLUSH/TRIM/DISCONNECT to LocalStorage |
| [[Logger]] | `utilities/logger/` | ✅ | Thread-safe centralized logging |
| [[Utilities Framework\]] | `utilities/threading/` | ✅ | Priority-ordered async execution |
| [[Factory]] | `design_patterns/factory/` | ✅ | Creates commands and plugins by name at runtime |
| [[Command]] | `design_patterns/command/` | ✅ | Abstract `ICommand` interface + priority enum |
| [[Singleton]] | `design_patterns/singleton/` | ✅ | Safe global instances — note: filename is `singelton.hpp` (typo baked in) |
| [[Observer]] | `design_patterns/observer/` | ✅ | `Dispatcher<T>` + `CallBack<T,Sub>` for event routing |
| [[DirMonitor]] | `plugins/` | ✅ | inotify wrapper — detects new `.so` plugin files |
| [[PNP]] | `plugins/` | ✅ | Orchestrates DirMonitor → soLoader → Factory |
| ReadCommand / WriteCommand | `services/commands/` | ❌ | Phase 2 — needed when writes fan out to multiple minions via ThreadPool. Currently handled as lambdas inside InputMediator. |

### Phase 2A — Mac Client TCP Bridge (⏳ Active)

| Component | Actual path | Status | Role |
|-----------|------------|--------|------|
| Reactor upgrade | `design_patterns/reactor/` | ❌ not built | Per-fd handler map — enables dynamic client fd registration |
| NetworkProtocol | `services/network/include/` | ❌ not built | Shared wire format structs used by both sides |
| [[Components/TCPServer\]] | `services/network/` | ❌ not built | Linux-side TCP listener; accepts clients, routes through LocalStorage |
| [[Components/BlockClient\]] | `client/` | ❌ not built | Mac-side TCP client: Connect / Read / Write |

### Phase 2 — Data Management & Network (⏳ Pending)

| Component | Planned path | Status | Role |
|-----------|-------------|--------|------|
| [[RAID01 Manager]] | `services/storage/` | ❌ not built | Maps block numbers → {primary, replica} minion IDs |
| [[MinionProxy]] | `services/network/` | ❌ not built | Serializes and sends UDP packets to minions |
| [[ResponseManager]] | `services/network/` | ❌ not built | Receives UDP responses, fires callbacks by MSG_ID |
| [[Scheduler]] | `services/execution/` | ❌ not built | Tracks deadlines, drives retry + exponential backoff |

### Phase 3 — Reliability (⏳ Pending)

| Component | Planned path | Status | Role |
|-----------|-------------|--------|------|
| [[Watchdog]] | `services/health/` | ❌ not built | Pings minions every 5s, marks FAILED after 15s silence |
| [[AutoDiscovery]] | `services/discovery/` | ❌ not built | Listens for minion UDP broadcasts, triggers rebalance |

### Phase 4 — Minion Server (⏳ Pending)

| Component | Planned path | Status | Role |
|-----------|-------------|--------|------|
| MinionServer | `minion/` | ❌ not built | Runs on each RPi — handles GET/PUT/DELETE over UDP |

---

## How LDS.cpp Is Wired — Now vs Target

### NOW — Current `app/LDS.cpp` (Phase 1 complete)

This is the actual code running today. InputMediator handles dispatch; LocalStorage is the backend:

```cpp
// Current LDS.cpp — what actually exists
LocalStorage  storage(size);
NBDDriverComm driver(device, size);
InputMediator mediator(&driver, &storage);  // routes READ/WRITE/FLUSH/TRIM/DISCONNECT
Reactor       reactor;

reactor.Add(driver.GetFD());
reactor.SetHandler([&](int fd) { mediator.Notify(fd); });
reactor.Run();
```

**What's being added in Phase 2A:** TCPServer + per-fd Reactor upgrade. The single Reactor loop will handle both the NBD fd and TCP client fds.

---

### PHASE 2A TARGET — After TCPServer + Reactor Upgrade

```cpp
LocalStorage  storage(size);
NBDDriverComm driver(device, size);
InputMediator mediator(&driver, &storage);
TCPServer     tcp_server(7800, reactor, storage);
Reactor       reactor;

// Each fd gets its own handler — no more global SetHandler
reactor.Add(driver.GetFD(),           [&](int fd){ mediator.Notify(fd); });
reactor.Add(tcp_server.GetListenFD(), [&](int fd){ tcp_server.OnAccept(fd); });
// tcp_server.OnAccept() calls reactor.Add(client_fd, ...) dynamically

reactor.Run();   // one epoll loop handles NBD + all TCP clients
```

---

### TARGET — Full LDS.cpp (Phases 1–3 complete)

This is what LDS.cpp will look like when all phases are done.
> Confused by the C++? → [[Engineering/main() Wiring Explained]]

```cpp
// Infrastructure
NBDDriverComm   driver(device, size);
Reactor         reactor;

// Phase 2: Storage + Network
RAID01Manager   raid;
raid.AddMinion(0, "192.168.1.10", 9000);
raid.AddMinion(1, "192.168.1.11", 9000);
ResponseManager response_mgr(MASTER_UDP_PORT);
Scheduler       scheduler(response_mgr);
MinionProxy     proxy(raid, scheduler);

// Command routing (Phase 1 wiring)
auto& factory = Singleton<CommandFactory>::GetInstance();
factory.Add("READ",  [&](DriverData d){ return make_shared<ReadCommand>(d, raid, proxy, scheduler); });
factory.Add("WRITE", [&](DriverData d){ return make_shared<WriteCommand>(d, raid, proxy, scheduler); });
factory.Add("FLUSH", [&](DriverData d){ return make_shared<FlushCommand>(d); });

ThreadPool      pool(std::thread::hardware_concurrency());
InputMediator   mediator(pool, factory, driver);

// Phase 3: Reliability
Watchdog        watchdog(proxy, raid);
AutoDiscovery   discovery(raid);

// Start
reactor.Add(driver.GetFD());
reactor.SetHandler([&](int fd){ mediator.HandleEvent(fd); });
reactor.Run();
```

---

## Data Flow Summary

```
                     USER: write(fd, data)
                              │
                         [KERNEL: NBD]
                              │ socketpair
                         [REACTOR: epoll]
                              │ event fires
                     [INPUT MEDIATOR]
                        │         │
                  Factory::Create("WRITE")
                        │
               [THREAD POOL / WPQ]
                  worker picks up
                        │
               [WRITE COMMAND::Execute()]
                        │
               [RAID01 MANAGER]
               GetBlockLocation(N)
               → (primary, replica)
                    │         │
             [MINION PROXY]  [MINION PROXY]
             SendPutBlock(A)  SendPutBlock(B)
                    │               │
             [UDP → Minion A] [UDP → Minion B]
                    │               │
             [RESPONSE MANAGER receives ACKs]
                    │
             [SCHEDULER clears deadlines]
                    │
             [WRITE COMMAND calls SendReply]
                              │ socketpair
                     [KERNEL: unblocks write()]
                              │
                       USER: write() returns
```

---

## Build Order

| Phase | Link | Status |
|---|---|---|
| Phase 1 — Core Framework | [[Phase 1 - Core Framework Integration]] | ✅ Done |
| Phase 2A — Mac Client TCP Bridge | [[Phase 2A - Mac Client TCP Bridge]] | ⏳ Active |
| Phase 2 — Data Management & Network | [[Phase 2 - Data Management & Network]] | ⏳ Pending |
| Phase 3 — Reliability | [[Phase 3 - Reliability Features]] | ⏳ Pending |
| Phase 4 — Minion Server | [[Phase 4 - Minion Server]] | ⏳ Pending |

→ [[00 Dashboard]] — full status and hour estimates

---

## Design Decisions (The "Why")

| Decision | Reason |
|----------|--------|
| UDP not TCP | [[Why UDP not TCP]] |
| RAID01 (mirroring) not RAID0 (striping) | Survive minion failure without data loss |
| epoll (Reactor) not blocking I/O | Single main thread handles all events without sleeping |
| Commands + ThreadPool not inline execution | Main thread never blocks; prioritized execution |
| Fire-and-forget UDP + ResponseManager | Decouples send from receive; enables async retry |
| Templates not virtual functions (Observer, Factory) | [[Why Templates not Virtual Functions]] |
| RAII everywhere | [[Why RAII]] |
| Observer (Dispatcher) not direct calls | [[Why Observer Pattern]] |
| Plugin system (.so + dlopen) | Add features at runtime without recompile |

---

## Current Status (as of 2026-05-06)

### ✅ Done
- Phase 1 — Core Framework (Reactor, NBD, ThreadPool, Factory, Observer, Command, Plugin system, InputMediator, Logger)

### 🔴 Important — Do These
| What | Why |
|---|---|
| Fix bugs #3, #8, #10 | Correctness blockers |
| Phase 2A — TCP demo (Mac↔Linux) | Cross-machine networking story for CV |
| README | First thing interviewer sees on GitHub |
| gtest on 2-3 tests | Signals professional, not student |
| GitHub Actions CI | Green checkmark on every commit |

### 🟡 Nice to Add
| What | Why |
|---|---|
| Watchdog (wire in the C version) | Adds reliability story, already built in C |
| MinionProxy + UDP | Adds distributed systems depth |
| AddressSanitizer clean run | Memory safety signal, 1 hr |

### ⚪ Skip
RAID01Manager, ResponseManager, LDS Scheduler, AutoDiscovery, Minion Server — describe the design in interviews, not worth the time to implement before job search.

**Immediate next step:** Fix bugs #3, #8, #10 → Reactor upgrade → TCPServer + BlockClient  
See: [[Phase 2A Execution Plan]]

---

## Navigation

| Goal | Go To |
|------|-------|
| Understand the full system | [[System Overview]] |
| Trace a single request step-by-step | [[Request Lifecycle]] |
| Understand the layered architecture | [[Three-Tier Architecture]] |
| See what's done and what's next | [[Roadmap]] |
| Open bugs blocking progress | [[Known Bugs]] |
| **Active sprint plan (Phase 2A)** | **[[Phase 2A Execution Plan]]** |
| Mac ↔ Linux TCP architecture | [[Architecture/Client-Server Architecture]] |
| Why TCP for the client link | [[Decisions/Why TCP for Client]] |
| TCPServer component | [[Components/TCPServer]] |
| BlockClient component | [[Components/BlockClient]] |
| NBD + kernel interface | [[NBD Layer]], [[NBD Protocol Deep Dive]] |
| RAID01 algorithm | [[RAID01 Explained]] |
| Concurrency model | [[Concurrency Model]] |
| Wire protocol (UDP, for minions) | [[Wire Protocol Spec]] |
| All component notes | [[Components/]] |
| All design pattern notes | [[Design Patterns/]] |
| UML diagrams | [[UML/]] |

---

## Where to Go Next

→ [[00 Dashboard]] — full project status and phase timeline  
→ [[Phase 2A Execution Plan]] — active sprint: bug fixes, Reactor upgrade, TCPServer, BlockClient  
→ [[Known Bugs]] — bugs #3, #8, #10 must be fixed first
