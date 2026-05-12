# mmap — Memory-Mapped Files

`mmap` maps a file or anonymous memory into the process's virtual address space. Once mapped, you access it like a regular pointer — no read/write syscalls needed per access.

---

## Basic Usage — Map a File

```c
#include <sys/mman.h>
#include <fcntl.h>

int fd = open("data.bin", O_RDWR);
struct stat st;
fstat(fd, &st);

void* ptr = mmap(
    NULL,              // OS chooses the address
    st.st_size,        // map the whole file
    PROT_READ | PROT_WRITE,  // read and write
    MAP_SHARED,        // writes go to the file
    fd, 0              // fd, offset into file
);

// Now access like memory:
char* data = (char*)ptr;
data[0] = 'X';   // modifies the file (MAP_SHARED)

munmap(ptr, st.st_size);
close(fd);
```

The file doesn't need to be fully read into RAM — pages are loaded on demand (page faults).

---

## Flags

| Flag | Effect |
|---|---|
| `MAP_SHARED` | Writes go back to the file / visible to other mappings |
| `MAP_PRIVATE` | Copy-on-write — writes don't affect the file |
| `MAP_ANONYMOUS` | No file — just zero-initialized memory (no fd needed) |
| `MAP_FIXED` | Map at exact address (dangerous — can overwrite existing mappings) |
| `MAP_POPULATE` | Pre-fault all pages (no demand-paging later) |
| `MAP_HUGETLB` | Use huge pages (2 MB on x86_64) |

---

## Protection Flags

```c
PROT_READ   // readable
PROT_WRITE  // writable
PROT_EXEC   // executable (for JIT compilers)
PROT_NONE   // no access (guard pages)
```

Change protection after mapping:
```c
mprotect(ptr, size, PROT_READ);  // make read-only after writing
```

---

## Anonymous Mapping — Dynamic Memory

`MAP_ANONYMOUS` is how `malloc` internally gets large chunks from the OS (instead of `brk` for small allocations):

```c
// Equivalent to what malloc does for large allocations:
void* mem = mmap(NULL, 1024 * 1024,
    PROT_READ | PROT_WRITE,
    MAP_PRIVATE | MAP_ANONYMOUS,
    -1, 0);

free equivalent:
munmap(mem, 1024 * 1024);
```

See [[../C/Memory - malloc and free]] — `malloc` uses `mmap` for allocations > `MMAP_THRESHOLD` (~128KB).

---

## File-Backed vs Syscall I/O

| | mmap | read/write |
|---|---|---|
| Access style | Pointer dereference | Syscall per operation |
| Kernel copy | No — accesses page cache directly | Yes — kernel copies to userspace buffer |
| Seek | Just change pointer | `lseek` |
| Random access | O(1) — pointer arithmetic | `lseek` + `read` |
| Large sequential reads | May be slower (many page faults) | Better with big `read()` |

mmap excels for random access to large files (databases, memory-mapped indexes).

---

## Shared Memory Between Processes

```c
// Process A:
int fd = shm_open("/myshm", O_CREAT | O_RDWR, 0666);
ftruncate(fd, 4096);
void* p = mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);

// Process B (same shm_open call):
int fd = shm_open("/myshm", O_RDWR, 0);
void* p = mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);

// Both p pointers point to the same physical page
```

See [[Shared Memory]] for the full shared memory pattern.

---

## msync — Flushing to Disk

For `MAP_SHARED` file mappings, writes may stay in the page cache:

```c
msync(ptr, size, MS_SYNC);    // flush synchronously — guaranteed on disk when returns
msync(ptr, size, MS_ASYNC);   // schedule flush — returns immediately
```

The OS will eventually write dirty pages back automatically, but `msync` gives explicit control.

---

## madvise — Hint to the Kernel

```c
madvise(ptr, size, MADV_SEQUENTIAL);  // prefetch aggressively
madvise(ptr, size, MADV_RANDOM);      // don't prefetch
madvise(ptr, size, MADV_WILLNEED);    // hint: I'll use this soon, preload
madvise(ptr, size, MADV_DONTNEED);    // hint: done with this, free pages
```

---

## Common Uses

| Use case | How |
|---|---|
| Load a file without read() | `mmap` + pointer access |
| Shared memory IPC | `MAP_SHARED` + `shm_open` |
| Executable loading | OS uses mmap to load `.text`, `.data` sections |
| Zero-copy networking (`sendfile`) | OS maps file pages directly to socket buffer |
| Memory-mapped database (SQLite, LMDB) | `MAP_SHARED` over database file |

---

## Error Handling

```c
void* ptr = mmap(...);
if (ptr == MAP_FAILED) {   // NOT (ptr == NULL) — MAP_FAILED is (void*)-1
    perror("mmap");
}
```

---

## Related Notes

- [[Shared Memory]] — mmap for inter-process shared memory
- [[../C/File IO]] — standard file I/O via open/read/write
- [[../Memory/Process Memory Layout]] — how mmap regions appear in virtual address space
- [[../C/Memory - malloc and free]] — malloc uses mmap internally for large allocations

---

## Understanding Check

> [!question]- What goes wrong if you check (ptr == NULL) instead of (ptr == MAP_FAILED) after a failed mmap call?
> MAP_FAILED is defined as (void*)-1, which is the all-bits-set address 0xFFFFFFFFFFFFFFFF on 64-bit systems — not NULL (0x0). If mmap fails, it returns MAP_FAILED, not NULL. Checking for NULL would miss the error and your code would proceed with an invalid pointer, causing undefined behavior when you dereference it (typically a segfault or silent data corruption if the address happens to be mapped by coincidence). Always compare the return value against MAP_FAILED explicitly.

> [!question]- Why does mmap with MAP_PRIVATE not affect the underlying file when you write to the mapping, and what is the mechanism?
> MAP_PRIVATE uses copy-on-write semantics at the page level. Initially, all pages in the private mapping point to the same physical pages as the file in the page cache — no copy is made. When you write to a page for the first time, the kernel intercepts the write (via a page fault), copies just that page to a new private physical page for this process, and redirects the mapping to the private copy. The file's page cache page is left unmodified. The result: your process sees the write, but the file on disk and other mappings of the same file are unaffected.

> [!question]- When would you prefer read()/write() syscalls over mmap for file I/O, despite mmap's zero-copy advantage?
> For large sequential reads, read() with a large buffer can be faster than mmap because a single read() call brings in a large chunk with one syscall, while mmap generates individual page faults for each 4KB page accessed sequentially — many more kernel entries. read() also works well over network filesystems and some special files that don't support mmap at all. mmap shines for random access to large files (databases, indexes) where you don't know which pages you'll need, and the on-demand page fault mechanism is more efficient than seeking and reading individual regions.

> [!question]- Why must you call msync before munmap if you need guaranteed durability for a MAP_SHARED file mapping?
> munmap does not guarantee that dirty pages are flushed to disk — it only removes the mapping from the process's address space. The pages may remain in the kernel's page cache as dirty and be written back lazily by the kernel's background writeback mechanism at some later time. If the system crashes after munmap but before writeback, changes are lost. msync(MS_SYNC) explicitly flushes dirty pages to disk synchronously before returning, giving you the same durability guarantee as fsync. Databases like SQLite and LMDB rely on this sequence.

> [!question]- How does the OS use mmap internally to load an executable, and why does this mean the text segment is not actually read into RAM all at once?
> When exec() loads a program, the kernel does not read the entire binary into RAM. Instead, it creates mmap mappings for each segment: MAP_PRIVATE | PROT_READ|PROT_EXEC for .text, MAP_PRIVATE | PROT_READ|PROT_WRITE for .data, etc., all backed by the executable file on disk. Pages are loaded on demand as the program executes and triggers page faults. For a large binary where only certain functions are ever called, most code pages may never be loaded. This is also why shared libraries can be mapped into many processes simultaneously — they all share the same physical pages of the .so file in the page cache, with each process getting its own private copy-on-write pages for any library globals they modify.
