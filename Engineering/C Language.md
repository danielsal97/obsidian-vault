# C Language Fundamentals

*Quick reference — condensed summaries only. For full coverage with examples, edge cases, and Understanding Check Q&A, see the [[C/]] topic files linked in [[00 Dashboard]].*

---

## Pointers

A pointer stores a memory address. The type tells the compiler how many bytes to read/write at that address.

```c
int x = 5;
int* p = &x;    // p holds the address of x
*p = 10;        // dereference — writes to x through p
```

**Pointer arithmetic:** incrementing a pointer moves it by `sizeof(type)` bytes, not 1 byte.
```c
int arr[3] = {1, 2, 3};
int* p = arr;
p++;   // now points to arr[1] — moved 4 bytes forward (sizeof int)
```

**Double pointer:** pointer to a pointer. Used when a function needs to modify a pointer itself.
```c
void alloc(int** pp) {
    *pp = malloc(sizeof(int));
}
int* p = NULL;
alloc(&p);   // p now points to allocated memory
```

**Function pointer:** stores the address of a function. Used for callbacks.
```c
int add(int a, int b) { return a + b; }

int (*fn)(int, int) = add;   // fn is a pointer to a function taking two ints
fn(3, 4);                    // calls add(3, 4)

// Cleaner with typedef:
typedef int (*BinaryOp)(int, int);
BinaryOp op = add;
```

**Void pointer:** generic pointer, no type. Must cast before use.
```c
void* p = malloc(100);
int* ip = (int*)p;
```

---

## Memory — malloc / free

```c
int* p = malloc(sizeof(int) * 10);   // allocate 10 ints on heap
if (!p) { /* malloc returns NULL on failure */ }
free(p);    // release — must call exactly once
p = NULL;   // good practice — prevents use-after-free
```

| Function | Behaviour |
|---|---|
| `malloc(n)` | Allocate n bytes, uninitialized |
| `calloc(n, size)` | Allocate n*size bytes, zeroed |
| `realloc(p, n)` | Resize allocation — may move it |
| `free(p)` | Release allocation |

**Common mistakes:**
- **Memory leak** — `malloc` without `free`
- **Double free** — `free(p)` twice → undefined behavior
- **Use-after-free** — access memory after `free` → undefined behavior
- **Buffer overflow** — write past the end of allocation → undefined behavior

---

## Structs and Memory Layout

```c
struct Point {
    char  a;    // 1 byte
    // 3 bytes padding (compiler aligns int to 4-byte boundary)
    int   b;    // 4 bytes
    char  c;    // 1 byte
    // 3 bytes padding (struct size must be multiple of largest member)
};
// sizeof(Point) = 12, not 6
```

**Why padding?** CPU reads aligned addresses faster. Misaligned reads may fault on some architectures.

**Packed struct** (no padding, use carefully):
```c
struct __attribute__((packed)) Header {
    uint8_t  type;
    uint64_t offset;
    uint32_t length;
};  // sizeof = 13 — no padding
```

---

## Preprocessor

Runs before compilation. Text substitution only — no type checking.

```c
#define MAX 100             // constant — prefer const in C++
#define SQ(x) ((x)*(x))    // macro function — always parenthesize args

#include "file.h"           // paste file contents here
#ifndef __MYFILE_H__        // header guard — prevent double inclusion
#define __MYFILE_H__
...
#endif
```

**Macro pitfall:**
```c
#define SQ(x) x*x
SQ(1+2)   // expands to 1+2*1+2 = 5, not 9
// Fix: #define SQ(x) ((x)*(x))
```

---

## Strings in C

A string is a `char` array terminated by `'\0'` (null byte).

```c
char s[] = "hello";   // s = {'h','e','l','l','o','\0'} — 6 bytes
strlen(s);            // 5 — does not count null terminator
sizeof(s);            // 6 — counts null terminator
```

**Safe copy:**
```c
strncpy(dst, src, sizeof(dst) - 1);  // copy at most n-1 bytes
dst[sizeof(dst) - 1] = '\0';         // always null-terminate manually
// strcpy is unsafe — no bounds check
```

---

## Undefined Behavior

C does not protect you from invalid operations. The result is undefined — the compiler can do anything, including appearing to work correctly in debug mode and crashing in release.

Common UB:
- Signed integer overflow
- Out-of-bounds array access
- Use-after-free
- Null pointer dereference
- Uninitialized variable read
- Modifying a string literal

Use `-fsanitize=undefined` (UBSan) to catch these at runtime.

---

## Common C Patterns

**Callback via function pointer:**
```c
typedef void (*Callback)(int event, void* ctx);

void register_handler(Callback cb, void* ctx) {
    cb(42, ctx);
}
```

**Linked list node:**
```c
typedef struct Node {
    int data;
    struct Node* next;
} Node;
```

**Opaque pointer (hiding implementation):**
```c
// header:
typedef struct MyStruct* MyHandle;
MyHandle create();
void destroy(MyHandle h);

// source:
struct MyStruct { int internal; };
```

---

## C vs C++

| C | C++ |
|---|---|
| `malloc`/`free` | `new`/`delete` (prefer smart pointers) |
| Function pointers | `std::function`, lambdas |
| `struct` (no methods) | `class`/`struct` with methods |
| No RAII | RAII via constructors/destructors |
| No exceptions | Exceptions |
| No namespaces | `namespace` |
| `NULL` | `nullptr` |
