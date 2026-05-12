# C++11 — The Revolution

## The Model
The update that turned C++ from "C with classes" into modern C++. Six machines were added that change how every line of code is written. Before C++11: manual memory management, raw threads, verbose syntax. After: RAII by default, lambdas, auto types, built-in concurrency.

## The Six Machines

**Move Semantics** — steal instead of copy (see file 29)
```cpp
std::vector<char> a(1MB);
std::vector<char> b = std::move(a);   // O(1) steal — before C++11: always O(n) copy
```

**Lambda — inline function objects**
```cpp
// Before: write a struct with operator() — 10 lines
// After:
auto task = [&storage, offset, len]() {
    storage.Read(offset, len);
};
wpq.push(std::move(task));   // the entire task is one expression
```

**`auto` — type deduction**
```cpp
// Before:
std::unordered_map<int, std::shared_ptr<IDriverComm>>::iterator it = m.find(fd);
// After:
auto it = m.find(fd);   // same type, compiler deduces it
```

**Smart Pointers** — RAII for heap (see file 28)
```cpp
// Before: raw new/delete, manual cleanup
// After:
auto driver = std::make_shared<NBDDriverComm>(fd);   // auto-cleaned
```

**Range-based for**
```cpp
for (auto& [fd, handler] : m_handlers) {   // structured binding (C++17 syntax)
    handler.reset();
}
```

**`nullptr` — typed null**
```cpp
// Before: NULL was 0 (integer) — ambiguous in overload resolution
// After: nullptr is type nullptr_t — unambiguous
void f(int);     void f(int*);
f(NULL);         // calls f(int) — bug!
f(nullptr);      // calls f(int*) — correct
```

**`constexpr` — compute at compile time**
```cpp
constexpr int NBD_REQUEST_SIZE = 28;
constexpr int NBD_REPLY_SIZE = 16;
char buf[NBD_REQUEST_SIZE];   // array size known at compile time — no VLA
```

**`std::thread` — built-in threads (no more pthreads in C++)**
```cpp
std::thread worker([this]() { workerLoop(); });
worker.join();
```

## In LDS

`utilities/threading/thread_pool/include/thread_pool.hpp`

The LDS ThreadPool uses C++11 throughout: `std::thread` for workers, `std::mutex`/`std::condition_variable` for synchronization, `std::function<void()>` for type-erased tasks (lambdas), `shared_ptr` for shared ownership of tasks. The entire design is C++11 patterns — none of it was possible in C++03 without heavyweight libraries.

## Validate

1. Before C++11, how did you store a function that captures local variables? Why was it verbose?
2. `auto task = [&storage]() { storage.Read(0, 10); }; wpq.push(task);` vs `wpq.push(std::move(task))`. What's different and why does it matter?
3. A function is overloaded: `void send(int fd)` and `void send(void* ptr)`. You call `send(NULL)`. Which overload is called? With `nullptr`?
