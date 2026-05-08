# Serialization

Converting data structures to a byte sequence (for network transmission, file storage, IPC) and back.

---

## Why Serialization is Non-Trivial

You can't just `memcpy` a struct over the wire:
1. **Padding** — struct may have alignment bytes between fields
2. **Byte order** — little-endian sender, big-endian receiver (or vice versa)
3. **Pointer sizes** — 32-bit vs 64-bit systems differ
4. **Floating point** — representation varies across platforms

---

## Manual Serialization — The Correct Way

Write each field explicitly, no padding, network byte order:

```c
#include <stdint.h>
#include <string.h>
#include <arpa/inet.h>  // htonl, htons
#include <endian.h>     // htobe64

typedef struct {
    uint8_t  type;
    uint64_t offset;
    uint32_t length;
} RequestHeader;

// Serialize to buffer (13 bytes, no padding):
void serialize_header(const RequestHeader* h, uint8_t* buf) {
    buf[0] = h->type;
    
    uint64_t offset_net = htobe64(h->offset);
    memcpy(buf + 1, &offset_net, 8);
    
    uint32_t length_net = htonl(h->length);
    memcpy(buf + 9, &length_net, 4);
}

// Deserialize from buffer:
void deserialize_header(const uint8_t* buf, RequestHeader* h) {
    h->type = buf[0];
    
    uint64_t offset_net;
    memcpy(&offset_net, buf + 1, 8);
    h->offset = be64toh(offset_net);
    
    uint32_t length_net;
    memcpy(&length_net, buf + 9, 4);
    h->length = ntohl(length_net);
}
```

---

## Packed Struct Approach

Use `__attribute__((packed))` to remove padding, then handle byte order:

```c
struct __attribute__((packed)) Header {
    uint8_t  type;
    uint64_t offset;   // still needs byte-order conversion
    uint32_t length;
} header;

// sizeof(header) == 13 — no padding
// But: misaligned access — only safe for serialization buffers
```

**Warning:** packed structs can cause misaligned memory access on ARM — segfault or performance penalty. Only use them as serialization buffers, not as general data structures.

---

## Byte Order Cheat Sheet

```c
// 16-bit:
htons(x)   // host → network (big-endian)
ntohs(x)   // network → host

// 32-bit:
htonl(x)
ntohl(x)

// 64-bit (Linux):
htobe64(x)   // host → big-endian
be64toh(x)   // big-endian → host
htole64(x)   // host → little-endian
le64toh(x)   // little-endian → host
```

---

## Length-Prefix Framing

When sending variable-length data over a stream (TCP), prefix it with its length:

```c
// Send: [4-byte length][data]
void send_message(int fd, const void* data, uint32_t len) {
    uint32_t net_len = htonl(len);
    send_all(fd, &net_len, 4);
    send_all(fd, data, len);
}

// Receive:
bool recv_message(int fd, void* buf, uint32_t max_len, uint32_t* out_len) {
    uint32_t net_len;
    if (!recv_all(fd, &net_len, 4)) return false;
    uint32_t len = ntohl(net_len);
    if (len > max_len) return false;
    if (!recv_all(fd, buf, len)) return false;
    *out_len = len;
    return true;
}
```

---

## Type-Tagged Messages

When a protocol has multiple message types:

```c
typedef enum : uint8_t {
    MSG_READ  = 0x00,
    MSG_WRITE = 0x01,
    MSG_ACK   = 0x02,
    MSG_ERROR = 0x03,
} MsgType;

// Fixed header for all messages:
struct __attribute__((packed)) MsgHeader {
    uint8_t  type;    // MsgType
    uint32_t length;  // payload length
};

// Dispatcher:
void dispatch(int fd) {
    MsgHeader hdr;
    recv_all(fd, &hdr, sizeof(hdr));
    hdr.length = ntohl(hdr.length);
    
    switch (hdr.type) {
        case MSG_READ:  handle_read(fd, hdr.length); break;
        case MSG_WRITE: handle_write(fd, hdr.length); break;
        default: handle_unknown(fd, &hdr); break;
    }
}
```

---

## Serializing Strings

Strings need special handling — null terminator or explicit length:

```c
// Option 1: length-prefixed (preferred — handles embedded nulls):
void serialize_string(uint8_t* buf, const char* s, size_t* pos) {
    uint16_t len = strlen(s);
    uint16_t net_len = htons(len);
    memcpy(buf + *pos, &net_len, 2); *pos += 2;
    memcpy(buf + *pos, s, len);     *pos += len;
}

// Option 2: null-terminated (simple but fragile):
// strcpy(buf, s); buf += strlen(s) + 1;
```

---

## Checksums / Integrity

For detecting corruption:

```c
// Simple XOR checksum:
uint8_t checksum(const uint8_t* data, size_t len) {
    uint8_t sum = 0;
    for (size_t i = 0; i < len; i++) sum ^= data[i];
    return sum;
}

// CRC32 — better, use zlib:
#include <zlib.h>
uint32_t crc = crc32(0, data, len);
```

---

## LDS Wire Protocol

LDS uses manual serialization for both TCP and UDP protocols:

**TCP (client ↔ master):**
```
[type:1B][offset:8B BE][length:4B BE][data:length bytes]
```

**UDP (master ↔ minion):**
```
[MSG_ID:4B][OP:1B][OFFSET:8B][LEN:4B][DATA:var]
```

Both use `RecvAll`/`SendAll` loops, big-endian multi-byte integers, and no struct padding.

---

## Understanding Check

> [!question]- Why can't you just `send(fd, &header, sizeof(header), 0)` to serialize a struct, even if you use `__attribute__((packed))`?
> `packed` removes padding so `sizeof` gives the wire size, but it does not convert multi-byte integer fields to network byte order. A little-endian sender and big-endian receiver will interpret the same bytes as different values. You still need `htonl`/`htobe64` on every multi-byte field. Additionally, dereferencing an unaligned pointer (which `packed` can create) is undefined behavior on ARM and a performance penalty on x86. The only correct approach is to write each field explicitly into a `uint8_t` buffer using `memcpy` after byte-order conversion.

> [!question]- What goes wrong if the receiver trusts the length field in a length-prefix framed message without validating it?
> A malicious or corrupt sender can set the length field to a huge value. The receiver calls `malloc(len)` or tries to `recv_all(fd, buf, len)` where `len` is e.g. 4GB. This causes either an OOM crash, a failed malloc followed by a null dereference, or an integer overflow if `len` wraps and the actual allocation is tiny but the `recv_all` loop reads gigabytes of data. Validation must happen before acting on `len`: check `len <= MAX_MESSAGE_SIZE` and check that `malloc` succeeded.

> [!question]- In the LDS TCP protocol, the offset field is 8 bytes in big-endian. Why does the serializer use `memcpy` into the buffer rather than casting the buffer pointer to `uint64_t*` and assigning directly?
> Casting `buf + 1` (a `uint8_t*`) to `uint64_t*` and dereferencing produces a misaligned pointer — the address is offset by 1 byte and `uint64_t` requires 8-byte alignment. On x86 this works by accident but is undefined behavior; on ARM it causes a bus error or silent misread. `memcpy` has no alignment requirement — it copies bytes regardless of the source and destination alignment. The compiler also optimizes `memcpy` of small fixed sizes (4, 8 bytes) into a single load/store instruction on aligned platforms, so there is no performance cost.

> [!question]- What goes wrong if you use a null-terminated string in a protocol message instead of a length-prefix, and the string data itself contains a null byte?
> A null-terminated string cannot represent data containing `'\0'` because the first zero byte is treated as the end of the string. Any bytes after it are silently dropped by `strlen`, `strcpy`, or any function that reads until `'\0'`. Filenames on some systems, binary keys, or encrypted data can all contain embedded zeros. Length-prefix framing treats the payload as opaque bytes and relies on the explicit length — it handles any byte value, including zero. The LDS protocol uses the length-prefix approach in its wire format for exactly this reason.

> [!question]- A CRC32 checksum detects corruption. Why is XOR checksum inadequate for a protocol that must detect single-bit errors in all positions?
> XOR checksum is simply all bytes XORed together. Any even number of errors in the same bit position cancel out — two bytes with bit 3 flipped produce the same XOR as if neither was flipped. It also cannot detect reordered bytes: the XOR of a message is the same regardless of byte order. CRC32 uses a polynomial division that produces a checksum sensitive to the position of each bit, not just its presence. A single-bit error in any position produces a different CRC32, and burst errors (consecutive corrupted bits) are detected with very high probability. For LDS storage blocks, CRC32 is the minimum acceptable integrity check.
