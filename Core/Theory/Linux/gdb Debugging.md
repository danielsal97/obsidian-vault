# gdb — Debugging

The GNU Debugger. How to find crashes, inspect state, and trace bugs in running C/C++ programs.

---

## Setup

Always compile with `-g` to include debug symbols. Without it, gdb shows only addresses.

```bash
g++ -g -O0 main.cpp -o app    # -O0 prevents optimiser from moving/removing variables
gdb ./app                      # start gdb with the binary
```

---

## Basic Session

```
(gdb) run                      # start the program
(gdb) run arg1 arg2            # start with arguments

# Program crashes → gdb stops at the crash site
(gdb) backtrace                # show call stack (bt for short)
(gdb) bt full                  # backtrace with local variables
(gdb) frame 2                  # switch to frame 2 in the call stack
(gdb) info locals              # show local variables in current frame
(gdb) info args                # show function arguments
(gdb) print x                  # print variable x
(gdb) print *ptr               # dereference pointer
(gdb) print arr[0]@10          # print 10 elements of arr from index 0
```

---

## Breakpoints

```
(gdb) break main               # break at start of main()
(gdb) break file.cpp:42        # break at line 42 of file.cpp
(gdb) break MyClass::method    # break at a method
(gdb) info breakpoints         # list all breakpoints
(gdb) delete 1                 # delete breakpoint #1
(gdb) disable 1                # temporarily disable

# Conditional breakpoint — only stop when condition is true:
(gdb) break file.cpp:42 if i == 100
```

---

## Stepping

```
(gdb) continue       # (c) run until next breakpoint or crash
(gdb) next           # (n) step over — execute one line, don't enter functions
(gdb) step           # (s) step into — enter function calls
(gdb) finish         # run until current function returns, then stop
(gdb) until 50       # run until line 50
```

---

## Watchpoints

Stop when a variable's value changes — invaluable for "who is modifying this?".

```
(gdb) watch x                  # stop when x changes
(gdb) watch *ptr               # stop when *ptr changes
(gdb) rwatch x                 # stop when x is read
(gdb) awatch x                 # stop when x is read or written
```

---

## Examining Memory

```
(gdb) x/10xw 0x7fffffffea10   # examine 10 words (4 bytes each) in hex at address
(gdb) x/s ptr                  # examine as string
(gdb) x/i 0x400500             # disassemble instruction at address

# Format: x/[count][format][size] address
# format: x=hex, d=decimal, s=string, i=instruction
# size:   b=byte, h=halfword(2), w=word(4), g=giant(8)
```

---

## Core Dumps

When a program crashes in production (no debugger attached), it can write a **core dump** — a snapshot of its memory at crash time.

```bash
# Enable core dumps:
ulimit -c unlimited

# Run the program until it crashes:
./app              # generates 'core' file

# Analyse the core:
gdb ./app core
(gdb) bt           # backtrace at crash point
(gdb) info locals
```

---

## Debugging Multi-threaded Programs

```
(gdb) info threads             # list all threads
(gdb) thread 2                 # switch to thread 2
(gdb) bt                       # backtrace for thread 2
(gdb) thread apply all bt      # backtrace for ALL threads at once
```

`thread apply all bt` is the first command to run when debugging a deadlock — shows what every thread is waiting on.

---

## Useful Commands Summary

```
run / r              start
continue / c         resume
next / n             step over
step / s             step into
finish               run to end of function
backtrace / bt       call stack
frame N              switch frame
info locals          local variables
info args            function arguments
print expr           evaluate and print
watch var            stop on change
break loc            set breakpoint
delete N             remove breakpoint
quit / q             exit gdb
```

---

## TUI Mode (Text UI)

Shows source code alongside the gdb prompt.

```bash
gdb -tui ./app
# or inside gdb:
(gdb) tui enable
```

---

## LDS Debugging

```bash
# Build LDS with debug symbols:
make DEBUG=1   # (if Makefile supports it, or add -g to CXXFLAGS)

# Run under gdb with NBD mode:
sudo gdb ./bin/LDS
(gdb) run nbd /dev/nbd0 134217728

# If it crashes, immediately run:
(gdb) bt full
(gdb) thread apply all bt
```

For race conditions: AddressSanitizer (ASan) catches them at runtime — faster than gdb for concurrent bugs. See [[Memory/Memory Errors and Tools]].

---

## Understanding Check

> [!question]- A program crashes with a segfault. What's the first gdb command to run and what does it tell you?
> `backtrace` (or `bt`). It shows the call stack at the moment of the crash — every function that was on the stack, from the innermost (where it crashed) to `main`. This immediately tells you which function caused the crash and how you got there. Follow with `frame N` and `info locals` to inspect variables at each level.

> [!question]- You suspect a variable is being modified by a part of the code you didn't expect. How do you find it with gdb?
> `watch variable_name`. gdb will stop execution the moment that variable's value changes, regardless of which line of code caused it. For pointer targets use `watch *ptr`. This is the fastest way to answer "who is touching this memory?"

> [!question]- What does `thread apply all bt` tell you that a single `bt` doesn't, and when is it essential?
> It prints the call stack for every thread simultaneously. A single `bt` only shows the current thread. This is essential for debugging deadlocks — you can see thread A is waiting on mutex M1 (held by B) while thread B is waiting on M2 (held by A), which immediately identifies the circular wait.

> [!question]- Why should you compile with `-O0` for debugging, and what problem does it solve?
> With optimisation on (`-O2`/`-O3`), the compiler can eliminate variables (they exist only in registers), inline functions (removing frames from the call stack), reorder instructions, and merge branches. gdb then shows "value optimized out" for variables and wrong line numbers. `-O0` disables all this — what you see in gdb matches what you wrote.

> [!question]- You don't have a debugger on the production machine and a process crashed. How do you debug it?
> Core dump. Run `ulimit -c unlimited` before starting the process. When it crashes, it writes a `core` file. Copy the core file + the binary (compiled with `-g`) to your dev machine and run `gdb ./binary core`. You get the full backtrace and variable state at the moment of the crash, as if you were there.
