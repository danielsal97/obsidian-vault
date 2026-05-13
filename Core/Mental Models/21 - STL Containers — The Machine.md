# STL Containers — The Machine

## The Model
Five warehouse designs, each built for a different job. Pick the wrong warehouse and every operation costs 10x more than it should. The choice is permanent for the lifetime of that data structure — switching warehouses means rebuilding.

## How It Moves

```
vector:          [0][1][2][3][4][ ][ ]  ← contiguous, gaps reserved
                  ↑ O(1) access by index
                  push_back: O(1) amort (doubles when full, copies all)
                  insert middle: O(n) — slides everything right

unordered_map:   key → hash(key) % buckets → bucket → linked list
                  O(1) avg lookup/insert
                  O(n) worst (all keys hash to same bucket)

map (BST):        sorted tree — always O(log n)
                  iteration gives sorted order

priority_queue:  heap pyramid — O(1) top, O(log n) push/pop

list:            [A]⇄[B]⇄[C]⇄[D]  ← O(1) insert/delete at known position
                  O(n) to find a position (no random access)
```

## The Blueprint

**Critical behaviors:**

```cpp
// vector — iterator invalidation trap:
std::vector<int> v = {1,2,3};
auto it = v.begin();
v.push_back(4);   // MAY REALLOCATE — it is now dangling!

// unordered_map — [] inserts on miss:
std::unordered_map<int,int> m;
int x = m[99];   // inserts {99: 0} if not present
// Use: m.find(99) or m.count(99) to check without inserting

// map — sorted iteration:
for (auto& [k,v] : m) { }   // guaranteed ascending key order

// priority_queue — max-heap by default:
std::priority_queue<int> pq;   // largest at top
std::priority_queue<int, std::vector<int>, std::greater<int>> min_pq;   // smallest at top

// reserve to avoid reallocation:
v.reserve(1000);   // pre-allocate 1000 slots — push_back never reallocates below 1000
```

**Choosing a container:**
- Need index access? → `vector`
- Need fast lookup by key? → `unordered_map`
- Need sorted iteration? → `map`
- Always need min/max? → `priority_queue`
- Frequent insert/delete at arbitrary positions? → `list`
- Need stack (LIFO)? → `vector` + `push_back`/`pop_back`
- Need queue (FIFO)? → `deque` or `queue<T, deque<T>>`

## Where It Breaks

- **`vector` iterator invalidated by push_back**: any stored iterator/pointer to elements becomes dangling after reallocation
- **`map::operator[]` inserts default**: `if (m[k])` creates key k with default value even if you just wanted to check
- **`unordered_map` ordered assumption**: iteration order is undefined — don't assume insertion order

## In LDS

`utilities/thread_safe_data_structures/priority_queue/include/wpq.hpp`

`WorkPriorityQueue` is built on `std::priority_queue` (heap). Tasks (WRITE=2, READ=1, FLUSH=0) are compared by priority. The highest-priority task is always at the top — the `ThreadPool` workers pop the top task, ensuring WRITE operations are served before READ before FLUSH. This is the O(log n) insertion + O(1) top-access contract of the heap.

`design_patterns/reactor/src/reactor.cpp` — `unordered_map<int, HandlerFunc>` maps fd → handler. O(1) lookup on every epoll event. A `map` would give O(log n) — tolerable, but `unordered_map` is correct here since no sorted iteration is needed.

## Validate

1. The Reactor holds 100 registered fds in `unordered_map`. An event fires on fd=47. How many comparisons does the lookup perform on average?
2. The WPQ has 1000 pending tasks. A WRITE task arrives. How many heap swaps occur during insertion, and what is the complexity?
3. You store pointers into a `vector<LocalStorage>`. The vector `reserve(10)` then you add 11 elements. What happens to your stored pointers?

## Connections

**Theory:** [[Core/Theory/C++/08 - STL Containers]]  
**Mental Models:** [[Data Structures — The Machine]], [[Move Semantics — The Machine]], [[Templates — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Utilities Framework]] — WPQ priority_queue; [[LDS/Infrastructure/Reactor]] — unordered_map<fd, handler>  
**Glossary:** [[WPQ]]
