# Strings — The Machine

## The Model
A C string is a chain of numbered rooms ending with a sealed empty room (the null terminator `\0`). `strlen` walks the chain counting rooms until it hits the seal. `strcpy` copies rooms one by one until it copies the seal. There is no lock on the chain — nothing stops you from walking past the seal into someone else's rooms.

## How It Moves

```
char s[] = "hello";

 s[0] s[1] s[2] s[3] s[4] s[5]
  'h'  'e'  'l'  'l'  'o'  '\0'  ← seal

strlen(s) = 5   (counts until '\0', does not count the seal)
sizeof(s) = 6   (counts all rooms including the seal)

strcpy(dst, s):  copies h,e,l,l,o,\0 into dst
                 if dst has only 4 rooms → writes into rooms 4,5 → OVERFLOW
```

**`std::string` vs C string:** `std::string` is a machine that manages the chain automatically. It tracks length separately (so `size()` is O(1), not O(n) like `strlen`). It owns the heap buffer and destructs it automatically. The `.c_str()` method exposes the raw chain when you need to pass it to a C API.

## The Blueprint

```cpp
// DANGEROUS — no bounds check:
char buf[8];
strcpy(buf, user_input);   // user_input could be 1000 bytes → overflow

// SAFER — bounded:
strncpy(buf, user_input, sizeof(buf) - 1);
buf[sizeof(buf) - 1] = '\0';   // strncpy doesn't guarantee null termination!

// BEST — use std::string:
std::string s = user_input;   // owns its memory, auto-sized
```

- `strcmp(a, b)`: returns 0 if equal, <0 if a < b, >0 if a > b. Does NOT return true/false.
- `strstr(haystack, needle)`: returns pointer to first occurrence, or NULL.
- `memcpy(dst, src, n)`: copies exactly n bytes — no null terminator logic. Use for binary data.
- `memset(buf, 0, n)`: fills n bytes with zero. Used to clear buffers before reading into them.

## Where It Breaks

- **Buffer overflow**: writing past the end of a fixed-size buffer tramples adjacent memory (stack variables, return addresses, heap metadata)
- **Missing null terminator**: a buffer filled with `memcpy` that doesn't add `\0` → `strlen` walks past the buffer → reads garbage until it finds a zero byte somewhere
- **`strncpy` trap**: `strncpy` does NOT null-terminate if the source is longer than n — you must add `\0` manually

## In LDS

`services/communication_protocols/tcp/src/TCPDriverComm.cpp`

TCP data arrives as raw bytes. The `RecvAll` loop reads into a `char` buffer using `recv()`. The received data is NOT a null-terminated C string — it's a binary protocol buffer. LDS uses `memcpy` and explicit length fields, not string functions, to parse it. Using `strlen` on a binary buffer would walk until it found a zero byte anywhere in the packet — a classic protocol parsing bug.

## Validate

1. `char buf[16]; memcpy(buf, data, 16);` — then you pass `buf` to `strlen`. What's the result if none of the 16 bytes is `\0`?
2. The NBD request header is 28 bytes of binary data. Why is it wrong to use `strcmp` to compare two NBD headers?
3. `std::string` in LDS: `std::string msg = "read request";` — where is the `std::string` object? Where is the character data `"read request"`?

## Connections

**Theory:** [[Core/Domains/02 - C/Theory/03 - Strings]]  
**Mental Models:** [[Serialization — The Machine]], [[Pointers — The Machine]], [[Stack vs Heap — The Machine]]  
**LDS Implementation:** [[LDS/Linux Integration/TCPServer]] — binary protocol, not string-based
