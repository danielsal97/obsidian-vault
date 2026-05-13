# gdb Debugging — The Machine

## The Model
A time machine and microscope combined. Breakpoint = pause the clock at this instruction. Step = advance one tick. Backtrace = unfold the entire call stack — every function that led to this moment, with their local variables frozen in time. Watch = pause the clock the instant this memory address changes.

## How It Moves

```
Normal execution:     instruction → instruction → instruction → ...

With GDB:
  b LocalStorage.cpp:47     ← plant a tripwire at line 47
  run                       ← start execution
  ...
  [Breakpoint hit line 47]  ← clock paused
  bt                        ← unfold the call stack
  p offset                  ← read the value of 'offset' right now
  p *m_data.data()          ← read first byte of storage
  n                         ← advance one line (step over)
  s                         ← advance one line (step into function)
  c                         ← continue until next breakpoint
  watch m_running           ← pause when m_running changes
```

## The Blueprint

**Essential commands:**
| Command | Meaning |
|---|---|
| `b file.cpp:42` | Breakpoint at line 42 |
| `b ClassName::method` | Breakpoint at function |
| `r [args]` | Run the program |
| `c` | Continue until next breakpoint |
| `n` | Next line (step over function calls) |
| `s` | Step into function call |
| `bt` / `backtrace` | Full call stack |
| `p expr` | Print expression value |
| `x/16xb addr` | Examine 16 bytes at addr in hex |
| `watch var` | Break when var changes |
| `info locals` | All local variables |
| `thread apply all bt` | Backtrace of ALL threads |

**Core dump analysis:**
```bash
# Enable core dumps:
ulimit -c unlimited

# Run program — if it crashes, core is generated
./lds_server

# Analyze:
gdb ./lds_server core
bt   # see where it crashed
```

**TUI mode:** `gdb -tui ./lds_server` — splits terminal: source code top, commands bottom. You see exactly which line is executing.

## Where It Breaks

- **No debug symbols**: compiled without `-g` → GDB shows assembly, not source. Add `-g` to Makefile.
- **Optimized code (-O2)**: variables may be in registers, inlined, or reordered — `p var` says "optimized out". Use `-O0 -g` for debugging.
- **Thread race in debugger**: stepping one thread while others run may make the race disappear (observer effect). Use `set scheduler-locking on` to freeze other threads.

## In LDS

`Makefile` — LDS has a debug build target that compiles with `-g -O0`. The resulting binary retains all symbol names and line mappings.

To debug a crash in `InputMediator::Notify`:
```bash
gdb ./test_input_mediator
b InputMediator.cpp:47
r
bt                        # see full call chain to the crash
p m_driver.get()          # check if shared_ptr is null
thread apply all bt       # check if other threads are in a bad state
```

To debug the mutex deadlock in LocalStorage, run with TSan: `make tsan && ./lds_server` — TSan reports exactly which threads are deadlocked and their lock acquisition order.

## Validate

1. LDS crashes with SIGSEGV. You run `gdb ./lds_server core` and type `bt`. What does the output tell you, and what do you look for first?
2. You set `b LocalStorage::Read`. The breakpoint triggers. `p offset` shows `offset = 18446744073709551615`. What does this value tell you in hex?
3. `thread apply all bt` shows Thread 3 in `__lll_lock_wait`. What does this mean about Thread 3's state?

## Connections

**Theory:** [[Core/Theory/Linux/09 - gdb Debugging]]  
**Mental Models:** [[Processes — The Machine]], [[Stack vs Heap — The Machine]], [[Undefined Behavior — The Machine]], [[Threads and pthreads — The Machine]]  
**LDS Implementation:** [[LDS/Debugging/Testing]], [[LDS/Debugging/Known Bugs]]
