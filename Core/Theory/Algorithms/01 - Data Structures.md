# Data Structures

The building blocks every interview assumes you know cold.
For each structure: what it is, how it works, complexity, when to use it, and the C++ STL type.

---

## Array / Vector

Contiguous block of memory. O(1) random access by index.

```cpp
std::vector<int> v = {1, 2, 3};
v.push_back(4);       // O(1) amortized
v[2];                 // O(1) access
v.insert(v.begin(), 0); // O(n) — shifts everything
```

| Operation | Complexity |
|---|---|
| Access by index | O(1) |
| Push back | O(1) amortized |
| Insert/delete middle | O(n) |
| Search (unsorted) | O(n) |
| Search (sorted, binary) | O(log n) |

**Cache friendly** — elements are contiguous. Prefer over linked list unless you need O(1) insert/delete in the middle.

---

## Linked List

Nodes with pointers to next (singly) or next+prev (doubly).

```cpp
std::list<int> lst;
lst.push_front(1);    // O(1)
lst.push_back(2);     // O(1)
lst.insert(it, 3);    // O(1) — given iterator
// No random access — must traverse from head
```

| Operation | Complexity |
|---|---|
| Insert/delete at known position | O(1) |
| Access by index | O(n) |
| Search | O(n) |

**Cache unfriendly** — nodes scattered in memory. Use only when you need O(1) insert/delete and never random access.

---

## Hash Table (unordered_map)

Key → value lookup via hash function. Average O(1) for everything.

```cpp
std::unordered_map<std::string, int> map;
map["key"] = 42;       // O(1) avg insert
map["key"];            // O(1) avg lookup — inserts 0 if missing!
map.at("key");         // O(1) avg — throws if missing (safer)
map.count("key");      // 0 or 1 — safe existence check
map.find("key");       // returns iterator, end() if not found
```

| Operation | Average | Worst case |
|---|---|---|
| Insert | O(1) | O(n) — hash collision |
| Lookup | O(1) | O(n) |
| Delete | O(1) | O(n) |

**Collision handling:** chaining (linked list per bucket) or open addressing.  
**When worst case hits:** all keys hash to same bucket — use `std::map` (O(log n) guaranteed) if this is a risk.

---

## Ordered Map (BST / Red-Black Tree)

Keys always sorted. Guaranteed O(log n).

```cpp
std::map<std::string, int> map;
map["b"] = 2;
map["a"] = 1;
// Iterates in sorted key order: a, b
for (auto& [k, v] : map) { ... }
map.lower_bound("key");  // first key >= "key"
map.upper_bound("key");  // first key > "key"
```

| Operation | Complexity |
|---|---|
| Insert/lookup/delete | O(log n) |
| Iterate in order | O(n) |
| Min/max | O(log n) |

Use when you need sorted order, range queries, or guaranteed worst-case over hash table.

---

## Stack

LIFO — last in, first out. Push and pop from the top.

```cpp
std::stack<int> s;
s.push(1);
s.push(2);
s.top();    // 2 — peek without removing
s.pop();    // removes 2
```

Use for: function call tracking, DFS, bracket matching, undo.

---

## Queue

FIFO — first in, first out.

```cpp
std::queue<int> q;
q.push(1);
q.push(2);
q.front();  // 1
q.pop();    // removes 1
```

Use for: BFS, task scheduling, any "process in order" problem.

---

## Priority Queue (Heap)

Always gives you the min (or max) element in O(1). Push/pop in O(log n).

```cpp
// Max-heap by default:
std::priority_queue<int> pq;
pq.push(3); pq.push(1); pq.push(2);
pq.top();   // 3 — always the largest
pq.pop();   // removes 3

// Min-heap:
std::priority_queue<int, std::vector<int>, std::greater<int>> min_pq;
```

| Operation | Complexity |
|---|---|
| Push | O(log n) |
| Pop | O(log n) |
| Peek top | O(1) |

**LDS:** The Work Priority Queue (`WPQ`) uses a `priority_queue` — WRITE > READ > FLUSH.

**Internal structure:** binary heap — a complete binary tree stored as an array. Parent at `i`, children at `2i+1` and `2i+2`.

---

## Binary Search Tree (BST)

Each node: left child < node < right child. Used internally by `std::map`/`std::set`.

```
       5
      / \
     3   7
    / \   \
   2   4   8
```

| Operation | Average | Worst (unbalanced) |
|---|---|---|
| Insert/search/delete | O(log n) | O(n) |

`std::map` uses a **self-balancing** BST (Red-Black Tree) — always O(log n).

---

## Set / Unordered Set

Same as map/unordered_map but stores keys only (no values).

```cpp
std::unordered_set<int> seen;
seen.insert(5);
seen.count(5);   // 1 — exists
seen.count(9);   // 0 — does not exist
```

Use for: deduplication, fast existence checks, visited tracking in graph traversal.

---

## Deque

Double-ended queue — O(1) push/pop from both front and back.

```cpp
std::deque<int> dq;
dq.push_front(1);
dq.push_back(2);
dq.pop_front();
dq[0];  // O(1) random access
```

---

## Choosing the Right Structure

| Need | Use |
|---|---|
| Fast lookup by key | `unordered_map` (O(1) avg) |
| Sorted keys, range queries | `map` (O(log n)) |
| Process in order received | `queue` |
| Always process highest priority | `priority_queue` |
| Undo / DFS / call stack | `stack` |
| Fast insert/delete anywhere | `list` (if you have iterator) |
| Cache-friendly, random access | `vector` |
| Unique elements, fast exists check | `unordered_set` |

---

## Understanding Check

> [!question]- `map["key"]` vs `map.at("key")` — what's the difference and when does it matter?
> `map["key"]` inserts a default-constructed value if "key" doesn't exist — this is a silent bug if you're just checking. `map.at("key")` throws `std::out_of_range` if missing. Use `at()` when the key must exist, `count()`/`find()` when you're not sure.

> [!question]- Why is `vector` almost always better than `list` even though list has O(1) insert?
> Cache locality. `vector` elements are contiguous — the CPU prefetcher loads them ahead. `list` nodes are scattered in heap memory, causing cache misses on every traversal. In practice, iterating a `list` of 1000 elements is often 10x slower than a `vector` even though the complexity is the same O(n).

> [!question]- The LDS WPQ uses a priority_queue. What happens internally when you push a new command?
> The new element is appended at the end of the underlying array (O(1)), then "bubbled up" by swapping with its parent until the heap property is restored — O(log n) comparisons total. The heap is stored as a flat array: parent at index `i`, children at `2i+1` and `2i+2`.

> [!question]- Hash table worst case is O(n). When does this happen and how do you prevent it?
> All keys hash to the same bucket — the table degrades to a linked list. This can happen accidentally (poorly designed hash function) or maliciously (hash-flooding attack in web servers). Prevention: use a good hash function, or switch to `std::map` (O(log n) guaranteed) for security-sensitive lookups.

> [!question]- You need to find the k-th largest element in a stream of numbers. What data structure and why?
> Min-heap of size k. Push each new element; if size exceeds k, pop the minimum. The top of the heap is always the k-th largest. Time: O(n log k). This is the classic "top-k" pattern used in monitoring systems, log analysis, and LDS request prioritization variants.
