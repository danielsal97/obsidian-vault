# Memory — malloc and free

---

## The Heap

The heap is a region of memory managed manually by the programmer. Unlike the stack (automatic), heap memory persists until you explicitly free it.

The OS gives the process memory in pages (4KB chunks). `malloc` manages these pages internally, subdividing them into blocks and handing out pointers.

---

## malloc / calloc / realloc / free

```c
#include <stdlib.h>

// malloc — allocate n bytes, uninitialized (may contain garbage)
void* p = malloc(n);
if (!p) { /* handle allocation failure */ }

// calloc — allocate n*size bytes, zeroed
void* p = calloc(n, sizeof(int));

// realloc — resize an existing allocation
// may move the block — old pointer may be invalid after this call
void* p2 = realloc(p, new_size);
if (!p2) { /* p is still valid, handle error */ }
else { p = p2; }

// free — release the allocation
free(p);
p = NULL;   // good practice — prevents accidental use-after-free
```

---

## How malloc Works Internally

malloc maintains a **free list** — a data structure tracking available memory blocks.

**On `malloc(n)`:**
1. Search free list for a block ≥ n bytes
2. If found: split it if much larger, return pointer
3. If not found: ask OS for more pages (`sbrk()` or `mmap()`)

**On `free(p)`:**
1. Add block back to free list
2. Coalesce with adjacent free blocks (reduce fragmentation)

**Hidden metadata:** every allocated block has a small header before the returned pointer storing the block size. This is why `free(p)` doesn't need a size argument.

```
[size | flags][  your data  ][size | flags][  next block  ]
              ^
              p = what malloc returns
```

---

## Fragmentation

**External fragmentation:** many small free blocks exist, but no single block is large enough for a new request.

```
[used 100B][free 10B][used 50B][free 10B][used 100B]
Request for 20B → fails even though 20B is free total
```

**Internal fragmentation:** allocated block is larger than requested (due to alignment/minimum block size).

---

## Common Errors

**Memory leak — malloc without free:**
```c
void f() {
    int* p = malloc(100);
    // ... forgot to free
}   // p is gone, memory is leaked — wasted until process exits
```

**Use-after-free:**
```c
int* p = malloc(sizeof(int));
free(p);
*p = 5;   // undefined behavior — p points to freed memory
          // could corrupt malloc's internal structures
```

**Double free:**
```c
free(p);
free(p);   // undefined behavior — corrupts free list
```

**Buffer overflow:**
```c
int* p = malloc(5 * sizeof(int));
p[5] = 99;   // off-by-one — writes into adjacent block's metadata
```

**Forgetting to check NULL:**
```c
int* p = malloc(1024 * 1024 * 1024);  // 1GB — may fail
p[0] = 1;   // crash if malloc returned NULL
```

---

## Correct Patterns

**Always check malloc return value:**
```c
int* arr = malloc(n * sizeof(int));
if (!arr) {
    perror("malloc");
    return -1;
}
```

**Sizeof the variable, not the type:**
```c
// Fragile — must update if type changes:
int* p = malloc(sizeof(int));

// Robust — type always matches:
int* p = malloc(sizeof(*p));
```

**Free and null in one step:**
```c
free(p);
p = NULL;
```

---

## Custom Allocators

When `malloc` is too slow or causes fragmentation:

**Fixed-Size Allocator (FSA):**
- Pre-allocate a pool of same-size chunks
- `alloc` = pop from free list → O(1)
- `free` = push to free list → O(1)
- Zero fragmentation — all chunks same size
- Used in: network packet pools, task queues, node allocators for linked lists

**Arena/Region Allocator:**
- Allocate from a large pre-allocated buffer, bumping a pointer
- `alloc` = bump pointer → O(1)
- `free` = does nothing — free the entire arena at once
- Used in: request handling (allocate for request lifetime, free all at end), compilers, parsers

**Pool Allocator:**
- Multiple FSAs for different sizes
- Handles varied allocation sizes with low overhead

---

## Tools to Detect Memory Errors

**Valgrind:**
```bash
valgrind --leak-check=full --track-origins=yes ./program
```
Detects: leaks, use-after-free, uninitialized reads. Slow (20x).

**AddressSanitizer:**
```bash
g++ -fsanitize=address -g main.cpp -o program && ./program
```
Detects: use-after-free, buffer overflow, leaks. Fast (2x).

**Electric Fence / libefence:**
Places a protected page after every allocation — immediate segfault on overflow.

---

## Understanding Check

> [!question]- Why doesn't `free` need a size argument, and what can go wrong with the hidden metadata it relies on?
> `malloc` stores the block size in a small header just before the pointer it returns. When you call `free(p)`, the implementation steps back a few bytes to read that header and learn the block size. This is why writing before the start of an allocation (`p[-1] = 0`) or overflowing the end (`p[n] = 0` for an n-element array) corrupts the heap metadata. The next `malloc` or `free` reads that corrupted header, misinterprets the block size or free-list pointers, and the heap becomes inconsistent — typically producing a delayed crash or silent memory corruption far from the original bad write.

> [!question]- What goes wrong if you use the pattern `p = realloc(p, new_size)` and realloc fails?
> If `realloc` returns NULL on failure, you've overwritten `p` with NULL while the original allocation is still live and unreachable — a memory leak on top of the failure. The correct pattern is `void* tmp = realloc(p, new_size); if (!tmp) { /* handle error, p is still valid */ } else { p = tmp; }`. Only assign the result back to `p` after confirming it is non-NULL.

> [!question]- Why might an arena allocator be a better fit than `malloc`/`free` for handling a single LDS request, and what does "free" mean in that context?
> Each LDS request involves multiple small allocations (header buffers, response structs, temporary strings) that all share the same lifetime — they're all needed until the response is sent, then all discarded. With `malloc`/`free` each allocation is independent, requiring careful tracking to avoid leaks. An arena allocator pre-allocates one large block at request start; each sub-allocation is just a pointer bump (O(1), no fragmentation). At request end, the entire arena is discarded in one operation. "Free" for an arena means resetting a pointer to the start of the pool — no individual bookkeeping needed.

> [!question]- What is the difference between external and internal fragmentation, and which one does a fixed-size allocator (FSA) eliminate entirely?
> External fragmentation is free memory that exists in too many small scattered chunks to satisfy a large request. Internal fragmentation is allocated memory that is larger than the request (the surplus is wasted inside the block). An FSA eliminates external fragmentation entirely: because every slot is the same size, any free slot can satisfy any request — there are no "wrong size" chunks. However, if the actual data is smaller than the slot size, you have internal fragmentation for every allocation. FSAs trade away flexibility to guarantee that free memory is always usable.

> [!question]- `calloc(n, size)` zeroes its memory while `malloc` does not. Beyond convenience, why might calloc be semantically important rather than just a shortcut for malloc + memset?
> `calloc` can be more efficient than `malloc` + `memset` because the OS already delivers freshly-mapped pages zeroed (for security — no previous process's data should leak). A smart `calloc` implementation can detect that a block came directly from the OS and skip the memset. More importantly, uninitialized memory from `malloc` contains whatever bytes were in that location before — reading it is undefined behavior. Using `calloc` is a correctness guarantee: every byte is a defined zero, so code that reads fields before writing them (e.g., a struct with only some fields initialized) doesn't invoke UB through an uninitialized read.
