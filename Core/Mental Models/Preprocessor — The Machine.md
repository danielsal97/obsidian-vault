# Preprocessor — The Machine

## The Model
A search-and-replace robot running over a raw text file. It has no dictionary. It cannot spell. It manipulates characters. It finishes before any C++ understanding begins.

## How It Moves

```
Input: NBDDriverComm.cpp (text)
       |
       | sees: #include <linux/nbd.h>
       v
[PASTE CONTENTS of /usr/include/linux/nbd.h here, verbatim]
       |
       | sees: #define NBD_REQUEST_MAGIC 0x25609513
       v
[BUILD A LOOKUP TABLE: "NBD_REQUEST_MAGIC" -> "0x25609513"]
       |
       | sees: NBD_REQUEST_MAGIC anywhere in text
       v
[REPLACE that text with "0x25609513"]
       |
       | sees: #ifdef __linux__
       v
[EVALUATE: is __linux__ defined?]
       YES -> keep the block, delete the #ifdef/#endif lines
       NO  -> delete the entire block
       |
       v
Output: one massive .cpp text file — no # directives remain
        compiler sees this output, not the original file
```

WHY it is separate from the compiler:
- The preprocessor runs on text before the compiler tokenizes anything. If `#include` were handled by the compiler, every grammar rule would need to handle "insert file here." Keeping it separate means the compiler receives a single, clean stream of tokens with no file boundaries.
- The robot has no type system. `#define MAX_SIZE 128` replaces the text "MAX_SIZE" with "128" everywhere — including inside strings and comments if the author is careless. It does not know that `MAX_SIZE` is going to become an `int`.

## The Blueprint

Three operations, nothing else:

**File inclusion** (`#include`):
- `#include <file>` — searches system include paths (`/usr/include`, paths in `-I` flags)
- `#include "file"` — searches relative to current file first, then system paths
- Result: the robot opens the file and pastes its entire text content at that line
- Recursive: included files may include other files; the robot processes those too
- Guard macros (`#ifndef __ILRD_DRIVER_DATA_HPP__`) prevent infinite paste loops

**Macro substitution** (`#define`):
- Object-like: `#define FOO 42` — text replacement, zero intelligence
- Function-like: `#define MAX(a,b) ((a)>(b)?(a):(b))` — parameter substitution in text; parentheses are required because the robot does not know operator precedence
- `#undef` removes an entry from the lookup table

**Conditional compilation** (`#ifdef`, `#ifndef`, `#if`, `#else`, `#endif`):
- The robot evaluates the condition against its lookup table
- Entire blocks of text vanish if the condition is false — the compiler never sees them
- This is how platform-specific code works: `#ifdef __linux__` removes the block on macOS

```cpp
// From NBDDriverComm.cpp — preprocessor pastes all of these:
#include <linux/nbd.h>    // pastes ~500 lines including nbd_request struct
#include <sys/ioctl.h>    // pastes ioctl() declaration
#include "NBDDriverComm.hpp"  // pastes class declaration
```

After preprocessing, the compiler sees one file containing the `nbd_request` struct definition, the `ioctl` declaration, and the `NBDDriverComm` class — all as if they were written in the same file.

## Where It Breaks

- **Missing file**: `#include "InputMediator.hpp"` but the file is not on any `-I` path → `fatal error: InputMediator.hpp: No such file or directory`. The compiler never starts.
- **Macro collision**: two included headers both `#define STATUS 0` with different values. The second silently wins. The bug surfaces as a wrong value deep in logic with no error message.
- **Missing include guard**: a header included twice pastes twice; the compiler sees duplicate struct definitions and reports an error — but the preprocessor is blameless, it just followed orders.
- **Accidental macro expansion**: `#define READ 0` in a system header expands inside `enum ActionType { READ, WRITE }` in `DriverData.hpp`, producing `enum ActionType { 0, WRITE }` — a compile error that looks like a compiler bug.

## In LDS

`/Users/danielsa/Desktop/lds-project/Igit/projects/lds/services/communication_protocols/nbd/include/DriverData.hpp` — lines 1–16

The file opens with an include guard:
```cpp
#ifndef __ILRD_DRIVER_DATA_HPP__
#define __ILRD_DRIVER_DATA_HPP__
```
This is the preprocessor's only defense against double-paste. Every `.cpp` that includes `DriverData.hpp` (NBDDriverComm.cpp, TCPDriverComm.cpp, InputMediator.cpp, LocalStorage.cpp) triggers a paste. The guard means the robot pastes the content the first time, then skips every subsequent `#include "DriverData.hpp"` because `__ILRD_DRIVER_DATA_HPP__` is now in the lookup table.

`/Users/danielsa/Desktop/lds-project/Igit/projects/lds/Makefile` — line 4: `-Iservices/communication_protocols/nbd/include` is added to `FLAGS`. This is the path list the preprocessor searches when it sees `#include "DriverData.hpp"`.

## Validate

1. `NBDDriverComm.cpp` includes `<linux/nbd.h>`. Mentally run the robot: what text is physically pasted, and what does the compiler then see as the definition of `struct nbd_request`?
2. If `DriverData.hpp` had no include guard and was included by both `NBDDriverComm.cpp` and `InputMediator.cpp` during the same compilation unit, what error would the compiler report and why would it be a preprocessor bug, not a C++ bug?
3. The Makefile's `-I` flags on line 4–19 are preprocessor search paths. If you removed `-Iservices/mediator/include`, which LDS source file would fail to compile first, and at which exact line would the robot halt?
