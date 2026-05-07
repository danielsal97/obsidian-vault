---
name: Block Number
type: concept
---

# Block Number

The sequential integer address of a 512-byte region of the virtual disk.

```
Virtual disk (e.g. 1 GB = 2,097,152 blocks):

Block 0      Block 1      Block 2      ...      Block N
[512 bytes]  [512 bytes]  [512 bytes]           [512 bytes]
  offset 0    offset 512  offset 1024            offset N×512
```

## Calculation

```cpp
uint64_t block_number = offset / BLOCK_SIZE;   // BLOCK_SIZE = 512
```

The `offset` comes from the NBD request (`DriverData::m_offset`). RAID01Manager uses the block number — not the raw byte offset — as the key for its mapping table.

## Why Block Numbers Matter

The RAID01 distribution algorithm works on block numbers:

```
primary = block_number % num_minions
replica = (block_number + 1) % num_minions
```

Two consecutive writes to `offset=0` and `offset=512` are both block 0 and block 1, which may go to different pairs of minions.

## Related
- [[RAID01 Explained]] — full mapping algorithm
- [[RAID01 Manager]] — implementation
- [[Block Device]] — what a block is
- [[NBD Layer]] — where `offset` comes from
