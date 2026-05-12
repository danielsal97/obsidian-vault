# malloc and free — The Machine

## The Model
A warehouse manager with a ledger book. Every row in the ledger is a memory block: address, size, status (free/used). `malloc` asks the manager for N bytes — the manager scans the ledger, finds a free block that fits, marks it "used", hands you the address. `free` hands the address back — the manager marks it "free" and may merge it with adjacent free blocks.

## How It Moves

```
malloc(256):
  Manager scans free-list → finds [addr: 0x1000, size: 512, FREE]
  Split: [addr: 0x1000, size: 256, USED] + [addr: 0x1100, size: 256, FREE]
  Return pointer: 0x1000

free(0x1000):
  Manager looks up 0x1000 → marks [addr: 0x1000, size: 256, FREE]
  Check neighbor 0x1100 → also FREE → merge → [addr: 0x1000, size: 512, FREE]
```

**The metadata trick:** `malloc` stores the block size in the bytes JUST BEFORE the pointer it returns. When you call `free(p)`, it reads `p[-1]` (roughly) to know the block size. This is why writing before the start of an allocated buffer corrupts the allocator.

**When the free-list is empty:** `malloc` calls `sbrk()` or `mmap()` — a syscall to the kernel to expand the heap. This is why malloc latency is variable.

## The Blueprint

- **`malloc(0)`**: implementation-defined — returns either NULL or a unique pointer. Never dereference it.
- **`realloc(p, n)`**: try to grow the block in place; if not possible, allocate a new block, copy, free the old.
- **`calloc(n, size)`**: allocates n×size bytes AND zero-fills them. The zero-fill is often done by the OS for fresh pages (free), so calloc can be faster than malloc+memset.
- **Fragmentation**: after many alloc/free cycles of varying sizes, the ledger has many small free gaps that can't satisfy large requests even though total free memory is sufficient.
- **Thread safety**: modern allocators (glibc ptmalloc, jemalloc) use per-thread arenas to reduce lock contention.

## Where It Breaks

- **Double-free**: manager marks a used block free twice — the block appears in the free-list twice. Next `malloc` may return the same address to two callers simultaneously.
- **Buffer overflow**: writing past the end of an allocated block overwrites the metadata of the next block. The next `free` reads corrupted metadata → crash or silent corruption.
- **Use-after-free**: accessing memory after `free` — the manager may have already handed it to another caller. You're reading/writing someone else's data.
- **Memory leak**: never calling `free` — the ledger grows monotonically until the process exhausts virtual address space.

## In LDS

`services/local_storage/include/LocalStorage.hpp`

`LocalStorage` stores data in a `std::vector<char> m_data`. The `std::vector` internally uses `new[]`/`delete[]` (which call `malloc`/`free`). When the vector resizes (e.g., on first construction), it calls `malloc` for the new buffer, copies data, and calls `free` on the old buffer. The `LocalStorage` destructor lets the vector go out of scope, which calls `delete[]`, which calls `free` — automatic RAII cleanup with no manual `free` needed.

## Validate

1. You call `malloc(100)`, write 105 bytes into the result, then `free` it. No immediate crash. Why might the crash appear 10 calls later in a completely unrelated `malloc`?
2. `std::vector<char>` in `LocalStorage` doubles its capacity when it runs out of space. Trace exactly what `malloc`/`free` calls happen during that resize.
3. `new LocalStorage()` vs `malloc(sizeof(LocalStorage))` — both allocate on the heap. What does `new` do that `malloc` does not?

## Connections

**Theory:** [[Core/Theory/C/Memory - malloc and free]]  
**Mental Models:** [[Stack vs Heap — The Machine]], [[Process Memory Layout — The Machine]], [[RAII — The Machine]], [[mmap — The Machine]]  
**LDS Implementation:** [[LDS/Application/LocalStorage]] — vector m_data buffer  
**Runtime Machines:** [[LDS/Runtime Machines/LocalStorage — The Machine]]
