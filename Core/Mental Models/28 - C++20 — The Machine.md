# C++20 — The Second Revolution

## The Model
The largest C++ update since C++11. Four major machines: Concepts (readable template constraints), Ranges (composable lazy pipelines), Coroutines (async as sequential code), and `std::span` (non-owning buffer view). Plus: `std::jthread`, `std::format`, designated initializers, atomic wait/notify.

## The Four Machines

**Concepts — readable template constraints**
```cpp
// Before: SFINAE — error messages fill pages with template instantiation noise
template<typename T>
requires std::totally_ordered<T>   // clear: T must support <, >, ==
T max(T a, T b) { return a > b ? a : b; }

max("hello", 1);   // error: "const char*" and "int" don't satisfy totally_ordered
                   // ONE clear line, not 40 lines of template noise
```

**`std::span` — non-owning buffer view**
```cpp
// LDS current: passes (char* buf, size_t len) pairs everywhere
// With span: bundles them safely:
void processBlock(std::span<const std::byte> data) {
    // data.data() = the pointer, data.size() = the length
    // can't pass mismatched pointer/size by accident
}

// Works with any contiguous container:
processBlock(my_vector);   // span of vector's data
processBlock(raw_array);   // span of C array
processBlock({ptr, 512});  // explicit span of 512 bytes at ptr
```

**`std::jthread` — RAII thread**
```cpp
// Before (std::thread):
std::thread t(workerLoop);
// if exception is thrown before t.join() → std::terminate on destruction
t.join();   // must not forget

// After (std::jthread):
std::jthread t([](std::stop_token st) {
    while (!st.stop_requested()) { doWork(); }
});
// t.join() called automatically in destructor — RAII
// t.request_stop() — signals the thread to stop via stop_token
```

**`std::format` — type-safe printf**
```cpp
// Before: printf (not type-safe), stringstream (verbose)
// After:
std::string msg = std::format("Read offset={} len={}", offset, len);
LOG(std::format("[{}] Request from fd={}", timestamp(), fd));
```

## In LDS

`utilities/threading/thread_pool/include/thread_pool.hpp`

LDS is declared `-std=c++20` in the build. The ThreadPool workers currently use `std::thread` — upgrading to `std::jthread` would:
1. Remove the manual `join()` loop in the destructor
2. Replace `atomic<bool> m_is_running` with `stop_token` for cleaner cancellation

`std::span` would replace every `(char* buf, size_t len)` pair in `NBDDriverComm` and `TCPDriverComm` — the single most impactful C++20 upgrade for LDS's codebase.

## Validate

1. LDS uses `std::atomic<bool> m_running` to stop the ThreadPool. How would `std::jthread` + `stop_token` replace this pattern?
2. `NBDDriverComm::RecvRequest` takes `char* buf, size_t len`. Rewrite the signature using `std::span<std::byte>`. What specific bug does this prevent?
3. LDS is compiled with `-std=c++20`. Can you use C++11 features like `std::thread` and `make_shared` in the same codebase?

## Connections

**Theory:** [[Core/Theory/C++/C++20]]  
**Mental Models:** [[Threads and pthreads — The Machine]], [[RAII — The Machine]], [[Templates — The Machine]], [[Serialization — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Utilities Framework]] — jthread would replace std::thread + atomic<bool> in ThreadPool; [[LDS/Linux Integration/NBDDriverComm]] — std::span would replace (char* buf, size_t len) pairs  
**Runtime Machines:** [[LDS/Runtime Machines/ThreadPool and WPQ — The Machine]]
