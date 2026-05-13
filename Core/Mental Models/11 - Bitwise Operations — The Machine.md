# Bitwise Operations — The Machine

## The Model
Direct manipulation of the individual light switches inside a number. Each bit is a physical on/off switch. AND, OR, XOR, NOT are operations that combine or flip switches. Shift moves all switches left or right. This is the language of hardware protocols and flags.

## How It Moves

```
AND  (&):  both switches must be ON
  1010 & 1100 = 1000   (bit 3 was on in both → stays on)

OR   (|):  either switch ON
  1010 | 1100 = 1110   (any bit that was on in either → on)

XOR  (^):  exactly one ON (toggle)
  1010 ^ 1100 = 0110   (bits that differ → on)

NOT  (~):  flip everything
  ~1010 = 0101

LEFT SHIFT  (<<): multiply by 2^n
  0001 << 3 = 1000   (1 → 8)

RIGHT SHIFT (>>): divide by 2^n
  1000 >> 2 = 0010   (8 → 2)
```

**WHY this exists:** The NBD protocol header packs multiple fields into a 32-bit integer. Bitwise operations extract or set individual fields without touching the others.

## The Blueprint

**Common patterns:**
```c
// Pack multiple booleans into one int (flags):
#define FLAG_READ  (1 << 0)  // 0001
#define FLAG_WRITE (1 << 1)  // 0010
#define FLAG_FLUSH (1 << 2)  // 0100

int flags = FLAG_READ | FLAG_FLUSH;   // set flags
bool is_read = flags & FLAG_READ;     // test a flag
flags &= ~FLAG_READ;                  // clear a flag
flags ^= FLAG_WRITE;                  // toggle a flag

// Extract a field from packed bits:
uint32_t header = 0xABCD1234;
uint16_t type = (header >> 16) & 0xFFFF;   // top 16 bits
uint16_t cmd  = header & 0xFFFF;           // bottom 16 bits
```

## Where It Breaks

- **Signed right shift**: shifting a negative `int` is implementation-defined in C/C++. Use `uint32_t` for bitfield manipulation.
- **Operator precedence**: `a & b == c` is parsed as `a & (b == c)` — always parenthesise.
- **Off-by-one in shifts**: `1 << 31` on a 32-bit signed int overflows (UB). Use `1U << 31`.

## In LDS

`services/communication_protocols/nbd/include/IDriverComm.hpp`

The NBD protocol uses a packed request structure. The request type field (`NBD_CMD_READ = 0`, `NBD_CMD_WRITE = 1`, `NBD_CMD_DISC = 2`, `NBD_CMD_FLUSH = 3`) is extracted from the raw 32-bit header using masking. The LDS Reactor dispatches to `Read`, `Write`, or `Flush` handlers based on this extracted type value.

## Validate

1. The NBD header has `flags` in bits 16–31 and `type` in bits 0–15 of a 32-bit word. Write the expression to extract `type`.
2. You want to test if `FLAG_WRITE` is set in `flags` without disturbing other bits. Write the expression.
3. `1 << 0` is 1, `1 << 1` is 2, `1 << 2` is 4. Why does this doubling pattern mean bit flags never collide?

## Connections

**Theory:** [[Core/Theory/C/06 - Bitwise Operations]]  
**Mental Models:** [[Serialization — The Machine]], [[Structs and Unions — The Machine]]  
**LDS Implementation:** [[LDS/Architecture/Wire Protocol Spec]] — flags and type field extraction  
**Runtime Machines:** [[LDS/Runtime Machines/NBDDriverComm — The Machine]]
