# Data Structures — The Machine

## The Model
Five warehouse designs, each optimized for a different access pattern. Choosing wrong is like storing mail in a filing cabinet sorted by envelope color — technically possible, practically unusable. The structure you pick determines which operations cost O(1) and which cost O(n).

## How It Moves

```
ARRAY / VECTOR         HASH MAP               HEAP (Priority Queue)
┌─┬─┬─┬─┬─┐           ┌────────────┐          ┌───[top]───┐
│0│1│2│3│4│           │ key → slot │           │    10     │
└─┴─┴─┴─┴─┘           │ hash(key)  │          ┌┴┐       ┌─┴┐
  O(1) access          │  % buckets │          │7│       │8 │
  O(n) insert          └────────────┘         ┌┴┐┌┴┐   ┌┴┐
  amortized O(1)         O(1) avg lookup       │3││5│   │6│
  push_back              O(n) worst case        always: top = max/min
```

## The Blueprint

| Structure | C++ Type | Access | Insert | Find | Use when |
|---|---|---|---|---|---|
| Array/Vector | `std::vector<T>` | O(1) | O(1) amort. | O(n) | sequential, index access |
| Hash Map | `std::unordered_map<K,V>` | O(1) avg | O(1) avg | O(1) avg | fast lookup by key |
| Ordered Map | `std::map<K,V>` | O(log n) | O(log n) | O(log n) | sorted iteration needed |
| Heap | `std::priority_queue<T>` | O(1) top | O(log n) | — | always want min/max fast |
| Linked List | `std::list<T>` | O(n) | O(1) at pos | O(n) | frequent insert at known pos |

**Key details:**
- `vector::push_back`: amortized O(1) — doubles capacity on overflow, copies all elements
- `unordered_map` vs `map`: use `unordered_map` by default; use `map` only if you need sorted iteration
- `priority_queue` by default is a max-heap (largest element at top); `greater<T>` makes it a min-heap
- `map::operator[]` inserts a default value if key missing — use `find()` when absence is valid

## Where It Breaks

- **Iterator invalidation**: adding to a `vector` may trigger realloc — all existing iterators/pointers become dangling
- **Hash collision**: `unordered_map` with a bad hash function degrades to O(n) lookup
- **`map::operator[]` side effect**: `if (m["key"])` creates the key if absent — use `m.count("key")` or `m.find("key")`

## In LDS

`utilities/thread_safe_data_structures/priority_queue/include/wpq.hpp`

The LDS WorkPriorityQueue IS a heap. Tasks have three priority levels: `WRITE > READ > FLUSH`. The heap ensures the next task dequeued is always the highest-priority one pending. A simple `queue` (FIFO) would not work — a burst of FLUSH tasks would delay WRITE tasks, potentially causing the client to time out.

`design_patterns/reactor/src/reactor.cpp` — the Reactor maintains an `unordered_map<int, Handler>` mapping fd numbers to handler functions. O(1) lookup on every epoll event — critical for the Reactor's performance since it handles hundreds of events per second.

## Validate

1. The Reactor maps fd→handler with `unordered_map`. Why not `map`? What would change in performance and behavior?
2. The WPQ must always serve the highest-priority task. Which property of the heap makes this O(1) instead of O(n)?
3. A `vector` holds 1000 handler objects. You store a pointer to `handlers[500]`. Then you `push_back` a new handler. Is the pointer still valid? Why?

## Connections

**Theory:** [[01 - Data Structures]]  
**Mental Models:** [[Big-O and Complexity — The Machine]], [[STL Containers — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Reactor]] — unordered_map<fd, handler>; [[LDS/Infrastructure/Utilities Framework]] — WPQ heap  
**Glossary:** [[WPQ]]
