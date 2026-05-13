# C++17 — Practical Simplifications

## The Model
C++17 adds features that remove daily friction — not revolutionary, but every one eliminates a pattern that was previously verbose or unsafe. Five machines that you will use in every codebase after C++17.

## The Five Machines

**Structured Bindings — unpack pairs, tuples, structs**
```cpp
// Before:
auto result = m.find(fd);
int key = result->first;
Handler handler = result->second;

// After:
auto [key, handler] = *m.find(fd);

// Map iteration:
for (const auto& [fd, handler] : m_handlers) {
    handler.invoke();
}
```

**`if constexpr` — compile-time branching in templates**
```cpp
// Before: SFINAE horror (4 specializations) or runtime if (both branches must compile)
template<typename T>
void serialize(T val) {
    if constexpr (std::is_integral_v<T>) {
        write_int(val);           // only compiled for integral T
    } else {
        write_bytes(&val, sizeof(T));   // only compiled for non-integral T
    }
}
```

**`std::optional` — nullable without sentinel values**
```cpp
// Before: return -1 for "not found", or bool output parameter
// After:
std::optional<int> findFd(const std::string& name) {
    auto it = m.find(name);
    if (it == m.end()) return std::nullopt;
    return it->second;
}

auto fd = findFd("nbd0");
if (fd) { connect(*fd); }
int safe = fd.value_or(-1);
```

**`std::string_view` — non-owning string reference**
```cpp
// Before: const std::string& forces a std::string (copies if you pass a literal)
// After:
void log(std::string_view msg) {   // zero allocation for string literals
    write(m_fd, msg.data(), msg.size());
}
log("NBD request received");   // no heap allocation
```

**`std::variant` — type-safe union**
```cpp
// Before: union (no destructor called on members) or base class + virtual
// After:
std::variant<ReadRequest, WriteRequest, FlushRequest> event;
std::visit([](auto& req) { req.execute(); }, event);
```

## In LDS

`services/local_storage/src/LocalStorage.cpp`

C++17 structured bindings would replace:
```cpp
// Current (C++11):
auto it = m_handlers.find(fd);
int key = it->first;
auto& handler = it->second;

// C++17:
auto& [key, handler] = *m_handlers.find(fd);
```

`std::string_view` in the Logger: every log call currently passes `const std::string&` — when passing string literals, this creates a temporary `std::string` (heap allocation). Changing to `std::string_view` eliminates these allocations.

## Validate

1. `for (auto [fd, handler] : m_handlers)` vs `for (const auto& [fd, handler] : m_handlers)`. What's the difference? Which is correct for read-only iteration?
2. `std::optional<int>` vs returning `-1` as "not found" — what specific bug does `optional` prevent?
3. `std::string_view` returned from a function that creates a `std::string` locally. The caller stores the `string_view`. What happens after the function returns?

## Connections

**Theory:** [[Core/Theory/C++/C++17]]  
**Mental Models:** [[Templates — The Machine]], [[STL Containers — The Machine]], [[Undefined Behavior — The Machine]], [[Serialization — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Reactor]] — structured bindings for fd→handler iteration; [[LDS/Application/LocalStorage]] — string_view for zero-allocation log messages
