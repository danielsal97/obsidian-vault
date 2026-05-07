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
