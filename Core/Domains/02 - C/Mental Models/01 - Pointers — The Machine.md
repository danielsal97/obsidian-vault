# Pointers — The Machine

## The Model
A sticky note with a room number written on it. The room exists in a warehouse of 2^64 numbered rooms (RAM). The sticky note is not the room — it is the address to find the room.

## How It Moves

```
WAREHOUSE (RAM)
┌────────────┬────────────┬────────────┬────────────┐
│  Room 100  │  Room 101  │  Room 102  │  Room 103  │
│   value=7  │   value=9  │   value=0  │   ...      │
└────────────┴────────────┴────────────┴────────────┘

Sticky note (pointer): [100]  ← address, not the value

int x = 7;         // Allocate room 100, write 7 into it
int* p = &x;       // Write "100" on the sticky note
*p = 42;           // Walk to room 100, write 42
int y = *p;        // Walk to room 100, read 42 → y = 42

POINTER ARITHMETIC
int arr[3] = {10, 20, 30};    // rooms 200, 201, 202 (int = 4 bytes each)
int* q = arr;                 // sticky note says "200"
q + 1;                        // sticky note says "204"  (200 + 1*sizeof(int))
*(q + 2);                     // walk to room 208, read 30
```

**Why pointers exist — the cost without them:**
```
void process(BigStruct s);    // copies entire struct onto stack — expensive
void process(BigStruct* s);   // copies 8 bytes (the sticky note) — cheap
```

**NULL — the forbidden zone:**
```
int* p = nullptr;  // sticky note says "0"
*p = 5;            // walk to room 0 → SEGFAULT (OS protects address 0)
```
Room 0 is reserved by the OS. Any dereference there is a hardware trap.

**Dangling pointer — the evicted room:**
```
int* p;
{
    int x = 7;
    p = &x;        // sticky note says room 100
}                  // x is destroyed — room 100 is now someone else's
*p = 42;           // writing into evicted room — undefined behavior
```

## The Blueprint

- **Address vs value**: `p` holds an address (8 bytes on 64-bit). `*p` is the value at that address.
- **Size of pointer**: always `sizeof(void*) = 8` bytes on 64-bit, regardless of what it points to.
- **`&` operator**: "give me the address of this room" — takes a variable, returns its location.
- **`*` operator (dereference)**: "go to that room and read/write" — takes an address, gives the value.
- **Pointer arithmetic**: `p + n` moves by `n * sizeof(*p)` bytes, not `n` bytes. Array indexing is pointer arithmetic.
- **`const int* p`**: the room content is read-only. `int* const p`: the sticky note is read-only (address fixed).
- **`void*`**: a sticky note with no type — you know the address but not the room's contents. Must cast before dereferencing.
- **Dangling**: pointer to stack memory that has gone out of scope. Address is still written on the note, but the room belongs to someone else.
- **`shared_ptr`**: a sticky note with a counter. The room is freed when the counter reaches zero.

## Program Lifecycle & Memory Flow

Every pointer value is a **virtual address**. The CPU never sees physical RAM directly — the MMU translates on every load/store.

```
*p  (dereference)
    ↓
CPU issues virtual address (e.g. 0x7fff1234)
    ↓
MMU checks TLB (cache of recent virtual→physical translations)
    ├── TLB HIT  → physical address in ~1 cycle → cache lookup
    └── TLB MISS → page table walk (4 levels on x86-64, ~dozens of cycles)
                   ↓
                   PTE found, physical frame known → TLB updated → continue
                   PTE not present → PAGE FAULT
                        ├── valid address (new heap/stack page) → kernel maps frame → resume
                        └── invalid address (null, unmapped gap) → SIGSEGV
```

**What this means for pointer performance:**

| Access pattern | Why | Cost |
|---|---|---|
| `arr[0], arr[1], arr[2]...` | Sequential, cache-friendly | ~1 cycle (L1 hit) |
| Linked list node traversal | Scattered heap pointers, cache cold | ~100–300 cycles (cache miss) |
| Pointer to local variable | Stack, recently accessed, L1 hot | ~1 cycle |
| Pointer to freed memory | Page may be returned to OS | SIGSEGV or silent corruption |

**Pointer lifetime vs allocation lifetime:**  
A pointer is just 8 bytes. It outlives the object it points to if you're not careful. The allocation has a lifetime (stack frame duration, or until `free()`). The pointer has no knowledge of whether that lifetime is over — it's just an integer address.

**NULL = address 0:**  
The kernel never maps address 0. Any dereference of a null pointer hits the unmapped page → MMU raises a fault → OS sends SIGSEGV. This is a hardware guarantee, not a software one.

## Where It Breaks

- **Dangling pointer**: local variable goes out of scope, pointer still used. Writes corrupt unrelated stack frames.
- **Double free**: two pointers to the same heap allocation, both call `delete`. Second `delete` corrupts the allocator's internal bookkeeping.
- **Wild pointer**: pointer never initialized, contains garbage address. Dereference crashes or silently corrupts.
- **NULL dereference**: sticky note says 0, you walk to room 0, kernel sends SIGSEGV.
- **Buffer overrun via pointer arithmetic**: `*(p + 1000)` when the array only has 3 rooms. You walk into someone else's data.

## In LDS

**`ReadAll` / `WriteAll` in `NBDDriverComm.cpp` lines 31–61** — `char* ptr` is a sticky note that walks forward through the receive buffer one chunk at a time:

```cpp
// services/communication_protocols/nbd/src/NBDDriverComm.cpp  line 33
char* ptr = static_cast<char*>(buf);
while (count > 0) {
    ssize_t n = ::read(fd, ptr, count);
    ptr += n;      // advance sticky note forward by n bytes
    count -= n;
}
```

Every call advances the sticky note. The constraint: `ptr` must always point inside the allocated buffer — go past the end and you write into kernel memory (SIGSEGV or UB).

**`TCPDriverComm.cpp` lines 81–94** — identical pattern in `ReadAll`, showing the same pointer-walk idiom for TCP receive.

## Validate

1. You have `int arr[4] = {1,2,3,4}` and `int* p = arr + 1`. What does `*(p + 2)` return? What address does `p - 1` point to?
2. Why does `NBDDriverComm::ReadAll` use `char*` specifically rather than `int*` or `void*` to walk through the buffer? What would break if it used `int*`?
3. In LDS, `ReceiveRequest()` passes `void* buf = &request` to `ReadAll`. The cast to `char*` happens inside `ReadAll`. What contract does the caller guarantee about `buf`'s lifetime — and what would a dangling pointer look like here?

## Connections

**Theory:** [[Core/Domains/02 - C/Theory/01 - Pointers]]  
**Mental Models:** [[Stack vs Heap — The Machine]], [[Process Memory Layout — The Machine]], [[Smart Pointers — The Machine]], [[Serialization — The Machine]]  
**LDS Implementation:** [[LDS/Linux Integration/NBDDriverComm]] — ReadAll pointer-walk pattern
