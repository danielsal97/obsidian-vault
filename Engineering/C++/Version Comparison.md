# C++ Version Comparison

---

## Feature Introduction Timeline

| Feature | C++11 | C++14 | C++17 | C++20 |
|---|---|---|---|---|
| `auto` type deduction | ✅ | | | |
| Range-based for | ✅ | | | |
| Lambda expressions | ✅ | Generic (`auto` params) | | |
| Lambda move capture | | ✅ | | |
| Move semantics / `&&` | ✅ | | | |
| `unique_ptr`, `shared_ptr` | ✅ | | | |
| `make_unique` | | ✅ | | |
| `nullptr` | ✅ | | | |
| `constexpr` (basic) | ✅ | Relaxed | | Immediate (`consteval`) |
| `override`, `final` | ✅ | | | |
| `= delete`, `= default` | ✅ | | | |
| `enum class` | ✅ | | | |
| `std::thread`, `std::mutex` | ✅ | | | `std::jthread` |
| `std::atomic` | ✅ | | | atomic wait/notify |
| `std::function` | ✅ | | | |
| Variadic templates | ✅ | | Fold expressions | |
| Type traits | ✅ | `_v` shortcuts | | |
| `static_assert` | ✅ | With no message | | |
| Initializer lists `{}` | ✅ | | | Designated initializers |
| Return type deduction | Trailing `->` | Full `auto` | | |
| Binary literals | | ✅ | | |
| Digit separators `'` | | ✅ | | |
| `std::exchange` | | ✅ | | |
| `[[deprecated]]` | | ✅ | | |
| Structured bindings | | | ✅ | |
| `if constexpr` | | | ✅ | |
| `std::optional` | | | ✅ | |
| `std::variant` | | | ✅ | |
| `std::string_view` | | | ✅ | |
| `std::filesystem` | | | ✅ | |
| CTAD | | | ✅ | |
| `if`/`switch` init | | | ✅ | |
| `[[nodiscard]]` | | | ✅ | |
| Parallel algorithms | | | ✅ | |
| `inline` variables | | | ✅ | |
| Concepts | | | | ✅ |
| Ranges | | | | ✅ |
| `std::span` | | | | ✅ |
| `std::format` | | | | ✅ |
| Coroutines | | | | ✅ |
| Modules | | | | ✅ (experimental) |
| `<=>` spaceship | | | | ✅ |
| `std::jthread` | | | | ✅ |

---

## What Each Version Brought in One Line

| Version | Character | One-liner |
|---|---|---|
| **C++03** | Legacy | Classes, templates, STL — but verbose, error-prone |
| **C++11** | Revolution | Move semantics, lambdas, threads, smart pointers, auto — modern C++ begins |
| **C++14** | Refinement | Polish on C++11 — `make_unique`, generic lambdas, return type deduction |
| **C++17** | Practical | `optional`, `variant`, `string_view`, structured bindings, `if constexpr` |
| **C++20** | Next revolution | Concepts, ranges, coroutines, `span`, `format` |

---

## Which Standard Should You Target?

| Target | Reason |
|---|---|
| **C++17** | Safe default for new projects. Universally supported. All major features available. |
| **C++20** | If your compiler/toolchain supports it. Adds `span`, `format`, concepts. |
| **C++14** | Minimum for modern code. Gives `make_unique`. |
| **C++11** | Last resort. Major improvement over C++03 but missing many conveniences. |
| **C++03** | Never for new code. |

**LDS targets C++20** — uses `std::atomic`, `std::shared_mutex`, lambdas, `shared_ptr`, `= delete`.

---

## Practical "Which Feature to Use" Decisions

| Situation | Use |
|---|---|
| Sole ownership of heap object | `unique_ptr` (C++11) + `make_unique` (C++14) |
| Shared ownership | `shared_ptr` + `make_shared` (C++11) |
| Non-owning string parameter | `string_view` (C++17) |
| Non-owning array parameter | `span` (C++20) |
| Nullable value, no heap | `optional` (C++17) |
| Type-safe union | `variant` (C++17) |
| Thread that auto-joins | `jthread` (C++20) |
| Compare structs | `<=>` with `= default` (C++20) |
| String formatting | `std::format` (C++20) or `snprintf` for C compat |
| Template constraints | Concepts (C++20) or SFINAE (C++11) |
| Compile-time branch in template | `if constexpr` (C++17) |

---

## Compiler Support

| Standard | GCC | Clang | MSVC |
|---|---|---|---|
| C++11 | 4.8+ | 3.3+ | VS 2015+ |
| C++14 | 5.0+ | 3.4+ | VS 2015+ |
| C++17 | 7.0+ | 5.0+ | VS 2017+ |
| C++20 | 10.0+ | 10.0+ | VS 2019 16.6+ |

```bash
g++ -std=c++20 ...   # enable C++20
g++ -std=c++17 ...   # enable C++17
```
