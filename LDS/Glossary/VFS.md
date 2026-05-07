---
name: VFS — Virtual File System
type: linux-kernel
---

# VFS — Virtual File System

**[Wikipedia →](https://en.wikipedia.org/wiki/Virtual_file_system)** | **[Kernel docs →](https://www.kernel.org/doc/html/latest/filesystems/vfs.html)**

The Linux kernel abstraction layer that sits above all concrete filesystems (ext4, NTFS, NFS, FAT, etc.) and presents a uniform interface to userspace. Every `open()`, `read()`, `write()`, `stat()` call goes through VFS first.

## The Stack

```
User process
  write(fd, buf, 512)
        │
        ▼
   VFS layer          ← uniform interface: inodes, dentries, file operations
        │
        ▼
  Filesystem          ← ext4, xfs, tmpfs, etc.
        │
        ▼
  Block layer         ← I/O scheduler, device mapper
        │
        ▼
  Block driver        ← SCSI, NVMe, NBD, loop, ...
        │
        ▼
  Physical / virtual storage
```

## How LDS Plugs In

LDS registers itself as a **block driver** via the NBD kernel module. The VFS and filesystem layers sit above NBD and know nothing about how NBD works. Steps:

1. `modprobe nbd` — load the NBD kernel driver
2. Our LDS process connects to `/dev/nbd0` via ioctl
3. `mkfs.ext4 /dev/nbd0` — lay a filesystem on top
4. `mount /dev/nbd0 /mnt/nas` — VFS mounts ext4 on top of our block device

From the VFS's perspective, `/dev/nbd0` is just another block device — identical to an SSD. The ext4 layer sends read/write block requests; the NBD driver forwards them to LDS; LDS distributes them across RPi minions.

## Related
- [[NBD Layer]] — how LDS registers as a block device
- [[Block Device]] — what a block device is
- [[Request Lifecycle]] — the full path from VFS to minion
