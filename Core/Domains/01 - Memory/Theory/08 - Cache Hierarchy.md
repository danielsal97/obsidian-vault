# Cache Hierarchy

The CPU cache hierarchy bridges the speed gap between the CPU (ns-scale computation) and DRAM (100+ ns latency). Without caches, every load/store would stall for ~100 cycles waiting for DRAM. Modern CPUs can retire instructions in ~0.25 ns — a DRAM wait at that speed wastes ~400 instructions of potential work.

---

## Hierarchy Overview

```
         ┌─────────────────────────────────────┐
CPU Core │  Registers (0 cycles, ~KB total)    │
         │  L1 I-cache + D-cache (~4 cycles,   │  Per-core
         │  32–64 KB each)                     │
         │  L2 cache   (~12 cycles, 256–512 KB)│  Per-core
         └─────────────────┬───────────────────┘
                           │ on-chip bus
         ┌─────────────────┴───────────────────┐
         │  L3 cache   (~40 cycles, 8–64 MB)   │  Shared (all cores)
         └─────────────────┬───────────────────┘
                           │ memory bus
         ┌─────────────────┴───────────────────┐
         │  DRAM (~100–300 cycles, GBs)        │  Shared (all cores)
         └─────────────────────────────────────┘
```

---

## Cache Line

The unit of transfer between all cache levels and DRAM is the **cache line**: **64 bytes** on all modern x86 CPUs.

```
Reading one byte from DRAM costs the same as reading 64 bytes — the CPU always fetches the entire line.

int arr[16];   // 64 bytes = exactly one cache line
arr[0] = 1;   // fetches all 64 bytes into cache
arr[1] = 2;   // cache hit — free
arr[15] = 2;  // cache hit — free
arr[16] = 2;  // cache miss — fetches next 64-byte line
```

---

## Access Patterns and Cache Behavior

### Sequential (cache-friendly):
```c
for (int i = 0; i < N; i++) sum += arr[i];
```
- Each cache miss fetches 64 bytes = 16 ints
- Cache miss rate: 1/16 = 6.25%
- Hardware prefetcher detects stride-1 pattern → prefetches ahead automatically

### Linked list traversal (cache-hostile):
```c
while (node) { sum += node->val; node = node->next; }
```
- Each `node->next` pointer points to a random heap location
- Likely a cache miss on every node
- Cache miss rate: ~100% (if nodes don't fit in L1/L2)
- Prefetcher cannot predict pointer values → no prefetching

### Matrix traversal order matters:
```c
// Row-major (C layout) — cache friendly:
for (i) for (j) sum += mat[i][j];   // sequential addresses

// Column-major — cache hostile:
for (j) for (i) sum += mat[i][j];   // jumps by row_size bytes each step
```

---

## Cache Associativity

Each cache is divided into sets. A physical address maps to exactly one set (by bits of the physical address). Within a set, there are N "ways" — N cache lines can live in the same set simultaneously.

- Direct-mapped (1-way): each address has exactly one possible cache slot. Simple, but **cache aliasing** (two hot addresses mapping to the same slot) causes pathological miss rates.
- N-way set-associative: N slots per set. L1 is typically 8-way, L3 16-way.

---

## False Sharing

Two threads write to **different variables that share a cache line**. The CPU's cache coherence protocol (MESI) must invalidate the line on the other core on every write — even though the data is logically independent.

```cpp
// BAD: both counters fit in one cache line
struct { int a; int b; } shared;
// Thread 1: shared.a++   Thread 2: shared.b++
// → each write invalidates the other core's L1 line → ~100 cycle stall each time

// GOOD: separate cache lines
struct alignas(64) Counter { int val; };
Counter c1, c2;   // on separate cache lines
```

Symptom: two threads are "mostly independent" but slower together than each alone. Fix: align per-thread data to 64-byte boundaries.

---

## Prefetching

The CPU hardware prefetcher automatically detects regular access patterns (stride-1, stride-2, etc.) and issues early memory reads before the data is needed. Works well for:
- Sequential array access
- Fixed-stride loops
- Pointer chasing with `__builtin_prefetch` hint

Doesn't work for random access patterns.

---

## Cache and Virtual Memory

TLB and data cache interact:

- **VIPT** (Virtually Indexed, Physically Tagged): L1 cache is indexed by virtual address bits within the page (bits 11:0 — same in virtual and physical). Tag comparison uses the physical address from TLB. TLB and cache lookup happen in parallel.
- Cache uses physical addresses for tags in L2/L3 — always consistent across processes for the same physical data.

---

## NUMA (Non-Uniform Memory Access)

On multi-socket servers, each CPU socket has its own L3 cache and local DRAM. Accessing remote DRAM (on another socket) costs ~300–500 cycles vs ~100 cycles for local.

```bash
numactl --hardware        # show NUMA topology
numactl --membind=0 ./prog # bind memory to socket 0
```

---

## Measuring Cache Performance

```bash
# Cache miss statistics:
perf stat -e L1-dcache-load-misses,LLC-load-misses,cache-misses ./program

# Detailed breakdown:
perf stat -e l1d.replacement,l2_rqsts.miss,llc_misses ./program

# Intel VTune / Linux perf annotate: find which lines cause most misses
```

---

## Understanding Check

> [!question]- An array of 1M ints is traversed sequentially. Approximately how many L1 cache misses occur, and why?
> 1M ints × 4 bytes = 4MB total. Each cache line is 64 bytes = 16 ints. Sequential access triggers a miss only on the first access to each line: 1M / 16 = 62,500 cache misses. L1 is 32KB = 8,192 ints, so the array doesn't fit in L1, but the hardware prefetcher detects the stride-1 pattern and issues prefetch requests before each cache line is needed. Effective observed miss penalty is very low because prefetches hide most of the DRAM latency.

> [!question]- Why does storing per-thread data in a shared struct cause false sharing, and why does aligning to 64 bytes fix it?
> The CPU's cache coherence protocol (MESI) operates at cache line granularity — 64 bytes. If two threads write to different fields within the same cache line, each write causes the other core's copy of the line to be invalidated (marked Modified), forcing a coherence round-trip on every subsequent access. The cores are not sharing data logically, but the hardware can't tell — it just sees writes to the same cache line. Padding each field to 64 bytes (via `alignas(64)`) ensures each field occupies its own cache line, so writes by different cores never conflict.

> [!question]- A linked list of 1M nodes and an array of 1M ints hold the same data. Traversal of the array is ~10× faster. Explain exactly why.
> Array traversal is sequential — the hardware prefetcher detects the stride-1 pattern and issues prefetch requests ahead of time, hiding most DRAM latency. Once a 64-byte cache line is loaded, all 16 consecutive elements are in cache, giving 15 free accesses per miss (6.25% miss rate). Linked list nodes are malloc'd independently and scattered across the heap — pointer values (`->next`) are unpredictable, the prefetcher cannot predict them, and every node access is likely a cache miss (~100% miss rate). Each cache miss = ~100–300 cycle stall. For 1M nodes, that's 100–300M cycles wasted in DRAM waits vs 6.25M stall cycles for the array.

---

**Mental Model:** [[Cache Hierarchy — The Machine]]
**Related:** [[MMU]], [[TLB]], [[Virtual Memory]], [[Stack vs Heap]], [[Pointers]]
