# STL Containers

---

## Sequence Containers

### vector — Dynamic Array

```cpp
std::vector<int> v = {1, 2, 3};
v.push_back(4);         // O(1) amortised
v.pop_back();           // O(1)
v[2];                   // O(1) — no bounds check
v.at(2);                // O(1) — throws if out of range
v.size();               // number of elements
v.capacity();           // allocated slots (≥ size)
v.reserve(100);         // pre-allocate — avoids repeated reallocation
v.resize(50);           // change size (fills new elements with 0)
v.clear();              // remove all elements, capacity unchanged
v.empty();              // true if size == 0
v.data();               // raw pointer to underlying array
```

**Reallocation:** when `size == capacity`, vector allocates a new buffer (typically 2x), moves all elements, frees old buffer. This invalidates all iterators and pointers into the vector.

**Reserve before filling:**
```cpp
v.reserve(n);           // avoid n reallocations
for (int i = 0; i < n; ++i) v.push_back(i);
```

---

### deque — Double-Ended Queue

```cpp
std::deque<int> d;
d.push_back(1);    // O(1)
d.push_front(0);   // O(1) — unlike vector
d.pop_front();     // O(1)
d[i];              // O(1)
```

Not a contiguous buffer — chunk of chunks. Slightly slower random access than vector. Use when you need fast front insertion/deletion.

---

### list — Doubly Linked List

```cpp
std::list<int> l;
l.push_back(1);
l.push_front(0);
auto it = l.begin();
l.insert(it, 99);   // O(1) insert at iterator
l.erase(it);        // O(1) erase at iterator
```

No random access (`l[i]` doesn't exist). Use when you frequently insert/erase in the middle. Poor cache performance — nodes scattered in memory.

---

## Associative Containers

### map — Sorted Key-Value

```cpp
std::map<std::string, int> m;
m["key"] = 42;         // insert or update — O(log n)
m.at("key");           // O(log n) — throws if not found
m.count("key");        // 0 or 1
m.find("key");         // iterator, or m.end() if not found
m.erase("key");        // O(log n)

// Iterate in sorted order:
for (auto& [k, v] : m) { ... }
```

Implemented as red-black tree. All operations O(log n). Keys are sorted.

---

### unordered_map — Hash Map

```cpp
std::unordered_map<std::string, int> m;
m["key"] = 42;         // O(1) average
m.find("key");         // O(1) average
m.erase("key");        // O(1) average
m.reserve(100);        // pre-allocate buckets
```

O(1) average, O(n) worst (all same bucket). No ordering. Faster than `map` for large datasets.

**Custom hash:**
```cpp
struct MyHash {
    size_t operator()(const MyKey& k) const { ... }
};
std::unordered_map<MyKey, int, MyHash> m;
```

---

### set / unordered_set

Like `map`/`unordered_map` but keys only, no values.

```cpp
std::unordered_set<int> s;
s.insert(5);
s.count(5);    // 1 if present, 0 if not
s.erase(5);
```

---

## Container Adaptors

### stack

```cpp
std::stack<int> s;     // backed by deque by default
s.push(1);
s.top();               // peek without removing
s.pop();               // remove (no return value)
s.empty();
```

### queue

```cpp
std::queue<int> q;
q.push(1);
q.front();             // peek
q.pop();               // remove front
```

### priority_queue

```cpp
std::priority_queue<int> pq;   // max-heap by default
pq.push(3);
pq.push(1);
pq.push(5);
pq.top();              // 5 — largest element
pq.pop();

// Min-heap:
std::priority_queue<int, std::vector<int>, std::greater<int>> min_pq;
```

---

## Choosing the Right Container

| Need | Use |
|---|---|
| Fast random access, append | `vector` |
| Fast front + back insert | `deque` |
| Fast middle insert/delete | `list` |
| Key-value, sorted | `map` |
| Key-value, fast lookup | `unordered_map` |
| Unique values, fast lookup | `unordered_set` |
| LIFO stack | `stack` |
| FIFO queue | `queue` |
| Priority queue | `priority_queue` |

Default: use `vector`. Switch only when profiling shows a bottleneck.

---

## Iterator Invalidation

Modifying a container can invalidate iterators:

| Container | Invalidates on |
|---|---|
| `vector` | Any reallocation (push_back, resize, insert) |
| `deque` | Insert/erase at front or back (front/back iterators); all on middle insert |
| `list` | Only the erased element's iterator |
| `map`/`set` | Only the erased element's iterator |
| `unordered_map` | Rehash (insert beyond load factor) |

Using an invalidated iterator = undefined behavior.

---

## Common Algorithms (work on any container via iterators)

```cpp
#include <algorithm>

std::sort(v.begin(), v.end());
std::sort(v.begin(), v.end(), std::greater<int>());   // reverse

std::find(v.begin(), v.end(), 5);     // iterator to element, or end()
std::count(v.begin(), v.end(), 5);    // occurrences

std::min_element(v.begin(), v.end());
std::max_element(v.begin(), v.end());

std::reverse(v.begin(), v.end());
std::unique(v.begin(), v.end());      // remove consecutive duplicates

// Lambda:
auto it = std::find_if(v.begin(), v.end(), [](int x){ return x > 5; });

std::for_each(v.begin(), v.end(), [](int& x){ x *= 2; });
```
