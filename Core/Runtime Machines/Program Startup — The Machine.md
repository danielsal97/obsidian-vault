# Program Startup — The Machine

## The Model

`exec("./program")` is not "start the program." It's "replace this process with the program." The kernel loads the binary, sets up the stack, hands off to the dynamic linker, which then hands off to C runtime init, which finally calls `main()`. Three handoffs before your first line runs.

## How It Moves

```
exec("./LDS", argv, envp)
      │
      ▼
Kernel: ELF loader
  → mmap() .text segment (readable, executable)
  → mmap() .data segment (readable, writable) — initialized globals
  → mmap() .bss segment (zero-filled pages) — uninitialized globals
  → set up initial stack:
      [argc] [argv[0]...argv[n]] [NULL] [envp[0]...envp[m]] [NULL] [aux vector]
  → read PT_INTERP from ELF: path to dynamic linker (/lib64/ld-linux-x86-64.so.2)
  → map dynamic linker into process, jump to its entry point
      │
      ▼
Dynamic linker (_dl_start)
  → reads ELF DYNAMIC section: list of needed libraries
  → for each library (e.g. libstdc++.so, libc.so):
      → find in ld.so.cache
      → mmap() into process address space
  → resolve relocations: fill GOT/PLT entries with actual symbol addresses
      │
      ▼
C runtime init (_start → __libc_start_main)
  → call __init_array (C++ global constructors, in link order)
  → set up atexit() handlers
  → call main(argc, argv, envp)
      │
      ▼
main() runs
      │
      ▼
return from main() (or exit())
  → call __fini_array (destructors for global objects, reverse order)
  → flush stdio buffers
  → exit syscall: kernel tears down the process
```

## C++ Global Constructors — The Trap

Global objects with non-trivial constructors run BEFORE `main()`. Order between translation units is undefined. This is the "static initialization order fiasco": if global object A's constructor calls global object B, and B hasn't been constructed yet, undefined behavior.

RAII-dependent systems avoid global objects with constructors, or use `static` locals (initialized on first call, thread-safe since C++11).

## Where Time Is Spent

- Dynamic linker resolution: milliseconds for large binaries with many shared libs
- GOT/PLT first-call overhead: first call to a shared lib function hits PLT trampoline, resolves symbol, patches GOT (cost once per symbol)
- After first call: direct GOT lookup, near-zero overhead

## Links

→ [[01 - Processes]] — exec() semantics
→ [[04 - Linker]] — static linking, ELF sections, relocations
→ [[01 - Process Memory Layout]] — what each ELF section maps to in memory
→ [[01 - RAII]] — why global constructors are dangerous
→ [[Linux Runtime — The Machine]] — what happens after main() runs
