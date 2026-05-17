# Fork and Exec — The Machine

## The Model

`fork()` creates a child process by duplicating the parent's virtual address space — not by copying physical memory. All pages are marked copy-on-write: parent and child share physical pages until either one writes. `exec()` replaces the entire address space with a new program: the kernel maps the ELF segments, sets up a new stack, hands control to the dynamic linker, and eventually reaches `main()`. Together, fork+exec is how every process on Linux comes to life.

---

## How It Moves — fork()

```cpp
pid_t pid = fork();
```

```
fork() syscall:
  → allocate new task_struct (kernel process descriptor) for child
  → copy parent's mm_struct (virtual memory descriptor)
  → duplicate page tables:
      → for every mapped page:
          → copy the page table entry
          → clear WRITE bit in BOTH parent and child's entry
          → increment page's reference count
      → physical pages are NOT copied — parent and child point to same pages
  → copy file descriptor table (same open files, same offsets)
  → copy signal handlers, credentials, etc.
  → child gets pid=0 return, parent gets child's PID
  Cost: ~50-200μs (proportional to number of mapped pages, not their contents)

After fork():
  parent:  continues normally
  child:   continues from same instruction, pid == 0 branch
  Both share all physical pages (marked read-only for CoW)
```

---

## How It Moves — Copy-on-Write During fork()

```
parent writes to a page after fork():
  → write to read-only CoW page → #PF
  → kernel: both parent and child reference this page
  → allocate new physical page for parent
  → copy 4KB content
  → update parent's page table: new page, WRITE=1
  → child's mapping unchanged (still original page)
  Cost: ~5-20μs per page touched

child calls exec() immediately (the common case):
  → exec() tears down the entire address space
  → CoW pages never written → no copies ever made
  → fork() effectively had zero memory-copy cost
```

This is why fork()+exec() is cheap despite "duplicating a process" — if exec() follows immediately, no physical page is ever copied.

---

## How It Moves — exec()

```cpp
execv("/usr/bin/myprogram", argv);
```

```
execv() syscall:
  → open the ELF binary
  → read ELF header: verify magic bytes (0x7f E L F), architecture
  → read program headers (PT_LOAD segments):

      PT_LOAD #1: .text + .rodata
        → mmap(NULL, size, PROT_READ|PROT_EXEC, MAP_PRIVATE, fd, offset)
        → kernel creates VMA, no pages loaded yet
      PT_LOAD #2: .data + .bss
        → mmap(NULL, size, PROT_READ|PROT_WRITE, MAP_PRIVATE, fd, offset)
        → .bss portion: MAP_ANONYMOUS (zero-filled on demand)

  → tear down old address space (unmap all previous VMAs, free page tables)
  → set up new stack:
      → mmap anonymous pages for stack region
      → push: argv strings, envp strings, argv[], envp[], auxv[], argc
      → set RSP to top of new stack
  → if INTERP segment exists (shared libraries):
      → mmap the dynamic linker (ld.so) into the address space
      → set entry point = ld.so's _start (not the program's _start yet)
  → return to userspace at entry point
  Cost: ~500μs-2ms (ELF parsing + mmap setup; no actual I/O yet — pages demand-faulted)
```

---

## How It Moves — Dynamic Linker (ld.so)

```
ld.so _start runs (before program's main):
  → read the program's .dynamic section:
      → DT_NEEDED entries: list of required shared libraries (libc.so.6, etc.)
  → for each DT_NEEDED:
      → search LD_LIBRARY_PATH, /etc/ld.so.cache, /lib, /usr/lib
      → open .so file
      → mmap its PT_LOAD segments into the address space
      → add to link map
  → symbol resolution (lazy by default — PLT stubs):
      → GOT/PLT entries initially point to resolver
      → on first call: resolver finds the real function, patches GOT entry
      → subsequent calls: GOT entry points directly, no resolver
  → run each library's .init_array functions (static constructors)
  → run program's .init_array (C++ global constructors)
  → call program's main(argc, argv, envp)
  Cost: ~1-10ms (per library mmap + symbol resolution)
```

---

## How It Moves — Stack Layout at main()

```
High address
┌─────────────────────────────┐
│  envp strings (null-term)   │
│  argv strings (null-term)   │
├─────────────────────────────┤
│  auxv (auxiliary vector)    │  AT_PAGESIZE, AT_HWCAP, AT_RANDOM...
│  NULL                       │
│  envp[n] → NULL             │
│  envp[0..n-1]               │
│  NULL                       │
│  argv[argc] → NULL          │
│  argv[0..argc-1]            │
│  argc                       │  ← RSP at entry to _start
└─────────────────────────────┘
Low address

_start (CRT):
  → pops argc
  → sets up argv, envp pointers
  → calls __libc_start_main(main, argc, argv, init, fini, ...)
      → runs .init_array
      → calls main()
      → calls exit() with main's return value
```

---

## The Full Timeline

```
fork():           ~100μs   duplicate page tables (CoW, no physical copies)
exec():           ~1ms     ELF parse + mmap segments + stack setup
ld.so:            ~5ms     load shared libs + symbol resolution
.init_array:      ~1ms     C++ global constructors
main() entry:     0ns      your code starts here
```

Total from fork() to first line of main(): **~5-10ms** for a typical C++ binary with libc + libstdc++.

---

## Links

→ [[01 - Processes — The Machine]]
→ [[03 - Virtual Memory — The Machine]]
→ [[04 - Paging — The Machine]]
→ [[01 - Processes]]
→ [[Page Fault — The Machine]]
→ [[Program Startup — The Machine]]
→ [[Memory System — The Machine]]
