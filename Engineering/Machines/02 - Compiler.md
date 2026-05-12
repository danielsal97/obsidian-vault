# Compiler — The Machine

## The Model
A translator who is the only person in the factory who actually reads C++. They convert your human-intent code into a list of CPU instructions — but wherever they encounter a name that belongs to another department, they leave a blank labelled sticky note and keep going.

## How It Moves

```
.cpp (preprocessed text)
      |
      v
[TOKENIZER]       — splits text into atoms: keywords, identifiers, operators
      |
      v
[PARSER → AST]    — builds a tree of meaning: "this is a function call, this is an if-branch"
      |
      v
[SEMANTIC ANALYSIS] — type-checks: "can you add an int and a string? no."
      |
      v
[IR / OPTIMIZER]  — rewrites the tree for speed: dead code removal, inlining, loop unrolling
      |
      v
[CODE GENERATOR]  — emits assembly instructions (.s file)
                    leaves RELOCATION ENTRIES where symbols are unknown
      |
      v
    .s file
```

**WHY the blank slots:** The compiler compiles one `.cpp` at a time. When it sees `storage.Read(request)`, `LocalStorage::Read` is defined in a different `.cpp` — possibly being compiled simultaneously on another CPU core. The compiler cannot wait. It emits a CALL instruction with address `0x00000000` and writes a note in the relocation table: "patch this slot with the real address of `LocalStorage::Read`."

## The Blueprint

- `-O0` = no optimization (fast compile, slow binary, easy to debug — use for development)
- `-O2` = standard optimization (most production builds)
- `-O3` = aggressive (can reorder code in ways that surprise you)
- `-g` = embed debug symbols (line numbers, variable names) into the `.o`
- `-c` = "stop after assembling, do not link" — produce `.o` only
- `-Wall -Wextra` = enable warnings — the compiler's opinion that your code is suspicious

The compiler **never** sees other `.cpp` files. It only knows what's in this one, plus the headers that were pasted in by the Preprocessor.

## Where It Breaks

- **Undeclared identifier**: you used a name the compiler has never seen (missing `#include` or typo)
- **Type mismatch**: `std::string s = 42;` — the translator sees an assignment that violates the type contract
- **Missing return**: function says it returns `int`, path exists that returns nothing — compiler can warn or error
- **NOT a linker error**: if the compiler accepts a function call to an undefined function, that's because the *declaration* was there (from a header). The blank slot is valid. The linker will complain later if no definition exists.

## In LDS

`services/mediator/src/InputMediator.cpp`

When compiled with `g++ -c InputMediator.cpp`, the compiler processes the call to `m_driver->SendReply(request)`. `m_driver` is a `shared_ptr<IDriverComm>` — the compiler knows the *interface* from `IDriverComm.hpp` but doesn't know whether `TCPDriverComm` or `NBDDriverComm` will be used at runtime. It emits a virtual dispatch instruction (vtable lookup) and moves on. No blank slot here — the vtable resolves this at runtime, not link time.

## Validate

1. You compile `InputMediator.cpp` alone with `-c`. It calls `LocalStorage::Read`. The build succeeds. Why didn't the compiler complain about `LocalStorage::Read` not being defined?
2. What does `-O2` actually do to your `for` loop that iterates over a known-size array?
3. You add `-g` to the build flags. The binary grows. Where does the extra data go, and does it affect runtime performance?
