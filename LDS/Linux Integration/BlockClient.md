# BlockClient

**Phase:** 2A | **Status:** ❌ Not built  
**Location:** `client/include/BlockClient.hpp` + `src/BlockClient.cpp`  
**Platform:** Mac (also compiles on Linux for testing)

---

## What It Does

BlockClient is the Mac-side TCP client. It provides a simple, typed API for reading and writing blocks of data to a remote Linux master over TCP.

Internally it:
1. Manages a TCP socket connection to the Linux master
2. Serializes read/write requests into the `NetworkProtocol` wire format
3. Handles TCP framing (length-prefix send/receive)
4. Deserializes responses and returns typed results

The user of `BlockClient` never touches a socket or a byte-order conversion.

---

## Interface

```cpp
class BlockClient {
public:
    BlockClient() = default;
    ~BlockClient();

    BlockClient(const BlockClient&) = delete;
    BlockClient& operator=(const BlockClient&) = delete;

    // Connect to a Linux master. Throws std::runtime_error on failure.
    void Connect(const std::string& ip, int port);

    // Close the connection.
    void Disconnect();

    // Read `length` bytes starting at `offset`.
    // Throws on error (connection lost, server returned ERROR status).
    std::vector<char> Read(uint64_t offset, uint32_t length);

    // Write `data` starting at `offset`.
    // Throws on error.
    void Write(uint64_t offset, const std::vector<char>& data);

private:
    int m_fd = -1;

    void SendAll(const void* buf, size_t n);
    void RecvAll(void* buf, size_t n);
};
```

---

## Wire Format It Speaks

Same format as TCPServer — both sides include `services/network/include/NetworkProtocol.hpp`.

**Write request:**
```
[type=0x01 (1B)][offset big-endian (8B)][length big-endian (4B)][data (length B)]
```

**Read request:**
```
[type=0x00 (1B)][offset big-endian (8B)][length big-endian (4B)]
```

**Response:**
```
[status (1B)][length big-endian (4B)][data (length B, READ only)]
```

---

## CLI Demo (main.cpp)

```
client/src/main.cpp wraps BlockClient in a command-line tool.

Usage:
  ./ldsclient <ip> <port> write <offset> <file>
  ./ldsclient <ip> <port> read  <offset> <length>

Examples:
  ./ldsclient 192.168.1.5 7800 write 0 hello.txt
  ./ldsclient 192.168.1.5 7800 read  0 13
  ./ldsclient 192.168.1.5 7800 write 4096 page2.bin
```

`write` reads the file and sends its contents starting at `offset`.  
`read` prints the data to stdout — pipe to a file with `> out.bin` if needed.

---

## Key Implementation Notes

**`RecvAll` is as critical here as on the server.**
TCP fragmentation happens on both ends. The same loop used in TCPServer must be used here:

```cpp
void BlockClient::RecvAll(void* buf, size_t n) {
    size_t received = 0;
    while (received < n) {
        ssize_t r = recv(m_fd, (char*)buf + received, n - received, 0);
        if (r <= 0) throw std::runtime_error("Connection lost");
        received += r;
    }
}
```

**Byte ordering.**
The Mac (ARM) and the Linux server (x86) are both little-endian, but the protocol mandates big-endian regardless. Always convert:

```cpp
// Sending:
req.offset = htobe64(offset);
req.length = htonl(data.size());

// Receiving:
uint32_t length = ntohl(resp.length);
```

Note: `htobe64` may not exist on older macOS. Use `OSSwapHostToBigInt64(x)` from `<libkern/OSByteOrder.h>` or implement as `__builtin_bswap64`.

**Error propagation.**
If the server returns `status=0x01` (ERROR), throw `std::runtime_error`. Don't silently return an empty buffer — callers need to know.

---

## Usage Example (in code)

```cpp
BlockClient client;
client.Connect("192.168.1.5", 7800);

// Write "Hello, world!" at offset 0
std::string msg = "Hello, world!";
client.Write(0, std::vector<char>(msg.begin(), msg.end()));

// Read it back
auto data = client.Read(0, 13);
std::string result(data.begin(), data.end());
// result == "Hello, world!"

client.Disconnect();
```

---

## Related Notes

- [[Architecture/Client-Server Architecture]]
- [[Components/TCPServer]] — the Linux-side counterpart
- [[Phase 2A - Mac Client TCP Bridge]]
- [[Decisions/Why TCP for Client]]
