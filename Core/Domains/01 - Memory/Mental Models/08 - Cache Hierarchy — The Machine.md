# Cache Hierarchy — The Machine

## The Model
A worker's desk, a nearby filing cabinet, a building archive, and a warehouse across town. RAM is the warehouse — huge but slow. L1 cache is the desk — tiny but instant. Work happens at the desk. If the file you need isn't on the desk, you fetch it from the cabinet (L2), then the archive (L3), then the warehouse (DRAM). Each level costs more time. The CPU is always hoping the file is already on the desk.

## How It Moves

```
CPU requests address X
        ↓
L1 cache lookup (~4 cycles, ~32KB)
  HIT  → return data
  MISS ↓
L2 cache lookup (~12 cycles, ~256KB)
  HIT  → load into L1 → return
  MISS ↓
L3 cache lookup (~40 cycles, 8–32MB shared across cores)
  HIT  → load into L2 + L1 → return
  MISS ↓
DRAM access (~100–300 cycles, GBs)
  → load cache line into L3 + L2 + L1 → return
```

**Cache line = 64 bytes.** The unit of transfer at every level is 64 bytes, not 1 byte. Reading `arr[0]` loads `arr[0]..arr[15]` (16 ints) into cache simultaneously.

```
arr[] = [1][2][3][4][5][6][7][8][9][10][11][12][13][14][15][16]...
         └─────────────── 64-byte cache line ────────────────┘
reading arr[0] → entire line cached → arr[1]..arr[15] are FREE
```

## The Blueprint

| Level | Latency | Size | Per-core? |
|---|---|---|---|
| L1 | ~4 cycles | 32–64 KB | Yes (separate I$ and D$) |
| L2 | ~12 cycles | 256–512 KB | Yes |
| L3 | ~40 cycles | 8–64 MB | Shared (all cores) |
| DRAM | ~100–300 cycles | GBs | Shared |

**Spatial locality**: access memory sequentially → cache line is already hot for the next element. Arrays, stack variables, tightly-packed structs all benefit.

**Temporal locality**: access the same memory repeatedly in a short window → stays in L1. Hot variables in a tight loop.

**False sharing**: two threads write to different variables that share a cache line → each write invalidates the line for the other core → cache coherence traffic → performance collapse despite no logical sharing.

```cpp
// BAD: counter_a and counter_b share a cache line
struct Counters { int counter_a; int counter_b; };

// GOOD: pad to separate cache lines
struct Counter { int value; char padding[60]; };
```

**Stack vs heap locality:**
- Stack: variables declared together are adjacent — O(1) distance, always hot after function entry
- Heap: `malloc`'d objects may be scattered across the heap — pointer-chasing (linked lists, trees) causes cache misses at every node

## Program Lifecycle & Memory Flow

Cache sits below everything — every memory access anywhere in the lifecycle goes through it.

```
Load time:
  .text segment paged in → instruction fetches populate I-cache
  .data/.bss touched → data cache fills

Runtime:
  Function call → stack frame pushed → local vars immediately L1 hot
  malloc → heap pointer returned → NOT cached until first write
  First write to new heap page → page fault → physical frame → then cache line loaded
  Repeated access to same buffer → stays L1/L2 hot if fits

Context switch:
  L1/L2 caches are per-core → other thread's data may be evicted
  L3 shared → survives thread switches on same socket
  Process switch → L3 may also go cold if new process has large working set
```

**Why heap allocation hurts cache:**  
`new node` for each linked list element → each node independently `malloc`'d → scattered physical frames → every pointer dereference is a cache miss. A contiguous `std::vector` keeps all elements in adjacent cache lines — traversal is O(n) cache misses for vector, O(n) × cache miss penalty for linked list.

## Where It Breaks

- **Cache miss waterfall**: linked list / tree traversal with pointers to scattered heap nodes — each `->next` is likely a cache miss
- **False sharing in thread pools**: `std::atomic` counters for each thread in a shared array — one cache line for 8 counters → every increment invalidates the line for all 8 cores
- **NUMA penalty**: on multi-socket systems, L3 cache is per-socket. Accessing memory allocated on socket 1 from socket 0 → cross-NUMA access → ~300–500 cycle penalty

## In LDS

The LDS `LocalStorage` buffer (`m_data`) is a contiguous `std::vector<char>` — sequential reads and writes get excellent cache performance. The WPQ's linked-list queue nodes are heap-allocated individually — each `WorkItem* next` pointer dereference may be a cache miss under high load. A ring-buffer WPQ would keep items cache-local. Worker thread stacks are warm after each task — local variables in handlers are L1 hot throughout execution.

## Validate

1. LDS `LocalStorage::Read` copies data from `m_data` into a caller buffer. Why is this copy fast compared to equivalent pointer-chasing through a linked list of the same total size?
2. The ThreadPool has 8 workers, each with a `std::atomic<int>` task counter. If all 8 counters are adjacent in memory (e.g. in an array), what performance problem occurs and why?
3. Why does `std::vector<WorkItem>` have better cache performance than `std::list<WorkItem>` for the WPQ, even though both are O(n) traversal?

## Connections

**Theory:** [[08 - Cache Hierarchy]]
**Mental Models:** [[MMU — The Machine]], [[TLB — The Machine]], [[Stack vs Heap — The Machine]], [[Process Memory Layout — The Machine]]
**Related:** [[Pointers — The Machine]], [[malloc and free — The Machine]], [[Virtual Memory — The Machine]]
