# MinionServer — Architecture

The MinionServer is the binary that runs on each Raspberry Pi. It is the other half of the LDS system. The master sends UDP commands (GET_BLOCK, PUT_BLOCK, DELETE_BLOCK, PING); the minion executes them against local storage and sends a response with the same MSG_ID.

**Phase:** Phase 4 | **Effort:** ~12 hrs | **Language:** C++20

---

## Responsibility

- Receive UDP packets from the master on a fixed port (default: 8800)
- Parse the wire format (same protocol as `MinionProxy` sends)
- Dispatch to GET, PUT, DELETE, or PING handlers
- Store blocks in local file storage
- Send response packets including MSG_ID for matching
- Broadcast `"Hello"` UDP message on startup so `AutoDiscovery` can register it

---

## Wire Protocol

Same format as `MinionProxy` sends. The minion is the server side.

### Request (master → minion)

```cpp
#pragma pack(push, 1)
struct MinionRequest {
    uint32_t msg_id;    // echo back in response — used by ResponseManager to match
    uint8_t  op;        // 0x01=GET_BLOCK, 0x02=PUT_BLOCK, 0x03=DELETE_BLOCK, 0x04=PING
    uint64_t offset;    // byte offset in minion's local storage (big-endian)
    uint32_t len;       // data length in bytes (big-endian); 0 for GET/DELETE/PING
    // followed by `len` bytes of data for PUT_BLOCK
};
#pragma pack(pop)
```

### Response (minion → master)

```cpp
#pragma pack(push, 1)
struct MinionResponse {
    uint32_t msg_id;    // copied from request
    uint8_t  status;    // 0x00=OK, 0x01=ERROR
    uint32_t len;       // data byte count (big-endian); 0 for PUT/DELETE/PING
    uint32_t reserved;  // padding — must be 0
    // followed by `len` bytes of data for GET_BLOCK response
};
#pragma pack(pop)
```

Op codes:

| Op | Value | Direction | Description |
|----|-------|-----------|-------------|
| GET_BLOCK | 0x01 | master→minion | Read `len` bytes from `offset`. Response carries data. |
| PUT_BLOCK | 0x02 | master→minion | Write `len` bytes to `offset`. Response is ACK only. |
| DELETE_BLOCK | 0x03 | master→minion | Zero-out block at `offset`. Response is ACK only. |
| PING | 0x04 | master→minion | Liveness check. Response is empty ACK. |

---

## Class Interface

```cpp
// minion/include/MinionServer.hpp

class MinionServer {
public:
    explicit MinionServer(int port = 8800);
    ~MinionServer();

    void Start();   // blocks: runs the receive loop until Stop() is called
    void Stop();    // signal the receive loop to exit (from signal handler)

private:
    int         m_sock_fd;
    int         m_port;
    std::atomic<bool> m_running{false};

    LocalStorage m_storage;   // re-uses the Phase 1 LocalStorage directly

    void ReceiveLoop();
    void Dispatch(const MinionRequest& req, size_t data_len,
                  const sockaddr_in& sender);

    void HandleGet   (const MinionRequest& req, const sockaddr_in& sender);
    void HandlePut   (const MinionRequest& req, const std::vector<char>& data,
                      const sockaddr_in& sender);
    void HandleDelete(const MinionRequest& req, const sockaddr_in& sender);
    void HandlePing  (const MinionRequest& req, const sockaddr_in& sender);

    void SendResponse(uint32_t msg_id, uint8_t status,
                      const std::vector<char>& data, const sockaddr_in& dest);

    void BroadcastHello();   // sends discovery packet on startup
};
```

---

## How It Moves

```
main() on Raspberry Pi:
  MinionServer server(8800)
  server.Start()         ← blocks here

Start():
  m_sock_fd = socket(AF_INET, SOCK_DGRAM, 0)
  bind(m_sock_fd, port 8800)
  BroadcastHello()       ← 255.255.255.255:9000 "HELLO minion_id port"
  ReceiveLoop()

ReceiveLoop():
  while m_running:
    recvfrom(m_sock_fd, buf, MAX_BUF, 0, &sender, &sender_len)
    parse MinionRequest from buf
    read trailing data bytes if op == PUT_BLOCK
    Dispatch(req, data_len, sender)

Dispatch():
  switch req.op:
    GET_BLOCK    → HandleGet(req, sender)
    PUT_BLOCK    → HandlePut(req, data, sender)
    DELETE_BLOCK → HandleDelete(req, sender)
    PING         → HandlePing(req, sender)

HandlePut():
  data_->m_type   = ActionType::WRITE
  data_->m_offset = be64toh(req.offset)
  data_->m_buffer = data
  m_storage.Write(data_)               ← same LocalStorage used by master in Phase 1
  SendResponse(req.msg_id, 0x00, {}, sender)

HandleGet():
  data_->m_type   = ActionType::READ
  data_->m_offset = be64toh(req.offset)
  data_->m_len    = ntohl(req.len)
  m_storage.Read(data_)
  SendResponse(req.msg_id, 0x00, data_->m_buffer, sender)

HandlePing():
  SendResponse(req.msg_id, 0x00, {}, sender)
  ← Watchdog on master uses this to confirm liveness
```

---

## Local Storage Backend

The minion reuses `LocalStorage` directly — the same class used by the master in Phase 1. It stores blocks in a memory-mapped file on the Pi's SD card or attached drive.

```cpp
// minion/src/main.cpp
int main(int argc, char* argv[]) {
    int port        = std::stoi(argv[1]);          // e.g. 8800
    size_t capacity = std::stoull(argv[2]);        // e.g. 1073741824 (1 GB)

    MinionServer server(port, capacity);
    server.Start();
}
```

Storage path: configurable at startup, defaults to `/var/lds/minion.dat`.
The file is created on first run and reused on restart — blocks survive reboot.

---

## AutoDiscovery Hello Broadcast

On startup, before entering the receive loop, the minion broadcasts a UDP packet:

```cpp
void MinionServer::BroadcastHello() {
    // Broadcast to 255.255.255.255 on the AutoDiscovery port (default: 9000)
    // Format: "HELLO <minion_id> <port>\n" as a plain text string
    // AutoDiscovery on the master parses this and calls RAID01Manager::AddMinion()
    std::string msg = "HELLO " + std::to_string(m_id) + " " + std::to_string(m_port) + "\n";
    sockaddr_in bcast{};
    bcast.sin_family      = AF_INET;
    bcast.sin_port        = htons(AUTODISCOVERY_PORT);   // 9000
    bcast.sin_addr.s_addr = INADDR_BROADCAST;

    int bcast_fd = socket(AF_INET, SOCK_DGRAM, 0);
    int opt = 1;
    setsockopt(bcast_fd, SOL_SOCKET, SO_BROADCAST, &opt, sizeof(opt));
    sendto(bcast_fd, msg.c_str(), msg.size(), 0,
           (sockaddr*)&bcast, sizeof(bcast));
    close(bcast_fd);
}
```

The master's `AutoDiscovery` component has a listener on port 9000 that parses these packets and adds the minion to `RAID01Manager`.

---

## Stop / Shutdown

`Stop()` sets `m_running = false`. This unblocks `recvfrom()` via `SO_RCVTIMEO`:

```cpp
// In constructor — set a 1-second receive timeout so the loop can check m_running
struct timeval tv{1, 0};
setsockopt(m_sock_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

// ReceiveLoop checks errno == EAGAIN and loops back to check m_running:
int n = recvfrom(...);
if (n < 0 && errno == EAGAIN) continue;   // timeout — check m_running
if (n < 0) break;                          // real error — exit
```

Signal handler calls `server.Stop()` on SIGINT/SIGTERM.

---

## File Layout

```
minion/
  include/
    MinionServer.hpp
  src/
    MinionServer.cpp
    main.cpp
  CMakeLists.txt   (or Makefile)
```

The minion binary is cross-compiled for ARM (Raspberry Pi) from the development machine, or compiled natively on the Pi.

---

## Phase 4 Task Checklist

- [ ] `MinionServer.hpp` / `MinionServer.cpp` — receive loop + dispatch
- [ ] `HandleGet` + `HandlePut` + `HandleDelete` — wire to `LocalStorage`
- [ ] `HandlePing` — single-packet response
- [ ] `BroadcastHello()` — AutoDiscovery integration
- [ ] `Stop()` via `SO_RCVTIMEO` + `m_running` flag
- [ ] `main.cpp` — parse port + capacity args, start server
- [ ] `test/unit/test_minion_server.cpp` — loopback test: send GET/PUT/DELETE/PING to localhost:8800, verify responses

---

## Where It Breaks

- **No authentication**: any host on the network can send PUT_BLOCK to the minion. For a trusted LAN this is acceptable; for any untrusted network, add a shared secret or HMAC.
- **SD card write endurance**: Raspberry Pi SD cards wear out quickly under heavy write workloads. Point `LocalStorage` at an attached SSD or USB drive for production use.
- **Duplicate PUT_BLOCK**: if the master retries a PUT due to timeout, the minion writes the same data twice. This is idempotent as long as the same data is written to the same offset — verify this assumption in the retry path.
- **Broadcast Hello fails**: if the Pi and master are on different subnets, broadcasts don't cross routers. Use unicast Hello (send to master IP directly) or mDNS as a fallback.

---

## In LDS

`minion/` — sibling directory to `services/` at the repo root.

Dependency chain: `LocalStorage` (Phase 1) is reused directly. The minion binary has no dependency on the master's `RAID01Manager`, `Reactor`, or `ThreadPool` — it is a standalone UDP server.
