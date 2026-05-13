# Phase 2A Execution Plan — Mac Client TCP Bridge

**Dates:** 2026-05-06 → 2026-05-20
**Budget:** ~16 hours
**Goal:** Working end-to-end TCP demo — Mac client reads/writes blocks on Linux master

---

## Pre-Work Gate (Day 1, 2 hrs) — Fix Bugs Before Writing New Code

Three bugs must be fixed first. They are small, but they will cause crashes or incorrect behavior the moment new code runs.

| Bug | File | Fix |
|---|---|---|
| #3 No error reply to kernel | `app/LDS.cpp` | Wrap storage calls in try/catch; always call `SendReply` regardless |
| #8 Dispatcher not thread-safe | `design_patterns/observer/include/Dispatcher.hpp` | Add `std::shared_mutex m_mutex`; shared lock for `NotifyAll`, unique lock for `Register`/`UnRegister` |
| #10 ThreadPool static mutex/cv | `utilities/threading/thread_pool/include/thread_pool.hpp` + `.cpp` | Remove `static` from `m_mutex` and `m_cv` — they must be instance members |

**Gate check:** Run all existing test binaries. All must pass before proceeding.

---

## Day 2: Reactor Upgrade (2 hrs)

Change the Reactor from a single global handler to per-fd handlers.

**`reactor.hpp` change:**
- Remove `m_io_handler` member
- Add `std::unordered_map<int, std::function<void(int)>> m_handlers`
- Change `Add(int fd)` to `Add(int fd, std::function<void(int)> handler)`
- Remove `SetHandler(fn)`

**`reactor.cpp` change:**
- `Add(fd, handler)` stores `{fd, handler}` in `m_handlers` and calls `epoll_ctl ADD`
- `Run()`: look up `m_handlers[fd]` and call it instead of `m_io_handler(fd)`

**`LDS.cpp` update:**
- `reactor.Add(driver.GetFD(), [&](int fd){ mediator.Notify(fd); });`

**Gate check:** System boots, NBD requests still work, signal shutdown still works.

---

## Day 3: Wire Protocol (1 hr)

Define `services/network/include/NetworkProtocol.hpp`. No implementation — just the structs.

```cpp
#pragma pack(push, 1)
namespace hrd41 {

struct ClientRequest {
    uint8_t  type;    // 0x00=READ, 0x01=WRITE
    uint64_t offset;  // big-endian (htobe64 on send, be64toh on recv)
    uint32_t length;  // big-endian (htonl on send, ntohl on recv)
    // followed by `length` bytes of data for WRITE; nothing for READ
};

struct ServerResponse {
    uint8_t  status;  // 0x00=OK, 0x01=ERROR
    uint32_t length;  // big-endian — data byte count
    // followed by `length` bytes of data for READ response; 0 for WRITE response
};

} // namespace hrd41
#pragma pack(pop)
```

Write this file. Do not write TCPServer or BlockClient yet — agree on the protocol first so both sides match.

---

## Days 4–5: TCPServer on Linux (5 hrs)

**Files:** `services/network/include/TCPServer.hpp` + `src/TCPServer.cpp`

**Implementation order:**

1. Constructor: `socket(AF_INET, SOCK_STREAM, 0)` + `SO_REUSEADDR` + `bind()` + `listen()`
2. `GetListenFD()` — returns `m_listen_fd` for registration with Reactor
3. `OnAccept(int listen_fd)` — calls `accept()`, then `m_reactor.Add(client_fd, [this, client_fd](int fd){ OnClientData(fd); })`
4. `RecvAll(int fd, void* buf, size_t n)` — loops `recv()` until all n bytes received (handles TCP fragmentation)
5. `SendAll(int fd, const void* buf, size_t n)` — loops `send()` until all n bytes sent
6. `OnClientData(int fd)`:
   - `RecvAll(fd, &req_hdr, sizeof(ClientRequest))`
   - Convert byte order: `offset = be64toh(req_hdr.offset)`, `length = ntohl(req_hdr.length)`
   - If WRITE: `RecvAll(fd, data_buf, length)`, then `m_storage.Write(...)`
   - If READ: `m_storage.Read(...)`, then `SendAll(fd, response + data)`
   - Send `ServerResponse` with status

**Wire into `LDS.cpp`:**
```cpp
TCPServer tcp_server(7800, reactor, storage);
reactor.Add(tcp_server.GetListenFD(), [&](int fd){ tcp_server.OnAccept(fd); });
```

**Gate check:** Connect with `nc` or `telnet` — server accepts without crashing.

---

## Days 6–7: BlockClient on Mac (4 hrs)

**Files:** `client/include/BlockClient.hpp` + `src/BlockClient.cpp`

**Interface:**
```cpp
class BlockClient {
public:
    void Connect(const std::string& ip, int port);
    void Disconnect();
    std::vector<char> Read(uint64_t offset, uint32_t length);
    void Write(uint64_t offset, const std::vector<char>& data);
private:
    int m_fd = -1;
    void SendAll(const void* buf, size_t n);
    void RecvAll(void* buf, size_t n);
};
```

**Implementation order:**
1. `Connect()` — `socket()` + `connect()` to Linux IP:port
2. `SendAll()` / `RecvAll()` — same TCP stream helpers as server side
3. `Write()`:
   - Fill `ClientRequest{0x01, htobe64(offset), htonl(data.size())}`
   - `SendAll(hdr)` then `SendAll(data)`
   - `RecvAll(response_hdr)` — check status
4. `Read()`:
   - Fill `ClientRequest{0x00, htobe64(offset), htonl(length)}`
   - `SendAll(hdr)`
   - `RecvAll(response_hdr)` — get length
   - `RecvAll(data_buf, ntohl(response_hdr.length))`
   - Return data

---

## Day 8: CLI Demo (1 hr)

**File:** `client/src/main.cpp`

```
Usage:
  ./ldsclient <ip> <port> write <offset> <file>
  ./ldsclient <ip> <port> read  <offset> <length>

Examples:
  ./ldsclient 192.168.1.5 7800 write 0 hello.txt
  ./ldsclient 192.168.1.5 7800 read  0 13
```

Parse args, create `BlockClient`, call `Connect`, call `Read` or `Write`, print result or write to stdout.

---

## Day 9: End-to-End Test (1 hr)

**On Linux (start master):**
```bash
sudo modprobe nbd
./lds /dev/nbd0 134217728
# should print: "LDS: serving 134217728 bytes on /dev/nbd0, TCP on port 7800"
```

**On Mac:**
```bash
echo "Hello from Mac!" > test.txt
./ldsclient 192.168.1.5 7800 write 0 test.txt
./ldsclient 192.168.1.5 7800 read  0 16
# expected output: Hello from Mac!
```

**Stress test:**
```bash
dd if=/dev/urandom of=random.bin bs=4096 count=256   # 1 MB
./ldsclient 192.168.1.5 7800 write 0 random.bin
./ldsclient 192.168.1.5 7800 read  0 1048576 > readback.bin
diff random.bin readback.bin  # must be empty
```

---

## Day 10: Buffer (tests + README)

- Write `test/unit/test_tcp_server.cpp` — loopback test: connect locally, write, read back
- Update `README.md`: architecture diagram, build instructions, run instructions for both machines
- Confirm tests pass on Linux

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| TCP fragmentation bug | High | Implement `RecvAll()` as a proper loop from day 1 — never assume one `recv()` gets everything |
| Mac missing `htobe64` / `be64toh` | Medium | Use `__builtin_bswap64` or manual shift; test byte order with a known value |
| Firewall blocks port 7800 on Linux | Medium | `sudo ufw allow 7800/tcp` or test on local LAN first |
| Reactor upgrade breaks existing tests | Low | Upgrade Reactor and run all tests before writing a single line of TCPServer |
| Client fd leaks on connection drop | Medium | `OnClientData()` must call `reactor.Remove(fd)` + `close(fd)` on recv error |

---

## Related Notes

- [[Phase 2A - Mac Client TCP Bridge]]
- [[Architecture/03 - Client-Server Architecture]]
- [[Decisions/05 - Why TCP for Client]]
- [[Components/TCPServer]]
- [[Components/BlockClient]]
- [[Engineering/Known Bugs]]
