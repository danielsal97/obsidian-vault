# System Overview — LDS Architecture

## What is LDS?

LDS (Local Drive Storage) is a distributed NAS (Network-Attached Storage) system built on top of Raspberry Pis acting as storage nodes. From the user's perspective it looks like a regular Linux disk — you can mount it and read/write files normally. Under the hood, data is split across multiple "minion" nodes with RAID01 redundancy.

---

## Master-Minion Model

```
┌───────────────────────────────────────────────┐
│                   MASTER NODE                 │
│                                               │
│  Linux NBD ──→ Reactor ──→ InputMediator      │
│                               │               │
│                         ThreadPool (WPQ)       │
│                               │               │
│              ┌────────────────┴──────────┐    │
│              │                           │    │
│         ReadCommand              WriteCommand  │
│              │                           │    │
│         RAID01Manager ←──────────────────┘    │
│              │                                │
│         MinionProxy ←──→ ResponseManager      │
│              │                                │
│         Scheduler (retry/timeout)             │
│              │                                │
│    Watchdog  │   AutoDiscovery               │
└──────────────┼────────────────────────────────┘
               │ UDP
    ┌──────────┼───────────────────┐
    │          │                   │
┌───▼───┐  ┌──▼────┐  ┌──────────▼┐
│Minion1│  │Minion2│  │ Minion N  │
│ RPi   │  │ RPi   │  │ RPi       │
└───────┘  └───────┘  └───────────┘
```

---

## How a Write Request Flows

```mermaid
sequenceDiagram
    participant User
    participant NBD as Linux NBD
    participant Reactor
    participant IM as InputMediator
    participant WC as WriteCommand
    participant RAID as RAID01Manager
    participant MP as MinionProxy
    participant M1 as Minion A
    participant M2 as Minion B

    User->>NBD: write(offset, data)
    NBD->>Reactor: fd event
    Reactor->>IM: OnNBDEvent(DriverData)
    IM->>WC: create WriteCommand
    IM->>IM: enqueue to ThreadPool WPQ
    WC->>RAID: GetBlockLocation(block_num)
    RAID-->>WC: (minionA, minionB)
    WC->>MP: SendPutBlock(minionA, data)
    WC->>MP: SendPutBlock(minionB, data)
    MP->>M1: UDP packet
    MP->>M2: UDP packet
    M1-->>MP: ACK
    M2-->>MP: ACK
    WC-->>NBD: write complete
```

---

## How a Read Request Flows

```mermaid
sequenceDiagram
    participant User
    participant NBD
    participant RC as ReadCommand
    participant RAID as RAID01Manager
    participant MP as MinionProxy
    participant M1 as Primary Minion
    participant M2 as Replica Minion

    User->>NBD: read(offset, length)
    NBD->>RC: execute
    RC->>RAID: GetBlockLocation(block_num)
    RAID-->>RC: (primary, replica)
    RC->>MP: SendGetBlock(primary, offset, length)
    MP->>M1: UDP request
    alt Primary responds
        M1-->>RC: data
        RC-->>NBD: return data
    else Primary fails / timeout
        RC->>MP: SendGetBlock(replica, offset, length)
        MP->>M2: UDP request
        M2-->>RC: data
        RC-->>NBD: return data
    end
```

---

## Component Responsibilities (Summary)

| Component | Layer | Does What |
|---|---|---|
| **Reactor** | Core | epoll event loop — drives all I/O |
| **InputMediator** | Phase 1 | Converts NBD events → ICommand objects |
| **ThreadPool + WPQ** | Core | Executes commands concurrently with priority |
| **ReadCommand** | Phase 1 | Fetches block from primary (or replica) minion |
| **WriteCommand** | Phase 1 | Writes block to 2 minions (RAID01) |
| **RAID01Manager** | Phase 2 | Maps block numbers → (minionA, minionB) |
| **MinionProxy** | Phase 2 | UDP socket abstraction for each minion |
| **ResponseManager** | Phase 2 | Matches async UDP responses to pending requests |
| **Scheduler** | Phase 2 | Timeout tracking + exponential backoff retry |
| **Watchdog** | Phase 3 | Pings minions every 5s, marks failed after 15s |
| **AutoDiscovery** | Phase 3 | Listens for UDP broadcasts from new/rejoining minions |
| **MinionServer** | Phase 4 | Runs on each Raspberry Pi, handles GET/PUT/DELETE |

---

## Key Design Principles

1. **Non-blocking I/O** — Reactor + epoll handles thousands of connections without blocking threads
2. **Priority queuing** — Write (Admin) > Read (High) > Flush (Med) in the WPQ
3. **Fire-and-forget UDP** — MinionProxy sends and returns a MSG_ID; ResponseManager handles replies asynchronously
4. **RAID01** — Every block stored on exactly 2 minions; survives any single minion failure
5. **Plugin extensibility** — New functionality added as `.so` plugins, auto-loaded by DirMonitor + PNP

---

## Related Notes
- [[RAID01 Explained]]
- [[NBD Layer]]
- [[Class Diagram - Full System]]
- [[Reactor]]
