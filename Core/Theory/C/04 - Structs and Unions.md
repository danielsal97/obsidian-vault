# Structs and Unions

---

## Struct — Grouping Data

A struct groups related variables into one unit. Each field has its own memory location.

```c
struct Point {
    int x;
    int y;
};

struct Point p;
p.x = 3;
p.y = 4;

// Initialize with compound literal:
struct Point p = {3, 4};
struct Point p = {.x = 3, .y = 4};  // designated initializer (C99)
```

---

## Memory Layout and Padding

The compiler adds padding between fields to align each field to its natural alignment (typically `sizeof(field)` bytes).

```c
struct Example {
    char  a;    // 1 byte at offset 0
                // 3 bytes padding (to align int to 4-byte boundary)
    int   b;    // 4 bytes at offset 4
    char  c;    // 1 byte at offset 8
                // 3 bytes padding (struct size rounded up to alignment of largest member)
};
// sizeof(Example) = 12, not 6
```

**Why alignment matters:** misaligned reads are slower (or cause a fault on ARM). The CPU reads memory in aligned chunks.

**Minimize padding — order fields largest to smallest:**
```c
struct Efficient {
    int   b;    // 4 bytes at offset 0
    char  a;    // 1 byte at offset 4
    char  c;    // 1 byte at offset 5
                // 2 bytes padding
};
// sizeof = 8, not 12
```

**Packed struct — remove all padding:**
```c
struct __attribute__((packed)) Header {
    uint8_t  type;    // 1 byte
    uint64_t offset;  // 8 bytes
    uint32_t length;  // 4 bytes
};
// sizeof = 13 — exactly what you send over the wire
// Warning: misaligned access — only use for serialization
```

---

## Struct Pointer

```c
struct Point* pp = &p;
(*pp).x = 5;   // dereference then access
pp->x = 5;     // arrow operator — same thing, cleaner syntax
```

**Passing structs to functions:**
```c
// By value — copies entire struct (expensive for large structs):
void print(struct Point p) { printf("%d %d\n", p.x, p.y); }

// By pointer — no copy, just 8 bytes:
void print(const struct Point* p) { printf("%d %d\n", p->x, p->y); }
```

Always pass large structs by pointer. Use `const` if you don't modify them.

---

## Typedef

```c
typedef struct Point {
    int x;
    int y;
} Point;

Point p;         // no need for 'struct' keyword
Point* pp = &p;
```

In C++ this is automatic — `struct` keyword not needed. In C, `typedef` is the convention.

---

## Opaque Struct (Information Hiding)

Hide implementation details — callers only see a pointer, not the contents:

```c
// scheduler.h — public interface:
typedef struct Scheduler Scheduler;   // forward declaration only
Scheduler* SchedulerCreate(void);
void SchedulerDestroy(Scheduler* s);
void SchedRun(Scheduler* s);

// scheduler.c — private implementation:
struct Scheduler {
    heap_pq_t* pq;
    int to_stop;
    // ...
};
```

Callers cannot access `pq` or `to_stop` — only through the API. This is C's version of encapsulation.

---

## Flexible Array Member

A struct with an array of unknown size at the end (C99):

```c
struct Packet {
    uint32_t length;
    uint8_t  data[];   // no size — must be last member
};

// Allocate for header + data:
struct Packet* p = malloc(sizeof(struct Packet) + data_len);
p->length = data_len;
memcpy(p->data, src, data_len);
```

Used in network protocols and message passing.

---

## Union — Shared Memory

All fields of a union occupy the **same** memory. Size = size of largest field.

```c
union Value {
    int   i;
    float f;
    char  bytes[4];
};

union Value v;
v.i = 42;
// v.f and v.bytes[0..3] now contain the same 4 bytes interpreted differently
```

**Use case — type punning (reading the bytes of a float as an int):**
```c
union FloatInt {
    float f;
    uint32_t i;
};
union FloatInt u = {.f = 3.14f};
printf("%08x\n", u.i);   // bit pattern of 3.14
```

**Tagged union — safe variant type:**
```c
typedef enum { TYPE_INT, TYPE_FLOAT, TYPE_STRING } Tag;

struct Variant {
    Tag tag;
    union {
        int    i;
        float  f;
        char*  s;
    } value;
};

// Usage:
struct Variant v = {TYPE_INT, {.i = 42}};
if (v.tag == TYPE_INT) printf("%d\n", v.value.i);
```

C++17's `std::variant` is the type-safe version of this pattern.

---

## Bit Fields

Pack multiple small values into one integer:

```c
struct Flags {
    unsigned int read    : 1;   // 1 bit
    unsigned int write   : 1;   // 1 bit
    unsigned int execute : 1;   // 1 bit
    unsigned int unused  : 5;   // 5 bits padding
};   // total: 8 bits = 1 byte

struct Flags f = {1, 0, 1};
f.write = 1;
```

Used in hardware registers, protocol headers, flag sets. Layout is implementation-defined — not portable across compilers for serialization.

---

## Understanding Check

> [!question]- Why does the compiler insert padding between struct fields, and why does reordering fields (largest to smallest) reduce struct size?
> Every field must be stored at an address that is a multiple of its own size — this is natural alignment, required for efficient (or even correct) CPU load/store instructions. When a small field (e.g., `char`) precedes a larger one (e.g., `int`), the compiler inserts padding bytes to push the `int` to the next 4-byte boundary. Placing the largest fields first means no padding is needed between them; smaller fields that follow can pack together in the leftover space. This matters for structs stored in large arrays where each wasted padding byte is multiplied by the element count.

> [!question]- What goes wrong if you use a union and read from a field you didn't most recently write?
> Reading a union field other than the last-written one is type punning. In C, this is technically allowed for reading the underlying byte representation, but the value you read is whatever bits the last write put there, interpreted as a completely different type. Reading `float f` after writing `int i` gives you the float whose bit pattern happens to equal that integer — not a meaningful floating-point number. In C++, reading any union member other than the active one is undefined behavior. The safe pattern is to always use a tag (tagged union) so you know which member is active.

> [!question]- What goes wrong if you `memcpy` an opaque struct pointer across a network boundary instead of serializing each field?
> The receiving side gets the raw in-memory bytes, which includes compiler-inserted padding, host-byte-order integers, and possibly pointer values that are meaningless on another machine. Even between two identical machines running the same binary, padding bytes have indeterminate values — so the comparison `memcmp(a, b, sizeof(Struct))` can return non-zero even when all logical fields are equal, because the padding differs. For the LDS wire protocol, each field must be written explicitly in network byte order with no padding.

> [!question]- The LDS protocol uses a flexible array member pattern (`uint8_t data[]`) for variable-length packets. What is the one invariant you must maintain when allocating one, and what happens if you violate it?
> You must allocate `sizeof(struct Packet) + data_len` bytes — never just `sizeof(struct Packet)`. The flexible array member contributes zero bytes to `sizeof`, so allocating only the struct size leaves no space for the data. Writing into `p->data[]` then immediately overflows into adjacent heap metadata or stack memory, corrupting the allocator's free list or causing a segfault. The length field must also faithfully reflect how many bytes were allocated for `data`, so any code reading the struct knows how far it can safely access.

> [!question]- An opaque struct hides its fields behind a forward declaration. What does this guarantee at the callsite, and when does it break down?
> The compiler only sees the pointer type, not the struct contents, so callers cannot access fields directly — this enforces the API boundary and lets you change the implementation without recompiling callers. It breaks down in two ways: (1) if you expose the struct definition in a public header (accidentally or for inline performance), the encapsulation is gone; (2) if a caller casts the pointer to `void*` or `char*` and interprets the raw bytes, they've bypassed the abstraction. The guarantee is only as strong as the discipline not to cast around it.
