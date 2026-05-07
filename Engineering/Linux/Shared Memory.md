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
