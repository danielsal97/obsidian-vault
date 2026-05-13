# RAID01 — How It Works in LDS

## What is RAID01?

RAID01 combines mirroring (RAID1) with striping (RAID0):
- **Striping** — data is split into blocks distributed across minions (performance)
- **Mirroring** — each block is stored on exactly **2 minions** (redundancy)

Result: if any single minion dies, all data is still accessible from its replica.

---

## Block Mapping Strategy

```
Total blocks: N
Minion count: M

Block B is stored on:
  Primary   = B % M
  Replica   = (B + 1) % M

Example with 4 minions (M0, M1, M2, M3):
  Block 0  → M0 (primary), M1 (replica)
  Block 1  → M1 (primary), M2 (replica)
  Block 2  → M2 (primary), M3 (replica)
  Block 3  → M3 (primary), M0 (replica)
  Block 4  → M0 (primary), M1 (replica)  ← wraps around
```

```mermaid
graph LR
    B0["Block 0"] --> M0["Minion 0\n(primary)"]
    B0 --> M1["Minion 1\n(replica)"]
    B1["Block 1"] --> M1
    B1 --> M2["Minion 2\n(replica)"]
    B2["Block 2"] --> M2
    B2 --> M3["Minion 3\n(replica)"]
    B3["Block 3"] --> M3
    B3 --> M0
```

---

## RAID01Manager Interface

```cpp
class RAID01Manager {
public:
    // Returns (primary_id, replica_id)
    std::pair<int, int> GetBlockLocation(uint64_t block_num);

    void AddMinion(int id, const std::string& ip, int port);
    void FailMinion(int id);          // marks minion as failed
    void RecoverMinion(int id);       // marks minion healthy again

    void SaveMapping(const std::string& filepath);
    void LoadMapping(const std::string& filepath);

private:
    std::map<int, Minion> minions_;
    std::map<uint64_t, std::pair<int, int>> block_map_;
};
```

---

## Minion Status States

```mermaid
stateDiagram-v2
    [*] --> Healthy : AddMinion()
    Healthy --> Degraded : missed heartbeat
    Degraded --> Healthy : heartbeat restored
    Degraded --> Failed : timeout exceeded (15s)
    Failed --> Healthy : AutoDiscovery broadcasts
    Failed --> [*] : removed from cluster
```

---

## Failure Scenario — Single Minion Down

```
Normal:   Block 5 → Minion1 (primary) ✅, Minion2 (replica) ✅
Failure:  Minion1 goes down
Read:     ReadCommand tries Minion1 → timeout → retries Minion2 ✅
Write:    WriteCommand writes to Minion2 only (single copy, degraded mode)
Recovery: Minion1 rejoins → AutoDiscovery detects it → resync missing blocks
```

```mermaid
flowchart TD
    A[Read Block 5] --> B{Minion1 alive?}
    B -- Yes --> C[Read from Minion1]
    B -- No --> D[Timeout / Scheduler retry]
    D --> E[Read from Minion2 replica]
    E --> F[Return data to user]
    C --> F
```

---

## Data Structures

```cpp
struct Minion {
    int id;
    std::string ip;
    int port;
    enum Status { HEALTHY, DEGRADED, FAILED } status;
    time_t last_response_time;
};
```

---

## Persistence

The block map is saved to disk so the mapping survives master restarts:
- On startup: `LoadMapping("raid_map.bin")`
- On shutdown / periodic: `SaveMapping("raid_map.bin")`

---

## Related Notes
- [[RAID01 Manager]]
- [[Watchdog]]
- [[AutoDiscovery]]
- [[System Overview]]
