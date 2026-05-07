# C++20 — The Second Big Update

C++20 is the largest update since C++11. Four major features: Concepts, Ranges, Coroutines, Modules.

---

## Concepts — Constrained Templates

Constraints on template parameters — better error messages, clearer intent.

```cpp
// Without concepts — error message is pages of template gibberish:
template<typename T>
T max(T a, T b) { return a > b ? a : b; }
max("a", 1);   // incomprehensible error

// With concepts — clear intent + clear error:
template<typename T>
requires std::totally_ordered<T>
T max(T a, T b) { return a > b ? a : b; }
max("a", 1);   // error: 'const char*' and 'int' don't satisfy totally_ordered

// Shorthand:
template<std::totally_ordered T>
T max(T a, T b) { return a > b ? a : b; }

// Even shorter with auto:
auto max(std::totally_ordered auto a, std::totally_ordered auto b) {
    return a > b ? a : b;
}
```

**Defining a concept:**
```cpp
template<typename T>
concept Printable = requires(T t) {
    { std::cout << t } -> std::same_as<std::ostream&>;
};

template<Printable T>
void print(T val) { std::cout << val; }
```

---

## std::span — Non-Owning View of Contiguous Data

Like `string_view` but for any contiguous sequence (array, vector, C array):

```cpp
#include <span>

void process(std::span<int> data) {
    for (int x : data) { ... }
    data[0] = 1;   // modifiable
}

int arr[] = {1, 2, 3, 4, 5};
std::vector<int> v = {1, 2, 3};

process(arr);            // works
process(v);              // works
process({arr+1, 3});     // subspan: elements 1,2,3

// Fixed-size span:
std::span<int, 5> fixed = arr;   // compile-time size
```

Replaces passing `(T* data, size_t n)` pairs — safer, more expressive.

---

## Ranges

A redesigned algorithm library. Lazy evaluation, composable operations, work directly on containers (no begin/end needed).

```cpp
#include <ranges>
namespace rng = std::ranges;
namespace views = std::views;

std::vector<int> v = {5, 3, 1, 4, 2};

// Sort directly on container:
rng::sort(v);

// Composable views (lazy — no intermediate containers):
auto result = v
    | views::filter([](int x){ return x % 2 == 0; })
    | views::transform([](int x){ return x * x; })
    | views::take(3);

for (int x : result) { std::cout << x; }   // evaluated here

// Other useful views:
views::iota(0, 10)          // 0,1,2,...,9
views::reverse(v)
views::drop(v, 2)
views::enumerate(v)         // C++23
views::zip(v1, v2)          // C++23
```

---

## Three-Way Comparison — <=>

The "spaceship operator". Returns `std::strong_ordering`, `std::weak_ordering`, or `std::partial_ordering`.

```cpp
#include <compare>

struct Point {
    int x, y;
    auto operator<=>(const Point&) const = default;  // compiler generates all comparisons
};

Point a{1, 2}, b{1, 3};
a < b;    // true
a == b;   // false
a > b;    // false

// Declaring <=> auto-generates: ==, !=, <, <=, >, >=
```

Before C++20 you had to write all 6 comparison operators manually.

---

## Coroutines

Functions that can suspend and resume. Foundation for async code without callbacks.

```cpp
#include <coroutine>

// Generator — yields values lazily:
Generator<int> iota(int start) {
    while (true) {
        co_yield start++;   // suspend, return start
    }
}

for (int x : iota(0) | views::take(5)) {
    std::cout << x;   // 0 1 2 3 4
}
```

`co_yield` — suspend and yield a value  
`co_return` — final return, ends coroutine  
`co_await` — suspend until an awaitable is ready (async I/O, futures)

**For async networking:**
```cpp
Task<std::string> fetch(std::string url) {
    auto response = co_await http_get(url);   // suspend, don't block thread
    co_return response.body;
}
```

Coroutines are complex to implement from scratch — usually use a library (`cppcoro`, `asio`).

---

## std::format — Type-Safe String Formatting

Python-style formatting. Replaces `printf` (unsafe) and `std::stringstream` (verbose).

```cpp
#include <format>

std::string s = std::format("Hello, {}! You are {} years old.", name, age);
std::format("{:>10}", "right");    // right-aligned, width 10
std::format("{:.2f}", 3.14159);   // "3.14"
std::format("{:#010x}", 255);     // "0x000000ff"

// Print directly (C++23):
std::print("x = {}\n", x);
```

---

## Modules (Experimental)

Replaces `#include`. Faster compilation, no header guard needed, no macro leakage.

```cpp
// math.cppm — module definition:
export module math;

export int add(int a, int b) { return a + b; }
int internal_helper() { return 0; }   // not exported

// main.cpp — import:
import math;
int x = add(1, 2);
```

Not yet widely adopted due to tooling/build system complexity. Headers are still the standard in most codebases.

---

## std::jthread — Joining Thread

Like `std::thread` but automatically joins on destruction and supports cancellation:

```cpp
std::jthread t([](std::stop_token stop) {
    while (!stop.stop_requested()) {
        doWork();
    }
});

// t automatically joins when it goes out of scope
// t.request_stop() — signal the thread to stop
```

No need to `join()` manually — RAII thread.

---

## Designated Initializers (from C99)

```cpp
struct Config {
    int port = 7800;
    int timeout = 30;
    bool verbose = false;
};

// Initialize only the fields you care about, by name:
Config c = {
    .port = 9000,
    .verbose = true
    // timeout uses default (30)
};
```

---

## Atomic Wait/Notify

```cpp
std::atomic<int> flag{0};

// Thread 1 — wait until flag != 0:
flag.wait(0);        // blocks until flag changes from 0

// Thread 2 — set and notify:
flag.store(1);
flag.notify_one();   // wake one waiter
flag.notify_all();   // wake all waiters
```

More efficient than `condition_variable` for simple flag patterns.

---

## What's Actually Used Day-to-Day

| Feature | Adoption |
|---|---|
| `std::span` | High — replaces T*/size pairs |
| `std::format` | High — replaces printf/stringstream |
| Concepts | Growing — especially for error messages |
| Ranges | Growing — especially pipeline syntax |
| `std::jthread` | High — safer than std::thread |
| `<=>` with `= default` | High — eliminates comparison boilerplate |
| Coroutines | Low — complex, library support needed |
| Modules | Low — tooling not mature yet |

**LDS uses:** `std::atomic<bool>`, `std::shared_mutex`, `std::function`, lambdas, `shared_ptr`, `= delete`, `override` — all C++11/14.
