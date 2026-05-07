---
name: Block Device
type: concept
---

# Block Device

**[Wikipedia →](https://en.wikipedia.org/wiki/Device_file#Block_devices)**

A storage abstraction where data is accessed in fixed-size chunks called **blocks** (typically 512 bytes or 4 KB), rather than as a byte stream. The OS reads and writes whole blocks; it never touches half a block.

## Linux Block Device Stack

```
User process:   read(fd, buf, 4096)
                       │
                  VFS layer
                       │
               Filesystem (ext4, etc.)
                       │
               Block layer (I/O scheduler)
                       │
               Block driver (NBD, SCSI, NVMe...)
                       │
               Physical storage (disk, network, RPi)
```

## LDS as a Block Device

LDS registers `/dev/nbd0` as a block device via the NBD kernel driver. The Linux kernel treats it identically to a hard drive — you can:

```bash
mkfs.ext4 /dev/nbd0       # format it
mount /dev/nbd0 /mnt/nas  # mount it
cp file.txt /mnt/nas/     # use it normally
```

The fact that blocks are stored on Raspberry Pis over UDP is completely transparent to the user.

## Block Size in LDS

LDS uses **512-byte blocks** (the NBD default). The RAID01Manager maps `block_number = offset / 512` to a pair of minion IDs.

## Related
- [[NBD Layer]] — how LDS exposes itself as a block device
- [[RAID01 Explained]] — how blocks are distributed across minions
- [[Block Number]] — the addressing scheme
