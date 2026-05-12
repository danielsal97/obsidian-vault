# File I/O

---

## POSIX File I/O (Low-Level)

Works with file descriptors. The same API used for sockets, pipes, and all other fds.

```c
#include <fcntl.h>
#include <unistd.h>

// Open:
int fd = open("file.txt", O_RDONLY);
int fd = open("file.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
int fd = open("file.txt", O_RDWR | O_APPEND);

// Read:
ssize_t n = read(fd, buf, sizeof(buf));
// n > 0: bytes read
// n == 0: EOF
// n < 0: error, check errno

// Write:
ssize_t n = write(fd, buf, len);
// n may be less than len — loop required (same as send)

// Seek:
off_t pos = lseek(fd, offset, SEEK_SET);   // absolute position
lseek(fd, 0, SEEK_SET);   // rewind to start
lseek(fd, 0, SEEK_END);   // seek to end (returns file size)
lseek(fd, -10, SEEK_CUR); // 10 bytes before current position

// Close:
close(fd);
```

---

## Open Flags

| Flag | Meaning |
|---|---|
| `O_RDONLY` | Read only |
| `O_WRONLY` | Write only |
| `O_RDWR` | Read and write |
| `O_CREAT` | Create if doesn't exist |
| `O_TRUNC` | Truncate to zero on open |
| `O_APPEND` | Writes always go to end |
| `O_NONBLOCK` | Non-blocking mode |
| `O_CLOEXEC` | Close on exec |

Mode (permissions) only used with `O_CREAT`:
```c
open("file", O_CREAT | O_WRONLY, 0644);   // rw-r--r--
open("file", O_CREAT | O_WRONLY, 0755);   // rwxr-xr-x
```

---

## C Standard Library File I/O (Buffered)

Higher level — uses `FILE*`. Includes buffering for performance.

```c
#include <stdio.h>

FILE* f = fopen("file.txt", "r");    // "r", "w", "a", "rb", "wb", "r+"
fclose(f);

// Read:
char buf[256];
fgets(buf, sizeof(buf), f);          // read one line
int n = fread(buf, 1, sizeof(buf), f); // read up to n bytes

// Write:
fputs("hello\n", f);
fprintf(f, "x=%d\n", x);
fwrite(data, 1, len, f);

// Check for EOF/error:
if (feof(f))   { /* end of file */ }
if (ferror(f)) { /* error occurred */ }

// Position:
fseek(f, 0, SEEK_SET);
long pos = ftell(f);
rewind(f);

// Flush buffer to OS:
fflush(f);
```

---

## Buffered vs Unbuffered

| | POSIX (`read`/`write`) | C stdio (`fread`/`fwrite`) |
|---|---|---|
| Buffering | No — every call is a syscall | Yes — batches small writes |
| Performance | Slow for many small ops | Fast for many small ops |
| Use for | Sockets, pipes, random access | Files with sequential I/O |
| Mixing with fd | Don't mix with `fileno()` output | Don't mix with raw fd ops |

`fileno(f)` — get the underlying fd from a FILE*.

---

## Error Handling

```c
int fd = open("file.txt", O_RDONLY);
if (fd < 0) {
    perror("open");         // prints: "open: No such file or directory"
    fprintf(stderr, "open failed: %s\n", strerror(errno));
    return -1;
}
```

`errno` is a thread-local variable set by syscalls on failure. Check it immediately — the next syscall may change it.

Common errno values:
- `ENOENT` — no such file or directory
- `EACCES` — permission denied
- `EEXIST` — file already exists
- `EBADF` — bad file descriptor
- `EINTR` — interrupted by signal (retry)
- `EAGAIN` — would block (non-blocking fd, no data)

---

## Reading a Whole File

```c
char* read_file(const char* path, size_t* out_size) {
    int fd = open(path, O_RDONLY);
    if (fd < 0) return NULL;
    
    // Get size:
    off_t size = lseek(fd, 0, SEEK_END);
    lseek(fd, 0, SEEK_SET);
    
    char* buf = malloc(size + 1);
    if (!buf) { close(fd); return NULL; }
    
    ssize_t n = read(fd, buf, size);
    close(fd);
    
    buf[n] = '\0';
    if (out_size) *out_size = n;
    return buf;   // caller must free
}
```

---

## File Metadata — stat

```c
#include <sys/stat.h>

struct stat st;
stat("file.txt", &st);       // by path
fstat(fd, &st);              // by fd

st.st_size;    // file size in bytes
st.st_mtime;   // last modification time
st.st_mode;    // file type + permissions
st.st_ino;     // inode number

// Check file type:
S_ISREG(st.st_mode)   // regular file
S_ISDIR(st.st_mode)   // directory
S_ISLNK(st.st_mode)   // symlink
```

---

## Directory Operations

```c
#include <dirent.h>

DIR* dir = opendir("/path");
struct dirent* entry;

while ((entry = readdir(dir)) != NULL) {
    printf("%s\n", entry->d_name);
    // entry->d_type: DT_REG (file), DT_DIR (dir), DT_LNK (symlink)
}

closedir(dir);
```

---

## Atomic File Write Pattern

Write to a temp file then rename — prevents partial writes being visible:

```c
void atomic_write(const char* path, const void* data, size_t len) {
    char tmp[256];
    snprintf(tmp, sizeof(tmp), "%s.tmp", path);
    
    int fd = open(tmp, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    write_all(fd, data, len);
    fsync(fd);    // flush to disk — important for crash safety
    close(fd);
    
    rename(tmp, path);   // atomic on same filesystem
}
```

`rename()` is atomic — the reader either sees the old file or the new file, never a partial write.

---

## Understanding Check

> [!question]- `read()` can return fewer bytes than requested even with no error and no EOF. Why does this happen, and what does correct handling look like?
> The kernel delivers whatever data is currently available — a single `read()` is not guaranteed to fill your buffer. On a socket, it returns what arrived in the current TCP segment. On a file, a signal (EINTR) can interrupt the call mid-read. The correct pattern is a loop: keep calling `read()` into `buf + total_read`, accumulating the count, until you've read the full expected length or hit EOF/error. This is what `recv_all`/`read_all` wrappers do in the LDS codebase. A single `read()` that happens to work in testing can silently truncate messages in production.

> [!question]- What goes wrong if you mix `FILE*` buffered I/O (`fwrite`) and raw POSIX `write()` on the same underlying file descriptor?
> The `FILE*` buffer holds bytes that have been logically written but not yet flushed to the OS. If you also call `write(fileno(f), ...)` directly, those bytes go to the kernel immediately, ahead of the data still sitting in the stdio buffer. The result is data written in the wrong order. Similarly, `fread` may have buffered bytes ahead of the OS read position, so a raw `read()` call skips bytes that are already in the stdio buffer. Always choose one interface per fd: either use `FILE*` exclusively (with `fflush` before any fd-level operations) or use raw POSIX fd operations.

> [!question]- What goes wrong if you skip `fsync` in the atomic write pattern before calling `rename`?
> Without `fsync`, the file data may still be in the OS page cache, not on disk. If the system crashes or loses power after `rename` returns but before the cache is flushed, the new file path exists but the inode contains zero or garbage bytes — exactly the partial-write scenario the pattern was meant to prevent. `fsync(fd)` forces the kernel to flush all dirty pages for that file descriptor to durable storage before you proceed. For LDS storage nodes writing blocks, skipping `fsync` means "crash-safe" is an illusion — the atomic rename is only as durable as the flush that precedes it.

> [!question]- `errno` must be checked immediately after a failing syscall. Why can it change before you read it?
> `errno` is thread-local but not "sticky" — any subsequent successful or failing syscall will overwrite it. If your error handling path calls `malloc`, `close`, `fprintf`, or any other function that makes a syscall, `errno` may be changed by those calls before you read it. The pattern is: check the return value, then immediately save `errno` into a local variable (`int saved_errno = errno`), then do your cleanup and reporting using the saved value. Functions like `perror` and `strerror` read `errno` internally, so they must also be called before any other syscall.

> [!question]- `lseek(fd, 0, SEEK_END)` is used in LDS to find a file's size. What is the subtle bug in the pattern `size = lseek(fd, 0, SEEK_END); buf = malloc(size); read(fd, buf, size)`?
> The file can grow between the `lseek` and the `read`. Another process or thread appending to the file means `read` returns more bytes than `size` — but the buffer is only `size` bytes, so the read overflows. The fix is to use `fstat(fd, &st)` to get `st.st_size` (also a snapshot, but from the already-opened fd, slightly safer), and then pass `size` as the maximum to `read`, not an exact count. Alternatively, read in a loop resizing the buffer as needed. Also: `lseek` does not reposition the fd before the `read`, so the code above always reads 0 bytes because the seek left the position at the end — you need `lseek(fd, 0, SEEK_SET)` before `read`.
