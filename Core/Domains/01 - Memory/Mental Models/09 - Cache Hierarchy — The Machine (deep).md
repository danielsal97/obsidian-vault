# Cache Hierarchy — The Machine (deep)

## The Model

The cache hierarchy is the speed illusion that makes modern CPUs possible. DRAM is 100-200ns away. If every instruction that touched memory had to wait for DRAM, a 3GHz CPU would run at ~10MHz effective speed. Caches bridge the gap by keeping recently and frequently used data in on-chip SRAM (0.5-15ns). The rules of the cache determine everything about memory access performance.

---

## The Four Levels

```
Register files     — on CPU core, 0 cycles
L1 cache (I + D)   — 32-64KB per core,   4 cycles  (~1ns)
L2 cache           — 256KB-1MB per core, 12 cycles (~4ns)
L3 cache (LLC)     — 4-32MB shared,      35 cycles (~10ns)
DRAM               — unlimited,          200 cycles (~60-100ns)
NVMe SSD           — unlimited,          100μs
HDD                — unlimited,          10ms
```

Every access that misses a level goes to the next. A cold access to fresh heap data: L1 miss → L2 miss → L3 miss → DRAM fetch. Total: ~200 cycles. A hot loop accessing the same 32KB repeatedly: all L1 hits, ~1 cycle/access.

---

## Cache Lines — The Unit of Transfer

The CPU never fetches a single byte. It fetches a **cache line** — 64 bytes on x86/ARM. When you access byte 0 of a struct, bytes 0-63 are loaded into cache together. The next access to bytes 1-63 is effectively free (already in cache).

```
Struct:
  offset 0: field_a (4 bytes)
  offset 4: field_b (4 bytes)
  ...
  offset 60: field_p (4 bytes)

All on one cache line. Reading field_a loads all 16 fields into L1.
Next 15 reads: 0 cache misses.
```

This is why array-of-structs vs struct-of-arrays matters for SIMD and loop performance.

---

## How It Moves — Cache Miss

```
CPU executes: mov rax, [ptr]   (load 8 bytes from address ptr)
      │
      ▼
L1 cache lookup (set-associative hash):
  → compute cache set = (ptr >> 6) % num_sets
  → check all ways in that set for matching tag
  → MISS: address not in L1
      │
      ▼
L2 cache lookup:
  → MISS
      │
      ▼
L3 cache lookup:
  → MISS (or HIT: fetch 64-byte cache line from L3 → L2 → L1)
      │
      ▼  (if L3 also missed)
Memory controller request:
  → identify which DRAM bank/row/column
  → if DRAM row already open (row buffer hit): ~50ns
  → if different row (row buffer miss): close row, open new row, read: ~100ns
      │
      ▼
64-byte cache line arrives:
  → fills L3 (evicts least-recently-used line from L3)
  → fills L2 (evicts LRU from L2)
  → fills L1 (evicts LRU from L1)
  → original load completes: mov rax, [ptr] has its data
```

**Spatial prefetching**: CPU's hardware prefetcher detects sequential access patterns. If you access ptr, ptr+64, ptr+128... the prefetcher starts fetching ahead. Sequential array scan: after the first few misses, subsequent accesses hit L1 (prefetched). Linked list walk: random pointers — prefetcher cannot predict, every node is a cache miss.

---

## Write Behavior — Write-Back vs Write-Through

**Write-back** (default on x86): writes go to cache only. Cache line is marked "dirty" (Modified in MESI). Dirty line is flushed to DRAM only when evicted. Burst writes stay in cache, one DRAM write when evicted.

**Write-through**: writes go to cache AND DRAM simultaneously. Slower for write-heavy workloads. Used for memory-mapped device registers (volatile + write-through) to ensure writes reach the device.

**Write combining** (WC): for video memory and DMA buffers. CPU batches multiple writes into a 64-byte buffer. When full (or flushed), sends as a burst. Avoids read-before-write overhead for write-only regions.

---

## Set-Associative Structure — Why Conflict Misses Exist

L1 cache is not a flat lookup. It's divided into **sets** (e.g. 64 sets) and each set has **ways** (e.g. 8 ways = 8-way associative). An address maps to exactly one set (based on address bits), and can occupy any of the 8 ways in that set.

```
64KB L1 cache, 64-byte lines, 8-way associative:
  Number of lines = 64KB / 64B = 1024
  Number of sets  = 1024 / 8 = 128
  Set index bits  = 7 (bits 6-12 of address)
```

If you access 9 addresses that all map to the same set: the 9th evicts one of the first 8. If you then access the evicted address again: conflict miss, even though the cache isn't "full." Classic cause: accessing stride-2048 arrays in a loop.

---

## MESI — Cache Coherence Between Cores

Every cache line on every CPU core is in one of four states (see False Sharing — The Machine for full detail):
- **M**odified: this core wrote it, other cores' copies are invalid
- **E**xclusive: this core has the only copy, unmodified
- **S**hared: multiple cores have valid copies, all clean
- **I**nvalid: this core's copy is stale (or not present)

Write to a Shared line: must invalidate all other copies first (takes bus transaction). This is why sharing writable data between cores is expensive — coherence traffic.

---

## Non-Temporal Stores — Bypass Cache for Large Writes

```cpp
_mm_stream_si32((int*)ptr, value);  // non-temporal store
_mm_sfence();                         // ensure ordering
```

For write-only regions (e.g. zeroing a large buffer, DMA-filling memory): non-temporal stores bypass the cache entirely and write directly to DRAM via write-combining buffers. This avoids polluting the cache with data you'll never read back — preserving cache for data that matters.

Particularly useful in LDS-style systems when zeroing large I/O buffers before sending.

---

## Hidden Costs Summary

| Pattern | Miss rate | Impact |
|---|---|---|
| Sequential array scan | Low (prefetcher helps) | ~1ns/element after warm-up |
| Random access (e.g. hash map) | High | ~100ns per access |
| Linked list traversal | Very high (per-node pointer) | ~100ns per node |
| Array of small structs, accessing one field | Medium (loads whole struct) | Wastes cache bandwidth |
| Two threads writing to adjacent variables | False sharing | ~100ns per write |
| Large object, cold first access | Compulsory miss | 200+ cycles, once |

---

## Related Machines

→ [[07 - TLB — The Machine]]
→ [[04 - Paging — The Machine]]
→ [[../Domains/05 - Concurrency/Mental Models/03 - False Sharing — The Machine]]
→ [[../Domains/03 - C++/Mental Models/17 - std::vector — The Machine]]
→ [[../Domains/03 - C++/Mental Models/19 - Object Layout — The Machine]]
→ [[../Domains/01 - Memory/Theory/08 - Cache Hierarchy]]
