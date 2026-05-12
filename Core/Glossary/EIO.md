---
name: EIO — I/O Error
type: linux-api
---

# EIO — I/O Error (errno 5)

**[man page →](https://man7.org/linux/man-pages/man3/errno.3.html)**

POSIX error code 5 (`errno = EIO`), meaning "Input/output error". Returned to userspace by the kernel when a block device operation fails at the hardware (or virtual hardware) level.

```c
ssize_t n = read(fd, buf, 512);
if (n == -1 && errno == EIO) {
    // The storage device reported an unrecoverable error
}
```

## How LDS Surfaces EIO

When a ReadCommand or WriteCommand exhausts all retries across all available replicas:

```cpp
// In WriteCommand::Execute() — after all retries exhausted:
driverData->m_status = DriverData::FAILURE;
driver.SendReply(driverData);
// ↑ encodes nbd_reply { error = EIO, handle = 0xABCD }
// ↑ kernel unblocks user's write(), returns -1, errno = EIO
```

## What Triggers EIO in LDS

| Scenario | What fails | Result |
|----------|-----------|--------|
| Both minions unreachable (primary + replica) | ReadCommand retries exhausted | EIO on read |
| Both minions unreachable | WriteCommand, no ACK received | EIO on write |
| Data corruption detected | Checksum mismatch | EIO |

## The "Must Always Reply" Rule

The kernel's user process is **blocked** waiting for our NBD reply. If we never send one, the user's `read()` or `write()` hangs forever. LDS must always send a reply, even on failure.

## Connections

**Mental Models:** [[Kernel — The Machine]], [[File Descriptors — The Machine]], [[Signals — The Machine]]  
**LDS Implementation:** [[Request Lifecycle]] — error handling section; [[Scheduler]] — when retries run out  
**Related Glossary:** [[Exponential Backoff]], [[Block Device]]
