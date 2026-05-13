# C++ Version Comparison — The Timeline

## The Model
C++ is a living machine that adds new parts every 3 years. Each version solved a specific pain. Knowing which version introduced what tells you: why the code looks the way it does, and what you can use if you're targeting a given standard.

## The Timeline

```
C++98/03  ← the baseline (most "old C++" codebases)
  STL containers, templates, exceptions, basic OOP
  Manual memory: new/delete everywhere
  No lambdas, no auto, no move semantics, no threads

C++11  ← THE revolution (2011)
  Move semantics, smart pointers, lambdas, auto
  std::thread, mutex, condition_variable (built-in concurrency)
  nullptr, constexpr, range-for, initializer lists
  → Most "modern C++" jobs require at least C++11 fluency

C++14  ← polish (2014)
  make_unique (accidentally omitted from C++11)
  Generic lambdas (auto parameters)
  Return type deduction

C++17  ← practical (2017)
  Structured bindings, if constexpr
  std::optional, std::variant, std::string_view
  std::filesystem, parallel algorithms
  → Most production codebases have moved to C++17

C++20  ← second revolution (2020)
  Concepts, Ranges, Coroutines
  std::span, std::jthread, std::format
  Modules (experimental), spaceship operator
  → LDS targets C++20

C++23  ← ongoing
  std::print, std::expected, std::flat_map
  Range improvements, monadic optional
```

## Minimum Version Required For Common Features

| Feature | Minimum |
|---|---|
| `auto`, range-for, nullptr | C++11 |
| `shared_ptr`, `unique_ptr` | C++11 |
| `std::thread`, `mutex` | C++11 |
| Lambda captures | C++11 |
| `make_unique` | C++14 |
| Generic lambdas | C++14 |
| Structured bindings | C++17 |
| `std::optional`, `string_view` | C++17 |
| `if constexpr` | C++17 |
| Concepts, `std::span` | C++20 |
| `std::jthread`, `std::format` | C++20 |

## In LDS

`Makefile` — `-std=c++20` flag means:
- All C++11–C++20 features available
- LDS's actual usage: mostly C++11/14 patterns (`shared_ptr`, `thread`, `mutex`, lambdas)
- Upgrade opportunities: `std::jthread` for ThreadPool workers, `std::span` for buffer passing, `std::format` for logging

## Validate

1. An interviewer asks "what does LDS use from C++20?" What's your honest answer, and what are the concrete upgrade opportunities?
2. You're joining a team using C++14. You want to use `std::optional`. Is it available?
3. `std::mutex` was introduced in C++11. Before that, how did C++ programmers handle mutual exclusion?

## Connections

**Theory:** [[Core/Theory/C++/C++11]], [[Core/Theory/C++/C++14]], [[Core/Theory/C++/C++17]], [[Core/Theory/C++/C++20]]  
**Mental Models:** [[C++11 — The Machine]], [[C++14 — The Machine]], [[C++17 — The Machine]], [[C++20 — The Machine]], [[Move Semantics — The Machine]], [[Smart Pointers — The Machine]], [[Templates — The Machine]]  
**LDS Implementation:** [[LDS/DevOps/Build System]] — -std=c++20 flag; actual LDS usage is mostly C++11/14 patterns with C++20 upgrade opportunities
