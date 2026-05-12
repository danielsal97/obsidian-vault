# Stack vs Heap

The two main memory regions a running program uses. Understanding the difference is fundamental to systems programming.

---

## Side-by-Side Comparison

| | Stack | Heap |
|---|---|---|
| Allocation | Automatic (compiler) | Manual (`malloc`/`new`) |
| Deallocation | Automatic (scope exit) | Manual (`free`/`delete`) |
| Speed | O(1) — move a pointer | Slower — find a free block |
| Size | ~8MB default | Limited by RAM |
| Fragmentation | None | Yes, over time |
| Lifetime | Tied to scope | Until explicitly freed |
| Threading | Each thread has its own | Shared between threads |
| Overflow | SIGSEGV | OOM / nullptr |

---

## Stack — How It Works

The CPU has a stack pointer register (`rsp` on x86-64). On function call:
1. Push return address and arguments → `rsp` decremented
2. Function runs — local variables are just offsets from `rsp`
3. Function returns → `rsp` incremented back

```c
void f() {
    int x = 5;        // x is at rsp - 4 (approximately)
    int arr[10];      // arr is at rsp - 44 (approximately)
}   // rsp restored — x and arr "freed" instantly
```

No system call, no searching for free blocks — just decrement a register. This is why stack allocation is O(1) and nearly free.

**Stack frame:** everything a function pushes onto the stack — local vars, saved registers, return address. A deep call chain = many frames stacked.

```
main() frame
  └── f() frame
        └── g() frame   ← rsp is here right now
```

---

## Heap — How It Works

The heap is a large region managed by the C runtime. `malloc` maintains a **free list** of available blocks.

```
Heap memory:
[used 100B | size=100][free 50B | size=50][used 200B | size=200][free 30B | size=30]
              ↑
  malloc's metadata (hidden, before your pointer)
```

On `malloc(n)`:
1. Search free list for a block ≥ n
2. Split it if much larger
3. Return pointer to the data portion

On `free(p)`:
1. Read size from hidden metadata before p
2. Add block back to free list
3. Coalesce with adjacent free blocks

This is why `free(p)` doesn't need a size — it reads it from the metadata.

---

## When to Use Each

**Use stack for:**
- Small, fixed-size objects (local variables, small structs)
- Short-lived data (scoped to a function or block)
- Performance-critical paths (no allocation overhead)

**Use heap for:**
- Objects that outlive the function
- Large data (arrays, buffers)
- Objects whose size is not known at compile time
- Sharing data between functions or threads

---

## Common Mistakes

**Returning pointer to stack variable:**
```c
int* bad() {
    int x = 5;
    return &x;   // x is on stack — gone after return
}

int* p = bad();
*p = 10;   // undefined behavior — writing to dead stack frame
```

**Large array on stack:**
```c
void f() {
    int arr[10000000];   // 40MB — exceeds stack limit → crash
    // Fix: malloc or std::vector
}
```

**Forgetting to free heap:**
```c
void f() {
    int* p = malloc(100);
    if (something) return;   // leak — never freed
    free(p);
}
```

---

## C++ RAII Eliminates the Heap Management Problem

```cpp
void f() {
    std::vector<int> v(1000000);   // heap buffer, but managed by vector
    // ...
}   // vector destructor frees the heap buffer automatically
```

The vector object itself is on the stack — its destructor runs at scope exit, freeing the heap buffer. You get heap capacity with stack lifetime management.

---

## Stack Size Configuration

```bash
ulimit -s          # show stack size limit (KB)
ulimit -s 65536    # increase to 64MB

# Per-thread stack size in C++:
pthread_attr_t attr;
pthread_attr_init(&attr);
pthread_attr_setstacksize(&attr, 16 * 1024 * 1024);  // 16MB per thread
pthread_create(&thread, &attr, fn, arg);
```

---

## Understanding Check

> [!question]- Why is stack allocation O(1) while heap allocation can be O(n) in the worst case?
> Stack allocation is a single instruction: decrement the stack pointer register by the total size of local variables. The compiler calculates the frame size at compile time, so at runtime it is just rsp -= N. Heap allocation requires malloc to search its free list for a block large enough to satisfy the request — in the worst case, it scans the entire free list before finding a fit or requesting more memory from the OS. Modern allocators use size-class bins to make typical allocations fast, but they are never as deterministic as a register decrement.

> [!question]- What goes wrong if you return a pointer to a local variable from a function, and why does it sometimes appear to work?
> The local variable lives in the function's stack frame. When the function returns, the stack pointer moves back up — the frame is "freed" but the bytes are not erased. If you dereference the returned pointer before any other function is called, the bytes may still contain the old value, making the bug invisible. But the next function call overwrites that stack region with its own frame, corrupting whatever the pointer points to. This is undefined behavior: it may silently work for years and then break when the calling code is refactored to add an intermediate function call.

> [!question]- In LDS's thread pool, each worker thread has its own stack — what happens if a worker thread's handler function processes an oversized request that creates a large local buffer?
> Each thread's stack is a fixed-size region (default ~8MB). If a worker function allocates a large local array — say, a 2MB read buffer declared as char buf[2097152] — it consumes a significant portion of that thread's stack. With 8 worker threads each holding such a frame, that is 16MB of stack just for those buffers, and a deep call chain could overflow one thread's stack entirely. The correct approach is to allocate large I/O buffers on the heap (malloc/std::vector) and pass a pointer, keeping the stack frame small.

> [!question]- Why does C++ RAII with std::vector give you "heap capacity with stack lifetime management," and why does this matter for exception safety?
> A std::vector object (the metadata: pointer, size, capacity) lives on the stack and is fixed-size. Its destructor is guaranteed to run when the enclosing scope exits — whether by normal return, early return, or exception. The destructor calls delete[] on the heap-allocated element array, so the heap memory is freed regardless of how the scope exits. Without RAII, a heap allocation paired with a manual free at the end of the function leaks memory whenever an exception or early return skips the free. RAII makes the lifetime of heap memory deterministic and exception-safe by tying it to a stack object's destructor.

> [!question]- What is heap fragmentation, and why does a long-running LDS storage server need to be more careful about it than a short-lived command-line tool?
> Fragmentation occurs when freed blocks are scattered throughout the heap in sizes that don't match future allocation requests. For example, alternating allocations of 100B and 1000B objects, then freeing all the 1000B ones, leaves many 1000B holes — but a request for 1001B cannot use any of them and must grow the heap. A short-lived tool exits before fragmentation accumulates. A long-running server that processes millions of requests, each with slightly different allocation patterns, can slowly increase its RSS (resident memory) over hours or days even with no logical memory leak. Mitigations include using size-class allocators (tcmalloc, jemalloc), reusing fixed-size buffers from a pool, and avoiding many small short-lived heap allocations on hot paths.
