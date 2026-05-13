# mmap — The Machine

## The Model
A projector that maps a file directly onto your virtual address space as if it were an array in RAM. Reading `ptr[1000]` reads byte 1000 of the file. Writing `ptr[1000] = 42` writes byte 42 to the file. The kernel handles the actual disk I/O lazily — the file doesn't load until you touch a page, and dirty pages flush asynchronously.

## How It Moves

```
File on disk: /data/storage.bin (1GB)

mmap(NULL, 1GB, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0)
         ↓
Virtual address space:
  0x7f000000 ... 0x7f000000 + 1GB  ← mapped region

ptr[0]       = 'H'   → page fault → kernel loads page 0 from disk
ptr[4096]    = 'e'   → page fault → kernel loads page 1 from disk
ptr[0]       = 'X'   → no fault   → page already in cache, write goes to cache
                                     kernel will write dirty page back to disk later

munmap(ptr, 1GB)     → removes the mapping, flushes dirty pages
msync(ptr, 4096, MS_SYNC)  → force immediate write of first page to disk
```

**WHY faster than read()/write() for large files:**
- `read()` copies: disk → kernel page cache → your buffer (2 copies)
- `mmap()`: disk → kernel page cache = your buffer (1 copy, same physical pages)
- For sequential access of large files, `mmap` avoids one copy per page

**WHY lazy:** If you map 1GB but only access 10MB, only 10MB worth of page faults occur. The rest never loads.

## The Blueprint

```c
int fd = open("storage.bin", O_RDWR);
struct stat st;
fstat(fd, &st);

void* ptr = mmap(NULL, st.st_size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
close(fd);   // safe — mmap holds its own reference to the file

char* data = (char*)ptr;
data[offset] = value;   // write directly to file via memory

msync(ptr, st.st_size, MS_SYNC);   // force flush
munmap(ptr, st.st_size);
```

**`MAP_ANONYMOUS`**: mmap without a file — allocates zeroed memory pages directly. What `malloc` uses internally for large allocations.

## Where It Breaks

- **`mmap` beyond file size**: accessing beyond `st_size` → SIGBUS (not SIGSEGV) — the mapped region exists but the backing store doesn't cover it
- **Forgetting `msync`**: writes to `MAP_SHARED` file may not reach disk before `munmap` in crash scenarios
- **File modified by another process while mapped**: your view becomes stale unless you use `MAP_SHARED` (in which case you see the changes)

## In LDS

`services/communication_protocols/nbd/src/NBDDriverComm.cpp`

The NBD block device `/dev/nbd0` is accessed via a file descriptor. LDS's `NBDDriverComm` uses `read()`/`write()` on this fd rather than `mmap`, because NBD requests arrive as discrete events (the Reactor pattern requires fd-based I/O). However, if LDS's `LocalStorage` backed by a real file, `mmap`-ing the storage file would eliminate the copy from `m_data` vector into the send buffer — a potential optimization for large block reads.

## Validate

1. You `mmap` a 100MB file with `MAP_SHARED`. You write to byte 50MB. Has anything been written to disk yet? What triggers the actual disk write?
2. `malloc(10MB)` vs `mmap(MAP_ANONYMOUS, 10MB)` — both give you 10MB of memory. What is the difference in how the kernel allocates physical RAM for each?
3. The LDS storage file is `mmap`ed by the manager process. A minion also `mmap`s the same file with `MAP_SHARED`. Manager writes block 5. Minion reads block 5. Is synchronization needed? Why?

## Connections

**Theory:** [[Core/Domains/04 - Linux/Theory/07 - mmap]]  
**Mental Models:** [[File Descriptors — The Machine]], [[Shared Memory — The Machine]], [[Stack vs Heap — The Machine]], [[malloc and free — The Machine]]  
**LDS Implementation:** [[LDS/Application/LocalStorage]] — potential mmap optimization for storage file  
**Runtime Machines:** [[LDS/Runtime Machines/LocalStorage — The Machine]]  
**Glossary:** [[VFS]]
