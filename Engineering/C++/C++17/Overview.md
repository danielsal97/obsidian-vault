# C++17 — Practical Additions

C++17 added many practical features that simplify common patterns. Widely supported. Most production codebases targeting C++17 or later.

---

## Structured Bindings

Unpack a pair, tuple, struct, or array into named variables:

```cpp
std::pair<int, std::string> p = {42, "hello"};

// Before:
int id = p.first;
std::string name = p.second;

// C++17:
auto [id, name] = p;

// With map iteration (extremely useful):
std::map<std::string, int> m;
for (auto& [key, value] : m) {
    std::cout << key << ": " << value << "\n";
}

// Unpack a struct:
struct Point { int x, y; };
Point pt{3, 4};
auto [x, y] = pt;
```

---

## if constexpr — Compile-Time Branching

Branch at compile time inside a template. The discarded branch is not compiled — eliminates SFINAE complexity.

```cpp
template<typename T>
void serialize(T val) {
    if constexpr (std::is_integral_v<T>) {
        write_int(val);
    } else if constexpr (std::is_floating_point_v<T>) {
        write_float(val);
    } else {
        write_bytes(&val, sizeof(val));
    }
}
```

The compiler only instantiates the branch that matches. No need for template specializations.

---

## std::optional — Nullable Value Without Pointer

Represents a value that may or may not be present. No heap allocation.

```cpp
#include <optional>

std::optional<int> find(const std::vector<int>& v, int target) {
    for (int i = 0; i < v.size(); ++i)
        if (v[i] == target) return i;   // has value
    return std::nullopt;                 // empty
}

auto result = find(v, 42);

if (result.has_value()) {
    std::cout << *result;       // dereference
    std::cout << result.value(); // throws std::bad_optional_access if empty
}

int idx = result.value_or(-1);  // default if empty
```

Replaces: returning -1 as "not found", returning nullptr, output parameters, `std::pair<bool, T>`.

---

## std::variant — Type-Safe Union

Holds exactly one value of a fixed set of types. Like `union` but type-safe.

```cpp
#include <variant>

std::variant<int, double, std::string> v;

v = 42;           // holds int
v = 3.14;         // now holds double
v = "hello";      // now holds string

// Access:
std::get<int>(v);           // throws std::bad_variant_access if not int
std::get_if<int>(&v);       // returns int* or nullptr — safe

// Visit — call the right function for whatever type it holds:
std::visit([](auto& val) {
    std::cout << val << "\n";
}, v);
```

Use case: command/event types, JSON parser results, error-or-value pattern.

---

## std::string_view — Non-Owning String Reference

A lightweight, non-owning view into a string. No allocation, no copy.

```cpp
#include <string_view>

void print(std::string_view sv) {
    std::cout << sv << " (len=" << sv.size() << ")\n";
}

print("hello");               // string literal — no allocation
print(std::string("world"));  // view into existing string — no copy
print(s.substr(0, 5));        // C++17: substr can return string_view with right type

// Does NOT own memory — don't store beyond the source's lifetime:
std::string_view bad() {
    std::string s = "hello";
    return s;   // DANGLING — s is destroyed
}
```

Use as function parameter instead of `const std::string&` when you don't need to store it.

---

## std::filesystem

```cpp
#include <filesystem>
namespace fs = std::filesystem;

fs::path p = "/home/user/file.txt";
p.filename();    // "file.txt"
p.stem();        // "file"
p.extension();   // ".txt"
p.parent_path(); // "/home/user"

fs::exists(p);
fs::is_directory(p);
fs::file_size(p);
fs::create_directory("newdir");
fs::remove(p);
fs::copy("src", "dst");

// Iterate directory:
for (auto& entry : fs::directory_iterator("/path")) {
    std::cout << entry.path() << "\n";
}
```

---

## Fold Expressions — Variadic Template Simplification

Apply an operator across all elements of a parameter pack:

```cpp
// Before C++17 — recursive template:
template<typename T>
T sum(T x) { return x; }
template<typename T, typename... Rest>
T sum(T x, Rest... rest) { return x + sum(rest...); }

// C++17 fold expression:
template<typename... Args>
auto sum(Args... args) { return (args + ...); }   // unary right fold

sum(1, 2, 3, 4);   // 1 + (2 + (3 + 4)) = 10

// Print all args:
template<typename... Args>
void print(Args... args) { (std::cout << ... << args); }
```

---

## Class Template Argument Deduction (CTAD)

```cpp
// Before C++17 — had to specify template args:
std::pair<int, std::string> p(42, "hello");
std::vector<int> v{1, 2, 3};   // OK because of deduction guides

// C++17 — deduced from constructor:
std::pair p(42, "hello");     // pair<int, const char*>
std::vector v{1, 2, 3};      // vector<int>
std::lock_guard lock(m);      // lock_guard<std::mutex>
```

---

## if / switch with Initializer

```cpp
// Before:
auto it = m.find(key);
if (it != m.end()) { use(it->second); }

// C++17 — init in the if:
if (auto it = m.find(key); it != m.end()) {
    use(it->second);
}
// it not accessible here — scoped to the if/else

// switch with init:
switch (auto val = compute(); val) {
    case 0: break;
    case 1: break;
}
```

---

## [[nodiscard]] Attribute

```cpp
[[nodiscard]] int important_result() { return 42; }

important_result();          // WARNING: ignoring return value
auto x = important_result(); // OK
```

Use on functions where ignoring the return value is almost always a bug (error codes, `push_back` that may throw, `lock()`).

---

## Parallel Algorithms

```cpp
#include <execution>

std::sort(std::execution::par, v.begin(), v.end());         // parallel
std::for_each(std::execution::par_unseq, v.begin(), v.end(), fn); // parallel + vectorized
```

---

## inline Variables

```cpp
// Before C++17 — defining a static member in .cpp was required:
// .hpp:  static int count;
// .cpp:  int MyClass::count = 0;

// C++17 — define in header directly:
struct MyClass {
    inline static int count = 0;   // defined here, no .cpp needed
};
```
