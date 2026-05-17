# Stack vs Heap — The Machine

## The Model
Two completely different allocation machines in the same building. The stack is a spring-loaded plate dispenser in a cafeteria — plates push on and pop off automatically in strict order, O(1), zero overhead. The heap is a warehouse with a human manager and a ledger — you request a shelf, the manager finds one, marks it yours, you must return it manually.

## How It Moves

```
STACK                              HEAP
─────────────────────────────      ──────────────────────────────
void Read() {                      void* p = malloc(1024);
  char buf[512];     ← pushed        // manager finds 1024-byte gap
  int  offset = 0;  ← pushed        // marks ledger: [addr: 0x7f40, size: 1024, used]
  // ... work ...                    // returns pointer
}  ← both popped automatically     free(p);
                                    // manager marks: [addr: 0x7f40, free]
```

**Stack push = one CPU instruction** (`sub rsp, N`). Stack pop = one CPU instruction (`add rsp, N`). The CPU register `rsp` IS the stack pointer — it's hardware.

**Heap allocation = a function call** that searches a free-list, possibly calls `brk()` or `mmap()` (syscall), updates the ledger. Variable latency.

## The Blueprint

**Stack:**
- Size is fixed at thread creation (default ~8MB on Linux, set with `ulimit -s`)
- Lifetime = scope. The compiler inserts push/pop at function entry/exit.
- Thread-local: each thread has its own stack.
- Cannot store data that outlives the function.

**Heap:**
- Size grows dynamically (up to virtual address space limit)
- Lifetime = until `free()`/`delete` is called
- Shared between threads (requires synchronization)
- Fragmentation: repeated alloc/free of different sizes leaves unusable gaps in the ledger

**When to use which:**
- Stack: small, fixed-size locals that die with the function
- Heap: large data, data with dynamic size, data that must outlive the function, shared between threads

## Program Lifecycle & Memory Flow

Stack and heap don't just exist — they are *created* during a precise sequence. You cannot reason about memory without knowing when each region appears.

### The Complete Lifecycle

```
1. SOURCE CODE        → .c / .cpp files
2. COMPILATION        → object files (.o) — machine code + unresolved symbols
3. LINKING            → resolves symbols, merges sections → ELF executable
4. PROGRAM LOADING    → OS reads ELF, creates process, maps segments
5. VIRTUAL ADDRESS SPACE CREATION
                      → kernel sets up page tables
6. STACK SETUP        → kernel allocates initial stack page, sets rsp
7. HEAP INITIALIZATION → runtime sets up brk pointer (heap starts empty)
8. RUNTIME            → function calls build stack frames, malloc grows heap
9. DYNAMIC ALLOCATION LIFECYCLE → alloc → use → free → coalesce
10. PROGRAM TERMINATION → OS reclaims all pages; stack/heap cease to exist
```

### ELF Segments → Virtual Address Space

When the loader maps an ELF executable, each segment maps to a distinct region:

```
High Address  ┌──────────────────┐
              │  Command-line    │  argv, envp strings
              │  args / env      │
              ├──────────────────┤
              │   STACK          │  grows ↓  (per-thread)
              │        ↓         │  exists from load time
              ├──────────────────┤
              │                  │
              │   (free space)   │  unmapped — SIGSEGV if touched
              │                  │
              ├──────────────────┤
              │   HEAP           │  grows ↑  (starts empty)
              │        ↑         │  created at load time, grows via brk/mmap
              ├──────────────────┤
              │   .bss           │  zero-initialized globals (load time)
              ├──────────────────┤
              │   .data          │  initialized globals (from ELF segment)
              ├──────────────────┤
              │   .text          │  machine code (read-only, shared pages)
Low Address   └──────────────────┘
```

**Which regions are created at load time:** `.text`, `.data`, `.bss`, initial stack page, brk pointer (heap base).  
**Which regions grow at runtime:** stack (grows down on each function call), heap (grows up on `brk()`/`mmap()` calls inside `malloc`).  
**Which memory is static:** `.text` and `.data` — size fixed at link time.  
**Which memory is thread-local:** each thread has its own stack; heap is shared.

### Compile Time vs Runtime: What Each Decides

| | Compile Time | Runtime |
|---|---|---|
| Stack frame size | ✅ fixed by compiler | only the *allocation* (rsp -= N) happens at runtime |
| Which heap blocks exist | ❌ unknown | determined by malloc/free calls |
| Virtual address of .text | mostly fixed (ASLR shifts it) | loaded by kernel |
| Stack depth | ❌ unknown | depends on call chain |
| Object lifetimes on heap | ❌ unknown | determined by when free() is called |

### Function Call → Stack Frame Anatomy

Every call is a structured push:

```
call f:
  1. push return address        ← where to resume after f returns
  2. push caller-saved registers (calling convention)
  3. push frame pointer (rbp)   ← optional, -fomit-frame-pointer removes it
  4. sub rsp, N                 ← reserve space for f's locals
  5. [f executes]
  6. add rsp, N                 ← release locals
  7. pop rbp
  8. ret                        ← pop return address → jmp
```

Calling convention (System V AMD64 ABI on Linux): first 6 integer args in `rdi, rsi, rdx, rcx, r8, r9`; rest on stack. Return value in `rax`. Callee saves `rbx, rbp, r12–r15`; caller saves the rest.

### Virtual Memory & the MMU

Every address your program uses is **virtual**. The MMU translates it to physical RAM via page tables on every memory access:

```
Virtual address → [ Page Table Walk ] → Physical frame + offset
                      (4KB pages)
```

If the page isn't in RAM → **page fault** → OS loads it from disk (or zero-fills it for new heap pages). This is why `malloc` can return a pointer before the physical memory exists — the OS maps it lazily.

**Cache locality matters** because the CPU caches physical cache lines (64 bytes). Stack variables are adjacent in memory and accessed in order → high cache hit rate. Heap allocations may be scattered → cache misses, especially after fragmentation.

### Dynamic Allocation Lifecycle

```
malloc(n)
  → check thread-local size-class cache (tcmalloc / jemalloc fast path)
  → if miss: search free list for block ≥ n
  → if heap exhausted: brk() syscall grows the heap segment
  → return pointer

free(p)
  → read hidden metadata block before p (contains size)
  → add block to free list
  → coalesce with adjacent free blocks
  → if large enough: may return pages to OS via sbrk(-n) or madvise
```

**Fragmentation** accumulates when freed blocks are too small to satisfy future requests — the heap grows even though aggregate live bytes shrink. Long-running processes need size-class allocators (tcmalloc, jemalloc) or object pools to avoid this.

## Where It Breaks

- **Stack overflow**: too many nested calls or too-large local array → `rsp` walks into the heap → segfault
- **Dangling stack pointer**: return a pointer to a local variable — the stack frame is popped, the memory is overwritten by the next function call
- **Heap double-free**: ledger corruption — the allocator may crash or silently corrupt the next allocation
- **Heap leak**: forget to `free()` — ledger keeps marking blocks "used" until the process runs out of virtual address space

## In LDS

`utilities/thread_pool/include/thread_pool.hpp`

Each worker thread in the LDS ThreadPool gets its own stack (OS-allocated at thread creation). Local variables inside the worker's lambda live on that thread's stack and vanish when the lambda returns.

`services/local_storage/src/LocalStorage.cpp` — `m_data` is a `std::vector<char>` whose internal buffer lives on the **heap** (vector calls `new[]` internally). This allows `LocalStorage` to persist across function calls and be shared between Read/Write operations on different threads.

## Validate

1. `LocalStorage::Read` has a local `std::string result`. Where does the `std::string` object itself live? Where does the character data inside it live?
2. A worker thread in the ThreadPool calls a chain: `ThreadPool → WorkFunc → LocalStorage::Read → RecvAll`. How deep is the stack at `RecvAll`? What determines the maximum depth before overflow?
3. You `new` a `LocalStorage` object and return a raw pointer from a factory function. The caller forgets to `delete` it. What specifically accumulates in which region of memory until the process dies?

## Connections

**Theory:** [[02 - Stack vs Heap]], [[01 - Process Memory Layout]]  
**Mental Models:** [[Process Memory Layout — The Machine]], [[malloc and free — The Machine]], [[RAII — The Machine]], [[Pointers — The Machine]], [[Build Process — The Machine]], [[Linker — The Machine]]  
**LDS Implementation:** [[LDS/Application/LocalStorage]] — vector heap allocation  
**Runtime Machines:** [[LDS/Runtime Machines/LocalStorage — The Machine]]
