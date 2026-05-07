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
