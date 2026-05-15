# LDS RAID01Manager — The Machine

## The Model
A shipping manager with a strict redundancy rule: every package must be delivered to exactly two warehouses simultaneously (Raspberry Pi minions). On the wall is a routing chart (`GetBlockLocation()`) — for any block number, it maps to a primary minion and a replica. For writes: both warehouses receive the package in parallel, and the manager waits for both acknowledgment stamps before telling the sender it's done. For reads: ask the primary; if it doesn't respond, ask the replica. The manager speaks UDP — fast, connectionless, but with an envelope numbering system (`MSG_ID`) to know when an ACK matches the original request.

## How It Moves

```
Write(data_):
  [block, replica] = GetBlockLocation(data_->m_offset)
    ← maps offset → two minion addresses (e.g., minion A and minion B)
  
  MinionProxy::Send(block, data_->m_buffer, MSG_ID) → minion_A   ← sendto() UDP
  MinionProxy::Send(block, data_->m_buffer, MSG_ID) → minion_B   ← sendto() UDP
  
  wait for ACK from minion_A   ← ResponseManager matches MSG_ID
  wait for ACK from minion_B   ← both must ACK before returning
  
  data_->m_status = SUCCESS
  ← caller (Mediator handler) then calls SendReply() to the kernel

Read(data_):
  [primary, replica] = GetBlockLocation(data_->m_offset)
  
  MinionProxy::Send(READ request, MSG_ID) → primary
  if ACK received within timeout:
    data_->m_buffer = ACK payload
    return
  else:
    MinionProxy::Send(READ request, MSG_ID) → replica   ← fallback
    data_->m_buffer = replica ACK payload

GetBlockLocation(offset_):
  block_num = offset_ / BLOCK_SIZE
  primary_idx = block_num % num_minions          ← striping
  replica_idx = (primary_idx + 1) % num_minions  ← next minion is always replica
  return {m_minions[primary_idx], m_minions[replica_idx]}
```

**RAID01 = Stripe + Mirror:**
Each block is mirrored to 2 minions. With N minions, block 0 → minion 0 + minion 1, block 1 → minion 1 + minion 2, block 2 → minion 2 + minion 3 (wrapping). This is RAID01: striped across minion pairs, each pair is a mirror. One minion can die — its partner serves all reads and buffers writes until the failed minion recovers.

**MSG_ID reliability on UDP:**
UDP is fire-and-forget. To get reliability, each message gets a unique `MSG_ID`. The `ResponseManager` sits in a background receiver thread, listening for UDP packets. When a packet arrives, it looks up the `MSG_ID` in a pending-request map and unblocks the waiting thread. If no ACK arrives within a timeout, the sender retries with the same `MSG_ID` (idempotent — minion ignores duplicate MSG_IDs it's already processed).

**MinionProxy:**
One `MinionProxy` per minion (IP:port pair). Wraps the UDP socket with `sendto()`. Handles the wire format: MSG_ID + block number + data payload. The manager creates one proxy per minion address at construction.

## The Blueprint

```cpp
// (Phase 2 — not fully implemented in current codebase)
// Conceptual structure based on LDS architecture and RAIDManager.hpp:

class RAID01Manager : public IStorage {
    struct MinionInfo { std::string ip; int port; };
    std::vector<MinionInfo> m_minions;
    ResponseManager m_responseManager;   // background receiver thread
    
    std::pair<MinionInfo, MinionInfo> GetBlockLocation(size_t offset) const;

public:
    RAID01Manager(std::vector<MinionInfo> minions);
    void Read(std::shared_ptr<DriverData> data_) override;
    void Write(std::shared_ptr<DriverData> data_) override;
};

// GetBlockLocation — block striping + mirror:
std::pair<...> RAID01Manager::GetBlockLocation(size_t offset) const {
    size_t block = offset / BLOCK_SIZE;
    size_t primary = block % m_minions.size();
    size_t replica = (primary + 1) % m_minions.size();
    return {m_minions[primary], m_minions[replica]};
}

// MinionProxy::Send — UDP fire:
void MinionProxy::Send(size_t block, const std::vector<char>& data, uint32_t msg_id) {
    RequestPacket pkt{msg_id, block, data};
    // MSG_ID is uint32_t (4 bytes) — matches wire format [MSG_ID:4B] and ResponseManager map
    sendto(m_sock_fd, &pkt, sizeof(pkt), 0, (sockaddr*)&m_addr, sizeof(m_addr));
}

// ResponseManager — background thread waiting for ACKs:
void ResponseManager::ReceiverThread() {
    while (true) {
        recvfrom(m_sock_fd, &ack, sizeof(ack), 0, ...);
        m_pending[ack.msg_id].promise.set_value(ack);  // unblocks waiting thread
    }
}
```

**Phase 2 status:** `services/local_storage/include/RAIDManager.hpp` exists as a 1-line stub. The architecture is designed, the interface (`IStorage*`) is ready — implementation is Phase 2 work. `LocalStorage` is the Phase 1 stand-in.

## Where It Breaks

- **Network partition**: both minions unreachable → `Write` waits for ACK forever (or until timeout). Add a write timeout + dead-letter queue to handle node failures without blocking the main pipeline.
- **Primary ACKs, replica doesn't**: manager gets one ACK, waits for second, timeout fires. Storage is now inconsistent — primary has new data, replica has old. Need a reconciliation protocol (replica sync on recovery).
- **UDP packet reorder**: ACK from request N-1 arrives after ACK from request N due to network reorder. `ResponseManager` must match by `MSG_ID`, not by arrival order.
- **RAID01 with 2 minions**: block 0 → minion 0 + minion 1, block 1 → minion 1 + minion 0 (same two!). Every block goes to both minions — effectively a full mirror with no striping benefit. RAID01 needs N ≥ 4 for meaningful striping.
- **Hot spot**: last minion in the array holds a replica of every "last block" for its position. Uneven write distribution possible depending on access patterns.

## In LDS

`services/local_storage/include/RAIDManager.hpp` (stub), `src/RAIDManager.cpp` (stub)

The `IStorage` interface was designed specifically to allow this swap:
```cpp
// Phase 1 (today):
LocalStorage storage(storageSize);
InputMediator mediator(&driver, &storage);   // IStorage* m_storage = &storage

// Phase 2 (when RAIDManager implemented):
RAID01Manager storage({{minion1_ip, 8800}, {minion2_ip, 8800}});
InputMediator mediator(&driver, &storage);   // identical line
```

`InputMediator::SetupHandlers()` calls `m_storage->Write(request)` — the vtable dispatch routes to `LocalStorage::Write` or `RAID01Manager::Write` transparently.

## Validate

1. A 4KB WRITE arrives at RAID01Manager with offset 0. With 4 minions (at indices 0,1,2,3), which two minions receive the write? If the block size is 4096, which minions receive a write at offset 4096?
2. A WRITE sends UDP to both minions. Primary ACKs in 5ms. Replica never ACKs (it crashed). The manager is waiting with `future::get()`. What exactly blocks? How would you add a timeout so the main pipeline doesn't stall forever?
3. The `ResponseManager` receiver thread calls `promise.set_value(ack)` for MSG_ID 42. Meanwhile, the main thread has already timed out on MSG_ID 42 and moved on. The promise is now dangling. What runtime behavior results, and how would you handle this race?
