# Shared Memory

The fastest IPC mechanism — multiple processes map the same physical memory into their address space. No kernel copy on every read/write.

---

## POSIX Shared Memory

```c
#include <sys/mman.h>
#include <fcntl.h>

// Process A — create and write:
int fd = shm_open("/my_shm", O_CREAT | O_RDWR, 0666);
ftruncate(fd, 4096);                             // set size
void* ptr = mmap(NULL, 4096,
    PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

strcpy((char*)ptr, "hello from A");

// Process B — open and read:
int fd = shm_open("/my_shm", O_RDWR, 0);
void* ptr = mmap(NULL, 4096,
    PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

printf("%s\n", (char*)ptr);   // "hello from A"

// Cleanup:
munmap(ptr, 4096);
close(fd);
shm_unlink("/my_shm");   // removes the name; memory freed when last mmap gone
```

Named with a `/name` — visible in `/dev/shm/` on Linux.

---

## mmap for Shared Memory

`mmap` is the underlying mechanism for both shared memory and file mapping. See [[mmap]] for full detail.

```c
// Anonymous shared memory — only between parent and children:
void* ptr = mmap(NULL, size,
    PROT_READ | PROT_WRITE,
    MAP_SHARED | MAP_ANONYMOUS,   // no fd needed
    -1, 0);

fork();   // child inherits the mapping — same physical pages
```

---

## Synchronization Required

Shared memory gives you raw shared bytes — no built-in synchronization. You need a separate mechanism:

| Mechanism | Header | Use |
|---|---|---|
| `pthread_mutex` with `PTHREAD_PROCESS_SHARED` | `<pthread.h>` | Fast mutual exclusion |
| POSIX semaphore | `<semaphore.h>` | Signaling + counting |
| Futex (Linux) | `<linux/futex.h>` | Low-level, what pthreads use internally |

```c
// Mutex in shared memory:
pthread_mutex_t* m = (pthread_mutex_t*)ptr;
pthread_mutexattr_t attr;
pthread_mutexattr_init(&attr);
pthread_mutexattr_setpshared(&attr, PTHREAD_PROCESS_SHARED);
pthread_mutex_init(m, &attr);
```

See [[Semaphores]] for semaphore-based coordination.

---

## System V Shared Memory (Legacy)

Older API — `shmget`/`shmat`/`shmdt`/`shmctl`. Prefer POSIX (`shm_open`/`mmap`).

```c
int shmid = shmget(IPC_PRIVATE, 4096, IPC_CREAT | 0666);
void* ptr = shmat(shmid, NULL, 0);   // attach
shmdt(ptr);                           // detach
shmctl(shmid, IPC_RMID, NULL);       // remove
```

---

## Performance

| IPC | Latency | Throughput |
|---|---|---|
| Shared memory | ~50 ns (cache) | Very high |
| Pipe / socketpair | ~1–5 µs | High |
| TCP loopback | ~5–20 µs | High |
| UDP | ~5–20 µs | High |

Shared memory is fast because data is never copied — both processes access the same physical pages. The bottleneck becomes cache coherency between CPU cores.

---

## When to Use

- **Shared memory:** large data, same host, highest throughput needed
- **Pipes/sockets:** simpler, buffered, good for command-type messages
- **TCP:** cross-machine, or when you want standard socket APIs

LDS uses UDP for master↔minion (different machines) and NBD kernel socket for kernel↔userspace. Shared memory would only apply if both processes ran on the same machine.

---

## Related Notes

- [[mmap]] — full mmap API and file-backed mappings
- [[Semaphores]] — synchronization for shared memory
- [[IPC Overview]] — all IPC mechanisms compared

---

## Understanding Check

> [!question]- What goes wrong if two processes write to shared memory simultaneously without synchronization?
> Without synchronization, both processes can interleave writes at the byte or word level, producing corrupted data that neither process wrote intentionally. For example, if a writer is updating a struct field-by-field, a reader can observe a partially-updated struct with some old fields and some new ones — a torn read. On x86-64, even a single 8-byte write is only atomic if naturally aligned; anything larger is not. The shared memory mechanism itself provides no protection — you must place a process-shared mutex or semaphore inside or alongside the shared region.

> [!question]- Why does shm_unlink not immediately free the shared memory if another process still has it mapped?
> shm_unlink removes the name from /dev/shm so no new process can open it by name — analogous to unlinking a file. But the underlying memory object uses reference counting: it stays alive as long as at least one process has an active mmap mapping to it. The physical pages are freed only when the last munmap call drops the last reference. This matches Unix file semantics (unlink removes the directory entry, inode persists until last file descriptor is closed).

> [!question]- Anonymous MAP_SHARED memory works between a parent and its children after fork — why can't two unrelated processes share it this way?
> MAP_ANONYMOUS | MAP_SHARED creates a mapping backed by physical pages that are shared between processes sharing the same memory object. After fork, the child inherits the parent's page table mappings, so both point to the same physical pages. Two unrelated processes have entirely separate address spaces and separate page tables — there is no inherited mapping to share. They must use a named mechanism (shm_open with a path, or a file-backed mmap) so the kernel can identify that both processes intend to share the same underlying object.

> [!question]- Why is shared memory described as having ~50ns latency compared to ~5–20µs for TCP loopback, even though both paths stay on one machine?
> TCP loopback still goes through the full kernel network stack: the sender copies data into a kernel socket buffer, the kernel processes protocol headers, schedules delivery, and the receiver copies data back out to userspace — multiple context switches and memory copies. Shared memory involves no copying at all: both processes directly access the same physical cache lines. The 50ns figure represents the cost of a cache-to-cache transfer between CPU cores plus any synchronization overhead. The bottleneck becomes CPU cache coherency, not kernel overhead.

> [!question]- In LDS, shared memory is not used — what is the architectural reason, and when would it become relevant?
> LDS is designed for distributed storage across multiple machines (master + minions over UDP). Shared memory only works within a single machine — processes on different hosts cannot share physical memory pages. It would become relevant only if LDS added an optimization where two processes on the same host (e.g., two minion instances, or a minion and a local cache daemon) needed high-throughput data exchange without network overhead. The current design uses UDP and the NBD kernel socket interface, which are appropriate for the cross-machine and kernel-to-userspace communication paths LDS actually needs.
