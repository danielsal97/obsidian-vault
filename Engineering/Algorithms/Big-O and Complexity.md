# Big-O and Complexity

How to measure and reason about algorithm efficiency. Every coding interview uses this.

---

## What Big-O Means

Big-O describes how runtime (or memory) **scales** as input size `n` grows. It ignores constants and lower-order terms — we care about the shape of growth, not the exact number.

```
O(1)       — constant    — doesn't grow with n
O(log n)   — logarithmic — doubles when n squares (binary search)
O(n)       — linear      — grows proportionally
O(n log n) — linearithmic — merge sort, heap sort
O(n²)      — quadratic   — nested loops
O(2ⁿ)      — exponential — every subset (brute-force)
O(n!)      — factorial   — every permutation
```

**Growth rate (n = 1000):**

| Complexity | Operations |
|---|---|
| O(1) | 1 |
| O(log n) | ~10 |
| O(n) | 1,000 |
| O(n log n) | ~10,000 |
| O(n²) | 1,000,000 |
| O(2ⁿ) | 10^300 (unusable) |

---

## Rules

**Drop constants:** O(2n) = O(n). We care about growth shape, not the multiplier.

**Drop lower-order terms:** O(n² + n) = O(n²). The dominant term wins as n → ∞.

**Add sequential steps:** two O(n) loops in sequence = O(n), not O(2n).

**Multiply nested loops:** a loop inside a loop = O(n) × O(n) = O(n²).

```cpp
// O(n): one pass
for (int i = 0; i < n; i++) { ... }

// O(n²): nested
for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++) { ... }

// O(n log n): outer linear, inner halves
for (int i = 0; i < n; i++)
    binary_search(arr, n, target);  // O(log n) each

// O(log n): halving each step
while (n > 1) { n /= 2; }
```

---

## Space Complexity

Memory used as a function of input size.

```cpp
// O(1) space — no extra memory proportional to input
int sum = 0;
for (int x : arr) sum += x;

// O(n) space — allocate proportional to input
std::vector<int> copy(arr);

// O(n) space — recursion stack depth proportional to n
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);  // n frames on stack
}
```

---

## Common Algorithm Complexities

### Sorting

| Algorithm | Best | Average | Worst | Space |
|---|---|---|---|---|
| `std::sort` (introsort) | O(n log n) | O(n log n) | O(n log n) | O(log n) |
| Merge sort | O(n log n) | O(n log n) | O(n log n) | O(n) |
| Quick sort | O(n log n) | O(n log n) | O(n²) | O(log n) |
| Heap sort | O(n log n) | O(n log n) | O(n log n) | O(1) |
| Bubble/insertion | O(n) | O(n²) | O(n²) | O(1) |

### Searching

| Algorithm | Complexity | Requirement |
|---|---|---|
| Linear search | O(n) | None |
| Binary search | O(log n) | Sorted array |
| Hash table lookup | O(1) avg | Hash function |
| BST lookup | O(log n) | Balanced tree |

---

## Binary Search Pattern

Whenever you see a **sorted array** and need to find something — binary search.

```cpp
int binary_search(std::vector<int>& arr, int target) {
    int lo = 0, hi = arr.size() - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;  // avoids overflow vs (lo+hi)/2
        if (arr[mid] == target) return mid;
        if (arr[mid] < target)  lo = mid + 1;
        else                    hi = mid - 1;
    }
    return -1;
}
```

`lo + (hi - lo) / 2` instead of `(lo + hi) / 2` — avoids integer overflow when lo and hi are large.

---

## Recognising Complexity in Code

```cpp
// Single loop → O(n)
for (int i = 0; i < n; i++) { }

// Loop that halves → O(log n)
for (int i = n; i > 1; i /= 2) { }

// Nested loops same range → O(n²)
for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++) { }

// Nested loops second starts at i → O(n²/2) = O(n²)
for (int i = 0; i < n; i++)
    for (int j = i; j < n; j++) { }

// Recursive halving → O(log n)
void f(int n) { if (n > 0) f(n / 2); }

// Recursive two calls → O(2ⁿ)
int fib(int n) { return fib(n-1) + fib(n-2); }

// Recursive two calls with memoisation → O(n)
```

---

## Amortised Analysis

Some operations are occasionally expensive but cheap on average.

**`vector::push_back`:** O(1) amortised.
- Usually O(1) — just writes to the next slot
- Occasionally O(n) — when capacity is exceeded, reallocates and copies
- But doubling capacity means the O(n) copy is paid back over n future O(1) pushes
- Net: O(1) per operation averaged over a sequence

---

## LDS Complexity Reference

| LDS Operation | Complexity | Why |
|---|---|---|
| WPQ push (new command) | O(log n) | Heap push |
| WPQ pop (get next command) | O(log n) | Heap pop |
| LocalStorage read/write | O(1) | Array index by offset |
| Plugin lookup by name | O(1) avg | Hash map in PNP |
| epoll_wait | O(1) | Returns only ready fds |
| Reactor fd dispatch | O(1) | Hash map fd → handler |

---

## Interview Patterns

**"Can you do better than O(n²)?"** — Almost always yes:
- Sort first → O(n log n), then linear scan
- Use a hash map → O(1) lookup replaces O(n) search
- Binary search → O(log n) instead of O(n) scan

**Two-pointer technique:** sorted array, two pointers converging → O(n) instead of O(n²).

**Sliding window:** subarray/substring problems → O(n) instead of O(n²).

**Memoisation:** recursive O(2ⁿ) → O(n) by caching subproblem results.

---

## Understanding Check

> [!question]- An algorithm runs in O(n) for the first half and O(n²) for the second half. What's the total?
> O(n²). You add the two: O(n) + O(n²) = O(n²) because the dominant term wins. The O(n) part becomes irrelevant as n grows.

> [!question]- Why is `mid = lo + (hi - lo) / 2` safer than `mid = (lo + hi) / 2`?
> When `lo` and `hi` are both large (near INT_MAX), `lo + hi` overflows. `(hi - lo)` is always small (never exceeds the array size), so `lo + (hi - lo) / 2` is safe.

> [!question]- `std::sort` is O(n log n). You call it inside a loop of n iterations. What's the total?
> O(n² log n). The outer loop runs n times, and each iteration does O(n log n) work. Multiply: O(n) × O(n log n) = O(n² log n).

> [!question]- You need to check if a value exists in a set 1 million times. The set has 10,000 elements. Which container and why?
> `std::unordered_set` — O(1) average per lookup vs O(log n) for `std::set`. Over 1M lookups: ~1M operations vs ~13M operations. For security-sensitive code where hash-flooding is a risk, `std::set` gives guaranteed O(log n).

> [!question]- What's the space complexity of a recursive depth-first search on a tree with n nodes and depth d?
> O(d) — the call stack holds one frame per level of recursion depth, which equals the tree depth. In a balanced tree d = O(log n); in a worst-case linear tree (like a linked list) d = O(n).
