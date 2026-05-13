# Serialization — The Machine

## The Model
Packing a 3D object into a flat envelope for shipping. The sender and receiver both have the same packing manual (the protocol). The sender dismantles the object, packs each component in a fixed slot in the envelope. The receiver unpacks each slot in the same order and reassembles the 3D object. If either side uses a different manual, the object is rebuilt wrong.

## How It Moves

```
In-memory struct:                    Wire format (flat bytes):
struct NbdRequest {                  ┌────────────────────────────────┐
  uint32_t magic;    ←── 4 bytes     │ 0x25609513  (magic, big-endian)│
  uint16_t flags;    ←── 2 bytes     │ 0x0000      (flags)            │
  uint16_t type;     ←── 2 bytes     │ 0x0001      (type: WRITE)      │
  uint64_t handle;   ←── 8 bytes     │ handle...                      │
  uint64_t offset;   ←── 8 bytes     │ offset...                      │
  uint32_t len;      ←── 4 bytes     │ len...                         │
};                    28 bytes total └────────────────────────────────┘

Serialize:   fill buffer left-to-right, field by field
Deserialize: read buffer left-to-right, parse each field
```

**THE ENDIANNESS PROBLEM:** Your CPU stores multi-byte integers in a specific byte order. x86 is little-endian (least significant byte first). Network protocols are big-endian (most significant byte first). If you don't convert, the other side reads your `uint32_t 1` as `16777216`.

```c
// Convert TO network byte order (big-endian) before sending:
req.magic  = htonl(NBD_REQUEST_MAGIC);   // host-to-network long (32-bit)
req.offset = htobe64(offset);             // host-to-big-endian 64-bit

// Convert FROM network byte order after receiving:
uint32_t len = ntohl(raw.len);
```

## The Blueprint

- **Fixed-width types**: always use `uint32_t`, `uint64_t` — never `int` or `long` (size varies by platform)
- **`__attribute__((packed))`** or `#pragma pack(1)`: tells the compiler not to add alignment padding between struct fields. Required for wire-format structs.
- **`memcpy` over cast**: `*(uint32_t*)buf` violates strict aliasing rules (UB). Use `memcpy(&val, buf, 4)` instead.
- **Protocol versioning**: always include a magic number and version field — the receiver can detect wrong protocol instantly.

## Where It Breaks

- **Endianness mismatch**: forgot to `htonl` → remote side reads garbage. Symmetric: both sides look correct locally, protocol breaks only across machines.
- **Alignment assumption**: casting a `char*` to `uint32_t*` and dereferencing — UB on architectures that require aligned access (crashes on ARM).
- **Struct padding**: `sizeof(struct)` ≠ sum of field sizes if compiler adds alignment padding. Always use `packed` for wire-format structs or serialize field by field.

## In LDS

`services/communication_protocols/nbd/include/IDriverComm.hpp` + `NBDDriverComm.cpp`

The NBD request and reply structs are wire-format: `nbd_request` and `nbd_reply`. `NBDDriverComm::RecvRequest` reads exactly 28 bytes, then uses `ntohl`/`be64toh` to deserialize each field from network byte order into host byte order. `NBDDriverComm::SendReply` does the reverse: `htonl` before writing to the socket/device.

## Validate

1. You receive an NBD request. `ntohl(raw.len)` returns `67108864` (64MB). The sender sent `len = 4`. What went wrong?
2. A struct has `uint8_t a; uint32_t b;`. Without `__attribute__((packed))`, what is `sizeof(struct)`? Where did the extra bytes come from?
3. `TCPDriverComm` sends an NBD reply. The client is on a big-endian SPARC machine. You forgot `htonl` on the error code. The client reads error code `0x01000000` instead of `0x00000001`. Describe exactly what happened at the byte level.

## Connections

**Theory:** [[Core/Domains/02 - C/Theory/07 - Serialization]]  
**Mental Models:** [[TCP Sockets — The Machine]], [[UDP Sockets — The Machine]], [[Strings — The Machine]], [[Pointers — The Machine]], [[Bitwise Operations — The Machine]]  
**LDS Implementation:** [[LDS/Architecture/Wire Protocol Spec]] — NBD request/reply wire format  
**Runtime Machines:** [[LDS/Runtime Machines/NBDDriverComm — The Machine]], [[LDS/Runtime Machines/TCPDriverComm — The Machine]]  
**Glossary:** [[MSG_ID]]
