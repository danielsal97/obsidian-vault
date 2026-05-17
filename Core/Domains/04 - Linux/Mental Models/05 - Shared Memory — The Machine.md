# Shared Memory — The Machine

## The Model
Two separate buildings (processes), each with their own rooms — but there is one room that both buildings have a private door into. It is the same physical room. Whatever one process writes appears instantly in the other process's view. There is no lock on the room by default — you must bring your own.

## How It Moves

```
Process A                    Physical RAM               Process B
─────────────                ────────────               ─────────────
virtual addr 0x7f00 ──────→  [page: 0xA000] ←────────  virtual addr 0x6f00
  p[0] = 42                  content: 42                 q[0] == 42 ← instant

mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0)
       ↑                                     ↑
   my virtual address                     shared file or shm_open region
```

**Why faster than sockets:** A socket copy goes: process A memory → kernel buffer → process B memory. Shared memory: process A writes directly to the shared page — process B reads it directly. Zero copies, no syscall for data transfer.

**But:** no synchronization is built in. If both processes write simultaneously, data races occur. You need a semaphore or `pthread_mutex` with `PTHREAD_PROCESS_SHARED` attribute.

## The Blueprint

```c
// Create shared region:
int fd = shm_open("/lds_shared", O_CREAT|O_RDWR, 0600);
ftruncate(fd, 4096);   // set size

// Map into address space:
void* ptr = mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);

// Use it:
((int*)ptr)[0] = 42;   // visible to all processes that mapped this region

// Cleanup:
munmap(ptr, 4096);
shm_unlink("/lds_shared");   // delete the name (region stays until all unmap)
```

**`MAP_SHARED` vs `MAP_PRIVATE`:**
- `MAP_SHARED`: writes are visible to other mappers AND written back to the file/shm region
- `MAP_PRIVATE`: writes create a private copy (copy-on-write) — not visible to others, not written back

## Where It Breaks

- **No synchronization**: two processes write to the same offset simultaneously → data race, corrupted data
- **Forgetting `munmap`**: the mapping persists until `munmap` or process exit — wastes virtual address space
- **Forgetting `shm_unlink`**: the name persists in `/dev/shm` even after all processes exit — leaked resource
- **Size mismatch**: one process maps 4096 bytes, another maps 8192 of the same region — both access the same physical pages, but one can access beyond the other's mapped range

## In LDS

LDS currently uses TCP sockets for inter-process communication (manager ↔ minions). Shared memory is a potential optimization for same-machine communication: instead of manager → TCP → minion, map a shared block region that both processes read/write directly. The RAID01Manager could write to a shared buffer, and the local minion could read from it without any network stack involvement.

## Validate

1. Process A writes `42` to offset 0 of a `MAP_SHARED` region. Process B reads offset 0 one millisecond later. Is the read guaranteed to see `42`? What could go wrong?
2. Two processes both call `mmap` with `MAP_PRIVATE` on the same file. Process A writes to offset 0. Does process B see the write? Why?
3. The LDS manager and a local minion share a 64MB data region via `shm_open`. Both can read simultaneously. Only the manager writes. What synchronization mechanism do you need, and why is a regular `std::mutex` not sufficient?

## Connections

**Theory:** [[05 - Shared Memory]]  
**Mental Models:** [[Semaphores — The Machine]], [[IPC Overview — The Machine]], [[mmap — The Machine]], [[Processes — The Machine]]  
**LDS Implementation:** [[LDS/Architecture/Concurrency Model]] — potential optimization path  
**Glossary:** [[pthreads]]
