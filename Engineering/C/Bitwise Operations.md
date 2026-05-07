# Bitwise Operations

Operate directly on the bits of an integer. Used in systems programming for flags, masks, hardware registers, protocols, and performance-critical code.

---

## The Six Operators

```c
a & b    // AND  — bit is 1 only if both are 1
a | b    // OR   — bit is 1 if either is 1
a ^ b    // XOR  — bit is 1 if they differ
~a       // NOT  — flip all bits
a << n   // left shift  — multiply by 2^n
a >> n   // right shift — divide by 2^n (arithmetic for signed, logical for unsigned)
```

---

## AND — Masking / Testing Bits

```c
uint8_t flags = 0b10110101;
uint8_t mask  = 0b00001111;   // lower 4 bits

flags & mask;   // 0b00000101 — extract lower nibble
flags & 0x01;   // test bit 0: result is 1 if set, 0 if not

// Check if a specific bit is set:
#define BIT(n) (1u << (n))
if (flags & BIT(2)) { /* bit 2 is set */ }
```

---

## OR — Setting Bits

```c
uint8_t flags = 0b00000000;
flags |= BIT(3);   // set bit 3  → 0b00001000
flags |= BIT(0);   // set bit 0  → 0b00001001
```

---

## XOR — Toggling Bits / Swap

```c
flags ^= BIT(3);   // toggle bit 3

// XOR swap (no temp variable):
a ^= b;
b ^= a;
a ^= b;
// a and b are swapped — works but confusing, avoid in real code

// XOR to detect difference:
if ((a ^ b) & mask) { /* bits in mask differ between a and b */ }
```

---

## NOT — Clearing Bits

```c
flags &= ~BIT(3);   // clear bit 3
// ~BIT(3) = ~0b00001000 = 0b11110111 — all bits set except bit 3
// AND with flags clears only bit 3
```

---

## Shift — Multiply and Divide by Powers of 2

```c
1 << 0  = 1
1 << 1  = 2
1 << 8  = 256
1 << 10 = 1024   // 1KB

x << n   // x * 2^n (faster than multiplication)
x >> n   // x / 2^n (for unsigned; arithmetic shift for signed)

// Extract byte N from a multi-byte value:
uint32_t val = 0xDEADBEEF;
uint8_t byte0 = (val >> 0)  & 0xFF;   // 0xEF
uint8_t byte1 = (val >> 8)  & 0xFF;   // 0xBE
uint8_t byte2 = (val >> 16) & 0xFF;   // 0xAD
uint8_t byte3 = (val >> 24) & 0xFF;   // 0xDE
```

---

## Common Patterns

**Check if power of 2:**
```c
bool is_power_of_2(unsigned n) {
    return n && !(n & (n - 1));
}
// If n is a power of 2: binary has exactly one 1 bit
// n-1 flips all lower bits: n & (n-1) == 0
```

**Round up to next power of 2:**
```c
uint32_t next_pow2(uint32_t n) {
    n--;
    n |= n >> 1; n |= n >> 2; n |= n >> 4;
    n |= n >> 8; n |= n >> 16;
    return n + 1;
}
```

**Count set bits (popcount):**
```c
int popcount(uint32_t n) {
    int count = 0;
    while (n) { count += n & 1; n >>= 1; }
    return count;
}
// Or use __builtin_popcount(n) — single CPU instruction
```

**Swap nibbles:**
```c
uint8_t swap_nibbles(uint8_t x) {
    return (x << 4) | (x >> 4);
}
```

**Byte order reversal:**
```c
uint32_t bswap32(uint32_t x) {
    return ((x & 0xFF000000) >> 24) |
           ((x & 0x00FF0000) >> 8)  |
           ((x & 0x0000FF00) << 8)  |
           ((x & 0x000000FF) << 24);
}
// Or use __builtin_bswap32(x) — single instruction
// This is what htonl/ntohl do internally
```

---

## Flags / Bitmask Pattern

```c
// Define flags as powers of 2:
#define FLAG_READ    (1 << 0)   // 0x01
#define FLAG_WRITE   (1 << 1)   // 0x02
#define FLAG_EXEC    (1 << 2)   // 0x04

// Combine:
int perms = FLAG_READ | FLAG_WRITE;   // 0x03

// Test:
if (perms & FLAG_READ)  { /* can read */ }
if (perms & FLAG_WRITE) { /* can write */ }

// Add:
perms |= FLAG_EXEC;

// Remove:
perms &= ~FLAG_WRITE;

// Toggle:
perms ^= FLAG_READ;
```

---

## Signed vs Unsigned Shift

```c
// Right shift on signed integers is implementation-defined:
int x = -8;
x >> 1;   // usually -4 (arithmetic shift — fills with sign bit)
          // but NOT guaranteed by C standard

// Always use unsigned for bit manipulation:
unsigned int x = 0xFFFFFFFF;
x >> 1;   // 0x7FFFFFFF — logical shift, fills with 0
```

---

## Useful Builtins (GCC/Clang)

```c
__builtin_popcount(x)    // count set bits
__builtin_clz(x)         // count leading zeros
__builtin_ctz(x)         // count trailing zeros
__builtin_parity(x)      // parity (XOR of all bits)
__builtin_bswap32(x)     // byte swap 32-bit
__builtin_bswap64(x)     // byte swap 64-bit
```

These compile to a single CPU instruction on modern hardware.
