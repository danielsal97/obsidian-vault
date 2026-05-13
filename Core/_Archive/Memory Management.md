# Memory Management

*Quick reference — condensed summaries only. For full coverage with LDS tie-ins and Understanding Check Q&A, see [[Memory/01 - Process Memory Layout]], [[Memory/02 - Stack vs Heap]], [[Memory/09 - Memory Errors and Tools]].*

---

## Process Memory Layout

Every process gets a virtual address space divided into segments:

```
High address
┌─────────────────┐
│   Stack         │  ← grows downward. Local variables, function frames.
│   ↓             │    Automatic lifetime. Limited size (~8MB default).
├─────────────────┤
│   (gap)         │
├─────────────────┤
│   ↑             │
│   Heap          │  ← grows upward. malloc/new. Manual lifetime.
├─────────────────┤
│   BSS           │  ← uninitialized global/static variables (zeroed at start)
├─────────────────┤
│   Data          │  ← initialized global/static variables
├─────────────────┤
│   Text          │  ← compiled machine code (read-only)
└─────────────────┘
Low address
```

---

## Stack

**What lives here:** local variables, function parameters, return addresses, saved registers.

**How it works:** the CPU maintains a stack pointer (`rsp` on x86-64). On function call: push return address + arguments → decrement stack pointer. On return: increment stack pointer → locals destroyed instantly.

**Properties:**
- O(1) allocation and deallocation (just move a pointer)
- No fragmentation
- Limited size — deep recursion or large local arrays → stack overflow (`SIGSEGV`)
- Lifetime tied to scope — no pointer to a local should outlive the function

```c
void f() {
    int arr[1000000];  // 4MB on stack — likely stack overflow
}

int* bad() {
    int x = 5;
    return &x;   // dangling pointer — x is gone when f returns
}
```

---

## Heap

**What lives here:** anything allocated with `malloc`/`new`. Survives function return.

**How malloc works internally:**
- Uses `sbrk()` or `mmap()` to request pages from the OS
- Maintains a free list of available blocks
- On `malloc(n)`: find a free block ≥ n, split it, return pointer
- On `free(p)`: add block back to free list, coalesce adjacent free blocks

**Fragmentation:**
- **External:** many small free blocks, but no single block large enough for a request
- **Internal:** allocated block is larger than requested (alignment/rounding)

**Why custom allocators exist:**
- `malloc` has per-call overhead (find block, update free list)
- For fixed-size objects: FSA (Fixed-Size Allocator) — O(1) alloc/free, zero fragmentation
- For variable-size objects: VSA, arena allocator, pool allocator

---

## Memory Errors

| Error | Description | Tool to catch |
|---|---|---|
| Memory leak | `malloc` without matching `free` | Valgrind, ASan (leak sanitizer) |
| Use-after-free | Access memory after `free` | ASan |
| Double free | `free(p)` twice | ASan |
| Buffer overflow | Write past end of allocation | ASan |
| Stack overflow | Too deep recursion or large locals | OS (SIGSEGV) |
| Uninitialized read | Read variable before writing it | Valgrind, MSan |

---

## Tools

**Valgrind:**
```bash
valgrind --leak-check=full ./program
```
Instruments every memory operation. Catches leaks, use-after-free, uninitialized reads. Slow (10-50x).

**AddressSanitizer (ASan):**
```bash
g++ -fsanitize=address -g program.cpp -o program
./program
```
Compiler instrumentation. Faster than Valgrind (2x overhead). Catches use-after-free, buffer overflow, leaks.

**UBSan:**
```bash
g++ -fsanitize=undefined -g program.cpp -o program
```
Catches undefined behavior: signed overflow, null dereference, misaligned access.

**Combine all three:**
```bash
g++ -fsanitize=address,undefined -g program.cpp -o program
```

---

## Smart Pointers (C++ RAII for heap)

The right way to manage heap memory in C++:

```cpp
auto p = std::make_unique<int>(5);   // freed when p goes out of scope
auto q = std::make_shared<int>(5);   // freed when last shared_ptr is destroyed
```

Rule: **never call `delete` manually**. Use smart pointers or containers (`std::vector`, `std::string`) which manage their own heap memory.

---

## Virtual Memory

Each process sees its own private address space (virtual addresses). The OS + MMU (Memory Management Unit) translate virtual → physical addresses via page tables.

**Pages:** memory is divided into fixed-size chunks (typically 4KB). Each page can be:
- Present (mapped to physical RAM)
- Swapped (moved to disk)
- Not mapped (access → segfault)

**Why this matters:**
- Two processes can have the same virtual address pointing to different physical pages — isolation
- `mmap` maps a file or anonymous memory into the virtual address space
- `fork()` uses copy-on-write — child shares parent's pages until either writes, then copies
