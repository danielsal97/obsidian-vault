# State Diagram — Minion Lifecycle

## States

```mermaid
stateDiagram-v2
    [*] --> Discovering : minion process starts

    Discovering --> Connected : UDP handshake with master
    Discovering --> Discovering : broadcast not heard

    Connected --> Active : first health check passes
    Connected --> Discovering : connection reset

    Active --> Degraded : 1 missed Watchdog ping
    Active --> Active : normal operation

    Degraded --> Active : PONG received within 5s
    Degraded --> Failed : no response > 15s

    Failed --> Discovering : minion restarts & broadcasts
    Failed --> Failed : master waits

    Active --> Rebalancing : new minion joined cluster
    Rebalancing --> Active : rebalancing complete
```

---

## State Descriptions

| State | Meaning | Impact on I/O |
|---|---|---|
| **Discovering** | Broadcasting Hello, waiting for master | No I/O |
| **Connected** | Master knows about minion | No I/O yet |
| **Active** | Fully operational, passes health checks | Reads + writes |
| **Degraded** | Missed a ping, might be slow | Still used, monitored closely |
| **Failed** | No response for 15s | Excluded from all I/O |
| **Rebalancing** | Receiving blocks from other minions | Limited I/O (background copy) |

---

## Watchdog Perspective

```mermaid
sequenceDiagram
    participant WD as Watchdog
    participant RAID as RAID01Manager
    participant M as Minion

    loop every 5 seconds
        WD->>M: PING
        alt Minion responds
            M-->>WD: PONG
            WD->>RAID: RecoverMinion(id)  [if was degraded]
        else No response within 5s
            WD->>WD: increment missed_count
            WD->>RAID: MarkDegraded(id)
        else 15s total silence
            WD->>RAID: FailMinion(id)
            Note over RAID: All blocks on this minion<br/>rerouted to replicas
        end
    end
```

---

## Master Perspective on Minion States

```mermaid
flowchart TD
    A["Minion Status: ACTIVE"] -->|read/write| B["Use as primary"]
    C["Minion Status: DEGRADED"] -->|read| D["Use but log warning"]
    C -->|write| E["Write + increase retry budget"]
    F["Minion Status: FAILED"] -->|read| G["Skip — use replica"]
    F -->|write| H["Skip — write to replica only"]
```
