# Phase 2A — Mac Client TCP Bridge

**Duration:** 2 weeks (May 6–20, 2026) | **Effort:** ~16 hrs | **Status:** ⏳ Active

---

## Goal

Build a real network link between a Mac client and the Linux master over TCP. After this phase, a program running on your Mac can read and write blocks to the Linux storage server over the network — using real sockets, a custom binary protocol, and the existing Reactor infrastructure.

**Milestone:** Mac client writes a block → TCP → Linux master stores it → Mac client reads it back → data matches byte for byte. Two real machines. Real network.

---

## Why This Before Phase 2 (RAID/Minions)

| Original Phase 2 | Phase 2A (this) |
|---|---|
| RAID01Manager, MinionProxy, Scheduler, ResponseManager | TCPServer + BlockClient |
| ~46 hours | ~16 hours |
| All runs on one machine (no real cross-machine networking) | Two real machines on a real network |
| Hard to show without explaining the full RAID design | Trivially demonstrable in 30 seconds |

Phase 2A gets you a **working distributed demo in 2 weeks** and a CV story you can tell confidently. Phase 2 (RAID) continues after.

---

## What's Being Built

### TCPServer (Linux side)

Sits inside the existing master process. Listens on a TCP port. When a client connects, it adds the client socket to the existing Reactor — so the same epoll loop that already handles NBD requests now also handles TCP client requests without a second thread.

When data arrives from a client, it parses the wire packet, calls `LocalStorage.Read` or `LocalStorage.Write`, and sends a response back over the same socket.

→ See [[Components/TCPServer]]

### BlockClient (Mac side)

A self-contained C++ class. Call `Connect(ip, port)`, then `Read(offset, len)` or `Write(offset, data)`. The class handles TCP framing, byte ordering, and response parsing internally.

A CLI demo (`ldsclient`) wraps it for easy testing and demos.

→ See [[Components/BlockClient]]

---

## Reactor Upgrade Required

The existing Reactor uses one global handler for all fds. TCPServer needs to add client fds dynamically with their own handlers. The fix is small but architectural:

```
Current:  Add(fd)  +  SetHandler(fn)  →  one fn called for every fd
Upgraded: Add(fd, fn)                 →  each fd has its own fn stored in a map
```

This makes the Reactor what it's supposed to be: a true per-fd event dispatcher, not a broadcaster to a single handler.

After upgrade, `LDS.cpp` wiring becomes:
```cpp
reactor.Add(driver.GetFD(),    [&](int fd){ mediator.Notify(fd); });
reactor.Add(server.GetListenFD(), [&](int fd){ server.OnAccept(fd); });
// server.OnAccept() internally calls reactor.Add(client_fd, handler)
reactor.Run();
```

---

## Wire Protocol (TCP framing)

TCP is a stream — you can receive half a message. The fix is length-prefix framing: always send a fixed-size header first, then exactly `header.length` bytes.

**Client → Server (Request):**
```
| type (1B) | offset (8B, big-endian) | length (4B, big-endian) | data (length B, WRITE only) |
```

**Server → Client (Response):**
```
| status (1B) | length (4B, big-endian) | data (length B, READ only) |
```

| Type | Value |
|---|---|
| READ | `0x00` |
| WRITE | `0x01` |

| Status | Value |
|---|---|
| OK | `0x00` |
| ERROR | `0x01` |

Defined in `services/network/include/NetworkProtocol.hpp` — included by both sides.

→ See [[03 - Client-Server Architecture]]

---

## Files To Create / Modify

```
design_patterns/reactor/
├── include/reactor.hpp          ← upgrade: per-fd handler map
└── src/reactor.cpp              ← upgrade: dispatch by fd in Run()

services/network/
├── include/NetworkProtocol.hpp  ← NEW: wire format structs (shared)
├── include/TCPServer.hpp        ← NEW
└── src/TCPServer.cpp            ← NEW

client/
├── include/BlockClient.hpp      ← NEW
├── src/BlockClient.cpp          ← NEW
└── src/main.cpp                 ← NEW: CLI demo

app/LDS.cpp                      ← update: add TCPServer, update Reactor calls
```

**Bug fixes first (before touching anything else):**
- Bug #3 — always reply to NBD kernel even on storage error
- Bug #8 — `Dispatcher` needs `shared_mutex`
- Bug #10 — `ThreadPool` static mutex/cv

---

## Build Order

1. Fix bugs #3, #8, #10 — verify existing tests still pass
2. Upgrade Reactor to per-fd handlers — verify NBD still works
3. Define `NetworkProtocol.hpp` — agree on wire format before writing either side
4. Build `TCPServer` on Linux
5. Build `BlockClient` on Mac
6. Build CLI demo
7. End-to-end test on real Mac ↔ Linux hardware

---

## Done Criteria

- [ ] Bugs #3, #8, #10 fixed — all existing tests still pass
- [ ] Reactor upgraded — per-fd handlers, no regression
- [ ] `TCPServer` accepts connections, routes through `LocalStorage`, sends response
- [ ] `BlockClient` can `Connect`, `Read`, `Write`
- [ ] CLI demo: write a file from Mac, read it back, diff is empty
- [ ] Tested on real Mac ↔ Linux (not just localhost)

---

## Previous / Next

← [[Phase 1 - Core Framework Integration]]
→ [[Phase 2 - Data Management & Network]] (RAID, Minion proxy — starts after Phase 2A milestone is green)
