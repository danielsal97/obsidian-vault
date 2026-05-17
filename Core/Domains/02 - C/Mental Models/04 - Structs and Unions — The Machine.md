# Structs and Unions — The Machine

## The Model
A struct is a multi-compartment toolbox where every drawer exists simultaneously, each holding its own labeled item. A union is a single drawer that can hold a hammer, a wrench, or a screwdriver — but only one at a time, and the drawer is sized for the largest possible tool.

## How It Moves

**Struct — all compartments live simultaneously:**
```
struct Point {
    int x;    // compartment at offset 0
    int y;    // compartment at offset 4
    int z;    // compartment at offset 8
};            // total size: 12 bytes

MEMORY LAYOUT:
┌────────────┬────────────┬────────────┐
│  x (4 B)   │  y (4 B)   │  z (4 B)   │
│  offset=0  │  offset=4  │  offset=8  │
└────────────┴────────────┴────────────┘
```

**Union — one compartment, multiple personalities:**
```
union Payload {
    uint32_t  as_int;    // 4 bytes
    float     as_float;  // 4 bytes
    char      as_bytes[4]; // 4 bytes
};

MEMORY LAYOUT (ALL share the SAME 4 bytes):
┌──────────────────────────────────────┐
│              4 bytes                 │
│  as_int    OR as_float OR as_bytes   │
└──────────────────────────────────────┘
```

**Padding — why the toolbox has spacers:**
```
struct Padded {
    char  a;     // 1 byte at offset 0
    // 3 bytes padding ← CPU wants int on 4-byte boundary
    int   b;     // 4 bytes at offset 4
    char  c;     // 1 byte at offset 8
    // 3 bytes padding ← struct size must be multiple of largest member
};               // total: 12 bytes, not 6

WHY: x86/ARM CPUs read 4-byte values most efficiently when the address
     is divisible by 4. Misaligned read = 2 bus transactions instead of 1,
     or a hardware fault on strict-alignment architectures (ARM).
```

**Avoiding waste with ordering:**
```
struct Tight {
    int   b;     // 4 bytes at offset 0
    char  a;     // 1 byte at offset 4
    char  c;     // 1 byte at offset 5
    // 2 bytes padding
};               // total: 8 bytes  (vs 12 above)
Rule: order members largest → smallest to minimize padding.
```

## The Blueprint

- **`offsetof(type, member)`**: returns byte offset of a member. Crucial for protocol parsing when you need to address fields directly.
- **`sizeof(struct)`**: includes all padding. Never assume it equals the sum of members.
- **`__attribute__((packed))` / `#pragma pack(1)`**: removes padding. Used in network protocols where wire format must be exact. Cost: unaligned access penalty on every read.
- **Struct copy**: assigning one struct to another copies all bytes including padding (undefined content, but harmless).
- **Union use cases**: (1) type-punning to inspect raw bytes of a float; (2) variant types (tagged unions); (3) protocol parsing where the same bytes mean different things based on a type field.
- **Tagged union pattern**:
```cpp
struct Message {
    uint32_t type;        // tells you which field is valid
    union {
        uint32_t read_len;
        uint32_t error_code;
    } data;
};
```

## Where It Breaks

- **Uninitialized padding**: `memcmp` on two structs with identical fields can return non-zero if padding bytes differ. Breaks hash-based equality.
- **`__attribute__((packed))` trap**: you take `&member` and pass it to a function expecting aligned access. On ARM, this is a bus error at runtime. On x86, it's just slow.
- **Union type confusion**: you write `as_float`, then read `as_int`. The bits are valid but the interpretation is different — this is only defined behavior if you use `memcpy` to type-pun in C++.
- **Struct size assumptions in protocols**: sender and receiver compiled with different padding rules. `sizeof` mismatch causes misaligned reads across the wire.

## In LDS

**`TCPDriverComm.cpp` lines 114–120** — `RequestHeader` is a `__attribute__((packed))` struct used to parse the exact wire format of incoming TCP requests. Padding is explicitly removed so bytes map 1:1 to the protocol:

```cpp
// services/communication_protocols/tcp/src/TCPDriverComm.cpp  line 113
struct RequestHeader {
    uint32_t type;
    uint64_t handle;
    uint64_t offset;
    uint32_t len;
} __attribute__((packed));
```

Without `__attribute__((packed))`, the compiler would insert 4 bytes of padding between `type` and `handle` (to align `uint64_t` on an 8-byte boundary), causing `ReadAll` to read the wrong bytes for every field.

**`DriverData.hpp` lines 18–48** — `DriverData` is a plain struct (no packing) that acts as the internal toolbox: all compartments (`m_type`, `m_handle`, `m_offset`, `m_len`, `m_buffer`) coexist and are accessed independently by storage and driver layers.

## Validate

1. Given `struct S { char a; double b; char c; }`, what is `sizeof(S)` on a 64-bit system? Now reorder the fields to minimize size. What is the new `sizeof`?
2. Why does `TCPDriverComm` use `__attribute__((packed))` on `RequestHeader` but `DriverData` has no such attribute? What breaks if you add `__attribute__((packed))` to `DriverData`?
3. If you `memset` a packed `RequestHeader` to zero and then `ReadAll` fills it from a TCP socket, can you safely take `&header.handle` and pass it to a function expecting `uint64_t*`? Why or why not on ARM vs x86?

## Connections

**Theory:** [[07 - Serialization]] (covers wire-format structs)  
**Mental Models:** [[Serialization — The Machine]], [[Memory Ordering — The Machine]], [[Bitwise Operations — The Machine]]  
**LDS Implementation:** [[LDS/Architecture/Wire Protocol Spec]] — RequestHeader packed struct; [[LDS/Linux Integration/TCPServer]]
