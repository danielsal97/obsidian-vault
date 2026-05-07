---
name: EIO — I/O Error
type: linux-api
---

# EIO — I/O Error (errno 5)

**[man page →](https://man7.org/linux/man-pages/man3/errno.3.html)** | **[POSIX →](https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/errno.h.html)**

POSIX error code 5 (`errno = EIO`), meaning "Input/output error". Returned to userspace by the kernel when a block device operation fails at the hardware (or virtual hardware) level.

```c
ssize_t n = read(fd, buf, 512);
if (n == -1 && errno == EIO) {
    // The storage device reported an unrecoverable error
    // Could be bad sector, RAID failure, network block device error
}
```

## How LDS Surfaces EIO

When a ReadCommand or WriteCommand exhausts all retries across all available replicas, it has no valid response to return. It signals failure via the NBD reply:

```cpp
// In WriteCommand::Execute() — after all retries exhausted:
driverData->m_status = DriverData::FAILURE;
driver.SendReply(driverData);
// ↑ encodes nbd_reply { error = EIO, handle = 0xABCD }
// ↑ kernel matches handle → unblocks user's write()
// ↑ user's write() returns -1, errno = EIO
```

## What Triggers EIO in LDS

| Scenario | What fails | Result |
|----------|-----------|--------|
| Both minions unreachable (primary + replica) | ReadCommand retries exhausted | EIO on read |
| Both minions unreachable | WriteCommand, no ACK received | EIO on write |
| Data corruption detected | Checksum mismatch | EIO |

## The "Must Always Reply" Rule

The kernel's user process is **blocked** waiting for our NBD reply. If we never send one — even on failure — the user's `read()` or `write()` hangs forever. LDS must always send a reply:

```cpp
// Correct error handling pattern:
try {
    result = fetchFromMinion(...);
} catch (...) {
    driverData->m_status = DriverData::FAILURE;
}
driver.SendReply(driverData);  // ← always runs, even on failure
```

→ See [[Request Lifecycle]] — Error Handling section.

## Related
- [[Request Lifecycle]] — the "missing reply bug" and correct pattern
- [[Scheduler]] — when retries run out
- [[Exponential Backoff]] — the retry strategy before EIO is triggered
