# Interview — Data Structures & Algorithms

Covers what you built in `ds/` and how those structures power LDS components.

---

## What you built in ds/

All implemented from scratch in C, reviewed by an instructor. This is a complete data structures library.

| Structure | File | Key property |
|---|---|---|
| Singly linked list | `sll.c` | O(1) prepend, O(n) search |
| Doubly linked list | `dll.c` | O(1) insert/delete at iterator, O(n) search |
| Sorted list | `sorted_list.c` | Sorted DLL, O(n) insert (find position), O(log n) with skip |
| Stack | `stack.c` | Array-based, O(1) push/pop |
| Queue | `queue.c` | Circular buffer, O(1) enqueue/dequeue |
| Circular buffer | `cbuff.c` | Fixed-size ring, O(1) read/write, no allocation after init |
| Vector | `vector.c` | Dynamic array, amortised O(1) push, O(1) random access |
| Priority queue | `pq.c` / `heap_pq.c` | Heap-based, O(log n) insert, O(log n) extract-min |
| Hash set | `hash_set.c` | Chained, O(1) average insert/lookup |
| BST | `bst.c` | O(log n) average, O(n) worst |
| RBST | `rbst.c` | Randomised BST — O(log n) expected without balancing |
| Binary trie | `bintrie.c` | O(k) lookup where k = key length in bits |
| UID | `uid.c` | PID + time + counter — unique across machines and reboots |
| Scheduler | `scheduler.c` | Time-ordered task runner backed by heap PQ |
| Watchdog | `wd.c` | Process-resurrection using fork/exec + signals |
| FSA | `fsa.c` | Fixed-size allocator — O(1) alloc/free, no fragmentation |
| VSA | `vsa.c` | Variable-size allocator — best-fit, O(n) alloc |
| DHCP | `dhcp.c` | IP allocator — trie-based, O(32) per alloc/free |
| Calc | `calc.c` | Infix expression evaluator — two-stack (operators + operands) |

---

## Big-O complexity to know cold

**Array (random access):** O(1) read/write, O(n) insert/delete (shifting)  
**Linked list:** O(1) insert at iterator, O(n) search  
**Hash table:** O(1) average, O(n) worst (all same bucket)  
**Binary search tree:** O(log n) average, O(n) worst (degenerate)  
**Heap:** O(log n) insert, O(log n) extract-min/max, O(1) peek-min  
**Trie (bit):** O(k) where k = key length in bits  

---

## Why Heap PQ for the Scheduler?

**Q: Why did you use a heap for the Scheduler instead of a sorted array or sorted list?**

The Scheduler's hot path: extract the earliest task, execute it, re-insert it with the new time.

| Structure | Insert | Extract-min | Notes |
|---|---|---|---|
| Sorted array | O(n) | O(1) | Shifting on insert is expensive |
| Sorted linked list | O(n) | O(1) | Pointer chasing on insert |
| **Heap** | **O(log n)** | **O(log n)** | Both operations balanced |
| Unsorted array | O(1) | O(n) | Linear scan to find min is expensive |

The Scheduler loops: extract → execute → re-insert. Both operations happen every tick → heap's O(log n) / O(log n) beats all alternatives.

---

## Hash Table — how it works

**Q: How does your hash set handle collisions?**

Chaining — each bucket is a linked list. When two keys hash to the same bucket, they chain. Average O(1) lookup assuming good distribution; O(n) worst case when all keys collide.

**Q: What makes a good hash function?**

- Distributes keys uniformly across buckets
- Deterministic — same key, same hash
- Fast to compute
- Avalanche effect — small input change → large output change

**Q: What is the load factor?**

`n / m` where n = number of elements, m = number of buckets. High load factor → more collisions → slower. Typical threshold to resize: 0.75. Resizing rehashes all elements into a larger table.

---

## Binary Trie — used for DHCP

**Q: What is a trie? Why did you use it for DHCP?**

A trie stores keys by their prefix. Each bit of the key is one edge (0 = left, 1 = right). Lookup is O(k) where k = key length — independent of how many keys are stored.

For DHCP (IP allocation): a 32-bit IP address is a 32-bit key. Allocate = find the first unoccupied leaf. Free = mark a leaf unoccupied. The trie naturally models the subnet structure — all IPs under a subnet share a prefix.

```
  root
  0/ \1
 /   \
...  ...
depth 32 = individual IP
```

**Complexity:** O(32) = O(1) for any IP operation. No sorting needed, no hash collisions.

---

## UID Design

**Q: How does your UID work? What makes it unique?**

```c
typedef struct {
    pid_t pid;      // unique per machine-session
    time_t time;    // unique per second
    size_t counter; // unique within a second
} uid_t;
```

Three components:
- `pid` — unique within a machine at any moment
- `time` — ensures different sessions (even same PID after reboot) produce different UIDs
- `counter` — handles multiple UIDs created within the same second

UIDs are used by the Scheduler to identify tasks — `SchedRemoveTask(sched, uid)` removes a specific task even while the scheduler is running. The implementation uses a `remove_current` flag inside `SchedRun` to safely remove the currently-executing task without invalidating the iterator.

---

## Expression Evaluator (Calc)

**Q: How does the two-stack infix evaluator work?**

Two stacks: one for operands, one for operators. Shunting-yard algorithm:

1. Read token left-to-right
2. If number → push onto operand stack
3. If operator → while top of operator stack has higher or equal precedence, pop operator and two operands, compute, push result; then push new operator
4. If `(` → push onto operator stack
5. If `)` → pop and evaluate until `(`
6. At end, drain operator stack

Result: correct precedence and associativity without recursion. O(n) time, O(n) space.

---

## Amortised Analysis

**Q: What is amortised O(1)? Give an example.**

Amortised analysis spreads the cost of occasional expensive operations over many cheap ones.

`std::vector::push_back`: usually O(1). When the buffer is full, it doubles capacity — O(n) copy. But this doubling happens only after n pushes, so the cost per push is O(1) amortised.

Your `vector.c` in `ds/` follows the same pattern. The LDS `LocalStorage` uses `std::vector<char>` internally — the buffer is allocated once at construction (size is known: `m_size`), so `push_back` never happens during operation — it's a fixed-size read/write.

---

## Questions the Interviewer Will Ask About ds/

**"How did you test these?"**  
Each structure has a `test/test_XXX.c` file with `assert()` checks for edge cases: empty structure, single element, boundary sizes, wrap-around for circular buffer.

**"How did you handle the circular buffer wrap-around?"**  
Track `head` and `tail` indices, both mod `capacity`. A full buffer is when `(tail + 1) % capacity == head`. This wastes one slot to distinguish full from empty without a separate flag.

**"What's harder: BST or RBST? Why use RBST?"**  
BST degenerates to O(n) with sorted input (becomes a linked list). RBST randomizes the insertion order probabilistically — the expected depth is O(log n) without any rebalancing code. Simpler than AVL or red-black while achieving the same expected complexity.

**"What's an FSA and when is it better than malloc?"**  
Fixed-Size Allocator: pre-allocates a block of N fixed-size chunks. Alloc = pop from free list (O(1)). Free = push back (O(1)). No fragmentation — all chunks are the same size. Better than `malloc` when you allocate and free the same small object repeatedly (e.g., network packets, task nodes). `malloc` has overhead per call and can fragment.
