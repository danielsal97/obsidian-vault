# Wire Protocol Specification — Master ↔ Minion UDP

**Status:** Draft — for Phase 2 implementation  
**Version:** 1.0  
**Transport:** UDP/IPv4 (LAN only, no WAN)

This is the byte-level contract between the master node and each minion. Define this on paper first, then implement it — changing the wire format mid-phase breaks everything.

---

## Design Principles

1. **Fixed-size header** — every message starts with the same header. Parser always knows how much to read first.
2. **Length-prefixed payload** — variable-length data is preceded by its byte count.
3. **Big-endian** — network byte order (`htonl`/`ntohl`) for all multi-byte integers.
4. **Stateless** — each UDP packet is self-contained. No session state on minions.
5. **MSG_ID for async matching** — master sends request, registers callback keyed by MSG_ID, gets reply later.

---

## Master → Minion: Request Packet

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌───────────────────────────────────────────────────────────────────┐
│                         MSG_ID (4 bytes)                          │
├───────┬───────────────────────────────────────────────────────────┤
│ OP(1) │                    RESERVED (3 bytes)                     │
├───────────────────────────────────────────────────────────────────┤
│                         OFFSET (8 bytes)                          │
│                                                                   │
├───────────────────────────────────────────────────────────────────┤
│                         LENGTH (4 bytes)                          │
├───────────────────────────────────────────────────────────────────┤
│                  DATA (LENGTH bytes, PUT only)                    │
│                           ...                                     │
└───────────────────────────────────────────────────────────────────┘
```

| Field | Size | Description |
|---|---|---|
| `MSG_ID` | 4 bytes | Unique request identifier (monotonic counter, thread-safe) |
| `OP` | 1 byte | Operation type: `0x00`=GET, `0x01`=PUT, `0x02`=DELETE |
| `RESERVED` | 3 bytes | Zero-padded, reserved for future flags |
| `OFFSET` | 8 bytes | Byte offset into the minion's storage |
| `LENGTH` | 4 bytes | Number of bytes to read/write |
| `DATA` | `LENGTH` bytes | Present only for PUT; absent for GET/DELETE |

**Total header size:** 20 bytes  
**Max payload:** 65,515 bytes (UDP max - IP header - UDP header - our header)  
**Practical block size:** 4096 bytes (one filesystem block per packet)

---

## Minion → Master: Response Packet

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌───────────────────────────────────────────────────────────────────┐
│                         MSG_ID (4 bytes)                          │
├───────┬───────────────────────────────────────────────────────────┤
│STATUS │                    RESERVED (3 bytes)                     │
├───────────────────────────────────────────────────────────────────┤
│                         LENGTH (4 bytes)                          │
├───────────────────────────────────────────────────────────────────┤
│                  DATA (LENGTH bytes, GET only)                    │
│                           ...                                     │
└───────────────────────────────────────────────────────────────────┘
```

| Field | Size | Description |
|---|---|---|
| `MSG_ID` | 4 bytes | Echoes the request's MSG_ID — master uses this to match |
| `STATUS` | 1 byte | `0x00`=OK, `0x01`=ERROR, `0x02`=OUT_OF_RANGE, `0x03`=CHECKSUM_FAIL |
| `RESERVED` | 3 bytes | Zero-padded |
| `LENGTH` | 4 bytes | Data length (0 for PUT/DELETE responses) |
| `DATA` | `LENGTH` bytes | Present only for GET responses |

---

## Operation Codes

| Code | Name | Request has DATA? | Response has DATA? |
|---|---|---|---|
| `0x00` | GET | No | Yes (requested bytes) |
| `0x01` | PUT | Yes (bytes to store) | No |
| `0x02` | DELETE | No | No |
| `0x03` | PING | No | No (STATUS=OK means alive) |

**PING** — used by the Watchdog to check if a minion is alive. Sent every 5s. Minion immediately replies with STATUS=OK. No data transferred.

---

## Status Codes

| Code | Name | Meaning | Master action |
|---|---|---|---|
| `0x00` | OK | Success | Mark complete |
| `0x01` | ERROR | Generic failure | Retry up to 3x |
| `0x02` | OUT_OF_RANGE | Offset+length exceeds storage | Permanent failure, escalate |
| `0x03` | CHECKSUM_FAIL | Data integrity error | Retry from replica |

---

## MSG_ID Generation

```cpp
// MinionProxy.cpp
class MinionProxy {
    std::atomic<uint32_t> m_nextMsgId{1};

    uint32_t NextMsgId() {
        return m_nextMsgId.fetch_add(1, std::memory_order_relaxed);
    }
};
```

- Starts at 1 (0 is reserved as "no ID")
- Wraps around at 2^32 (after 4 billion requests — acceptable)
- `std::atomic` ensures thread-safe increment without a mutex
- IDs must be unique per concurrent outstanding request, not globally forever

---

## Packet Layout in C++ (Implementation Guide)

```cpp
// Request header (pack to avoid padding)
#pragma pack(push, 1)
struct RequestHeader {
    uint32_t msg_id;     // htonl()
    uint8_t  op;
    uint8_t  reserved[3];
    uint64_t offset;     // htobe64()
    uint32_t length;     // htonl()
};

struct ResponseHeader {
    uint32_t msg_id;     // ntohl()
    uint8_t  status;
    uint8_t  reserved[3];
    uint32_t length;     // ntohl()
};
#pragma pack(pop)
```

**Serialization:**
```cpp
// Sending a PUT:
RequestHeader hdr;
hdr.msg_id  = htonl(msg_id);
hdr.op      = 0x01;  // PUT
hdr.offset  = htobe64(offset);
hdr.length  = htonl(data.size());
memset(hdr.reserved, 0, 3);

iovec iov[2];
iov[0] = { &hdr, sizeof(hdr) };
iov[1] = { data.data(), data.size() };

sendmsg(udp_fd, &msg, 0);  // scatter-gather, one syscall
```

---

## UDP Reliability Model

UDP is unreliable. LDS handles this at the application layer:

```
Master sends request → starts Scheduler timer (1s)
  ├─ Response arrives within 1s → cancel timer, success
  └─ Timer expires:
        attempt 2 → wait 2s
        attempt 3 → wait 4s
        give up → mark minion DEGRADED, try replica
```

**Exponential backoff:**

| Attempt | Wait | Total elapsed |
|---|---|---|
| 1 | 1s | 1s |
| 2 | 2s | 3s |
| 3 | 4s | 7s |
| fail | — | 7s max per block |

**The 7-second worst case** happens only when a minion dies mid-request. Normal operation: sub-millisecond round trip on LAN.

---

## Port Assignment

| Port | Used by | Direction |
|---|---|---|
| `7700` | Master listens for minion responses | Minion → Master |
| `7701` | Minion listens for master requests | Master → Minion |
| `7702` | AutoDiscovery broadcast | Minion → Master (broadcast) |

These are configurable. Ports above 1024 don't require root.

---

## Example Exchange — GET Block 42

```
Master → Minion 2 (192.168.1.12:7701):
  MSG_ID = 0x00000017
  OP     = 0x00 (GET)
  OFFSET = 0x000000000002A000  (block 42 × 4096 = 172032)
  LENGTH = 0x00001000 (4096)

Minion 2 → Master (192.168.1.1:7700):
  MSG_ID = 0x00000017  (echoed)
  STATUS = 0x00 (OK)
  LENGTH = 0x00001000 (4096)
  DATA   = [4096 bytes of block data]
```

---

## Phase 2 Implementation Checklist

- [ ] `RequestHeader` / `ResponseHeader` structs with `#pragma pack`
- [ ] `MSG_ID` atomic counter in `MinionProxy`
- [ ] `sendmsg` with scatter-gather for zero-copy header+data
- [ ] `ResponseManager` parses response header, dispatches by MSG_ID
- [ ] `Scheduler` tracks pending MSG_IDs with deadlines
- [ ] Byte order conversion (`htonl`/`ntohl`/`htobe64`/`be64toh`) tested

---

## Related Notes
- [[MinionProxy]]
- [[ResponseManager]]
- [[Scheduler]]
- [[Phase 2 - Data Management & Network]]
- [[Request Lifecycle]]
