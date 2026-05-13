# Big-O and Complexity — The Machine

## The Model
The shadow a function casts as its input grows. A candle flame casts a fixed shadow (O(1)). A stick held upright casts a shadow proportional to its length (O(n)). A square grid of sticks casts a shadow proportional to its area (O(n²)). Big-O is only about the shape of the shadow — not the size of the candle.

## How It Moves

```
Input n:        1    10    100    1,000    1,000,000
O(1):           1     1      1        1            1
O(log n):       0     3      7       10           20
O(n):           1    10    100    1,000    1,000,000
O(n log n):     0    33    664   10,000   20,000,000
O(n²):          1   100  10000  1000000  10^12   ← unusable at 1M
```

**The rule:** constants disappear at scale. `100n` is O(n). `n/2` is O(n). Only the dominant term survives.

## The Blueprint

**How to read complexity from code:**
```cpp
// O(1): fixed number of operations, no matter n
int top = pq.top();

// O(n): one loop through n elements
for (auto& item : container) { process(item); }

// O(n²): nested loops both proportional to n
for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++) { ... }

// O(log n): each iteration halves the search space
int lo = 0, hi = n;
while (lo < hi) { int mid = lo + (hi-lo)/2; ... }

// O(n log n): sort + scan pattern
std::sort(v.begin(), v.end());   // O(n log n)
for (auto& x : v) { ... }        // O(n)
// total: O(n log n)
```

**Common operations to know cold:**
| Operation | Complexity |
|---|---|
| `unordered_map` lookup | O(1) avg |
| `map` lookup | O(log n) |
| `vector` push_back | O(1) amortized |
| `vector` insert at front | O(n) |
| `std::sort` | O(n log n) |
| Binary search | O(log n) |
| Heap push/pop | O(log n) |
| Heap top | O(1) |

**Amortized O(1):** `vector::push_back` occasionally triggers a realloc (O(n)), but over n pushes the average cost is O(1). The expensive operation is paid for by the many cheap ones.

## Where It Breaks

- **Ignoring constants**: O(1) with a constant of 10^6 is slower than O(n) for small n. Big-O is about asymptotic behavior — measure for your actual input sizes.
- **Cache effects**: O(n) over a linked list may be slower than O(n log n) over a vector because cache misses dominate at large n.
- **Hash collisions**: `unordered_map` is O(1) average, O(n) worst case if all keys hash to the same bucket.

## In LDS

`utilities/thread_safe_data_structures/priority_queue/include/wpq.hpp`

The LDS WorkPriorityQueue is a heap. `push()` is O(log n), `top()` is O(1), `pop()` is O(log n). When n=100 pending tasks, each push costs ~7 comparisons. This is why the WPQ can handle thousands of requests per second without becoming a bottleneck — O(log n) at any realistic queue depth is effectively constant.

## Validate

1. The LDS WPQ holds 1000 pending tasks. A new task arrives. How many comparisons does the heap perform to insert it?
2. An interviewer asks you to find if a value exists in a sorted vector. What's your approach and complexity? What if the vector is unsorted?
3. Two solutions: one does two O(n) passes over the data, one does one O(n log n) pass. Which is faster? Does it depend on n?

## Connections

**Theory:** [[Core/Theory/Algorithms/02 - Big-O and Complexity]]  
**Mental Models:** [[Data Structures — The Machine]], [[STL Containers — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Utilities Framework]] — WPQ heap: push O(log n), top O(1); [[LDS/Infrastructure/Reactor]] — unordered_map O(1) fd→handler lookup  
**Glossary:** [[WPQ]]
