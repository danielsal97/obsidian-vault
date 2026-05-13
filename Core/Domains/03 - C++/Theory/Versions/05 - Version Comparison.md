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

---

## Understanding Check

> [!question]- `make_unique` was introduced in C++14, not C++11. What did people do in C++11, and what problem does `make_unique` fix?
> In C++11: `std::unique_ptr<int> p(new int(42))`. The problem is exception safety: in `f(unique_ptr<int>(new int(42)), g())`, if `g()` throws after `new` but before the `unique_ptr` is constructed, you leak. `make_unique` combines allocation and construction atomically — no leak window. It also avoids writing the type twice and makes ownership intent clear.

> [!question]- When should you use `std::string_view` instead of `const std::string&` as a function parameter?
> Use `string_view` when: the function only reads the string (doesn't store it), and the caller might pass a string literal, a `std::string`, or a substring. `string_view` avoids constructing a `std::string` from a literal (which allocates). The danger: never store a `string_view` in a member variable or return it from a function — it can dangle if the source string is destroyed.

> [!question]- LDS targets C++20 but uses mostly C++11/14 features (`std::atomic`, lambdas, `shared_ptr`, `= delete`). What does this tell you about version targeting?
> Targeting a standard means "at minimum this version" — you can use any feature up to that version. LDS was written using C++11/14 idioms because that's what the codebase needs. Targeting C++20 just ensures the compiler won't reject any C++20 syntax if you add it later (e.g., `std::span` for buffer parameters, `std::jthread` for the ThreadPool). It's forward-compatibility, not a requirement to use every feature.

> [!question]- An interviewer asks "what's new in modern C++?" — what's the most impactful answer you can give in 30 seconds?
> C++11 was the revolution: move semantics (no more expensive copies), RAII smart pointers (no manual memory management), lambdas (inline callbacks without functor boilerplate), and a real threading model. C++17 added `optional`, `variant`, `string_view`, and structured bindings for cleaner code. C++20 added concepts (readable template constraints) and `span` (safe array views). The common theme: making the safe thing the easy thing.

> [!question]- `std::variant` vs C-style `union` — what does variant guarantee that union doesn't?
> A C union has no runtime type tracking — reading the wrong member is UB. `std::variant` always knows which type it holds (stored as a discriminant), `std::get<T>` throws if the type doesn't match, and `std::get_if<T>` returns nullptr safely. Variant also calls the correct constructor and destructor as the type changes — union doesn't. The cost: slightly larger (size of largest type + discriminant + alignment padding).
