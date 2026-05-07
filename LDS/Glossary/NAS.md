---
name: NAS — Network-Attached Storage
type: concept
---

# NAS — Network-Attached Storage

**[Wikipedia →](https://en.wikipedia.org/wiki/Network-attached_storage)**

A storage device accessible over a network that appears to the client OS as a regular local disk. Users read and write files normally; the NAS handles where and how the data is physically stored and retrieved.

## Examples

| Product | Notes |
|---------|-------|
| Synology DS series | Commercial appliance, proprietary OS |
| FreeNAS / TrueNAS | Open-source, x86 hardware |
| **LDS (this project)** | Custom-built from Raspberry Pis |

## How LDS Fits

LDS exposes a virtual block device (`/dev/nbd0`) to the Linux kernel via [[NBD Layer\|NBD]]. Once mounted, it behaves exactly like any other disk — `ls`, `cp`, databases, everything works unchanged. The fact that data is distributed across multiple Raspberry Pi nodes over UDP is invisible to the user.

## Related
- [[NBD Layer]] — how Linux sees our virtual disk
- [[RAID01 Explained]] — how data is kept redundant
- [[System Overview]] — full architecture
