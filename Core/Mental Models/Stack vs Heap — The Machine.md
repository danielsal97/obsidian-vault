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

**Theory:** [[Core/Theory/Memory/Stack vs Heap]]  
**Mental Models:** [[Process Memory Layout — The Machine]], [[malloc and free — The Machine]], [[RAII — The Machine]], [[Pointers — The Machine]]  
**LDS Implementation:** [[LDS/Application/LocalStorage]] — vector heap allocation  
**Runtime Machines:** [[LDS/Runtime Machines/LocalStorage — The Machine]]
