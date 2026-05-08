# Process Memory Layout

Every process has a private virtual address space divided into segments.

---

## The Map

```
High address  (0x7FFFFFFF FFFFFFFF on 64-bit)
┌─────────────────────────────────────┐
│         Stack                       │  ← grows downward
│         ↓                           │    local vars, function frames, return addresses
│                                     │    ~8MB default limit
├─────────────────────────────────────┤
│         (unmapped gap)              │  ← stack overflow hits this → SIGSEGV
├─────────────────────────────────────┤
│         Memory-mapped files         │  ← mmap(), shared libraries (.so)
├─────────────────────────────────────┤
│         ↑                           │
│         Heap                        │  ← grows upward. malloc/new.
│                                     │    managed by malloc, grows via sbrk/mmap
├─────────────────────────────────────┤
│         BSS                         │  ← uninitialized globals/statics → zeroed at start
├─────────────────────────────────────┤
│         Data                        │  ← initialized globals/statics
├─────────────────────────────────────┤
│         Text (code)                 │  ← compiled machine code. read-only.
├─────────────────────────────────────┤
│         (reserved)                  │
└─────────────────────────────────────┘
Low address  (0x0000000000000000)
```

---

## Text Segment

- Contains compiled machine code
- Read-only — writing to it causes SIGSEGV
- Shared between multiple instances of the same program (one copy in RAM)
- String literals stored here (why `char* s = "hello"; s[0] = 'H'` crashes)

---

## Data Segment

Initialized global and static variables:
```c
int global = 42;          // data segment
static int s = 100;       // data segment

void f() {
    static int count = 0; // data segment — persists across calls
}
```

---

## BSS Segment

Uninitialized (or zero-initialized) global and static variables. The OS zero-fills this at startup. Takes no space in the binary file — just a size annotation.

```c
int global_array[1000000];   // BSS — doesn't add 4MB to the binary
```

---

## Stack

- Local variables and function parameters
- Grows downward (toward lower addresses) on x86-64
- Stack pointer (`rsp`) moves down on function call, up on return
- Each function call creates a **stack frame** containing:
  - Local variables
  - Saved registers
  - Return address
  - Function arguments (some in registers, rest on stack)

```
Stack frame for f():
┌────────────────┐  ← rsp before f() call
│ return address │
│ saved rbp      │
│ local var a    │
│ local var b    │
└────────────────┘  ← rsp during f()
```

Stack overflow: recursion too deep or local array too large → stack pointer goes past the guard page → SIGSEGV.

---

## Heap

- Managed by the C runtime (`malloc`/`free`) or C++ (`new`/`delete`)
- `malloc` uses `sbrk()` (moves heap boundary) or `mmap()` for large allocations
- Grows upward (toward higher addresses)
- Can be fragmented over time

---

## Memory-Mapped Region

`mmap()` maps files or anonymous memory into the virtual address space:
- Shared libraries (`.so` files) are mapped here — multiple processes share one physical copy
- Anonymous `mmap` — like `malloc` but bypasses malloc's free list (used for large allocations)
- File-backed `mmap` — file contents appear as memory; OS handles paging

---

## Virtual vs Physical Memory

Each process sees virtual addresses. The MMU (hardware) translates to physical RAM via page tables maintained by the kernel.

**Pages:** 4KB chunks. Each page can be:
- Mapped to physical RAM
- Swapped to disk
- Not mapped → access causes SIGSEGV

**Address Space Layout Randomization (ASLR):** the kernel randomizes the base addresses of stack, heap, and libraries on each run. Makes exploits harder.

```bash
cat /proc/PID/maps   # see the actual virtual memory map of a process
```

---

## sizeof Examples

```c
// Stack:
int x;                  // 4 bytes on stack
char buf[1024];         // 1024 bytes on stack
struct Point p;         // sizeof(Point) bytes on stack

// Stack pointer moved, but HEAP is used for the contents:
std::vector<int> v(1000);   // v object (24 bytes) on stack, int[] on heap
std::string s = "hello";    // s object on stack, char[] on heap (if long enough)

// Heap:
int* p = malloc(100);   // 100 bytes on heap
int* p = new int[100];  // 400 bytes on heap
```

---

## Checking Process Memory

```bash
/proc/PID/status    # VmRSS (physical RAM used), VmVirt (virtual space)
/proc/PID/maps      # all memory regions with permissions
/proc/PID/smaps     # detailed per-region breakdown
valgrind ./prog     # track heap allocations
```

---

## Understanding Check

> [!question]- Why is the BSS segment described as taking "no space in the binary" even though it can represent megabytes of data at runtime?
> BSS contains uninitialized global and static variables, which are guaranteed by C to be zero at program start. The binary only needs to record the total size of the BSS region — the actual zeros are never stored in the executable file. At load time, the OS allocates physical pages for BSS and zero-fills them (the kernel provides zero pages efficiently via copy-on-write from a shared zero page). A 4MB global array adds only a few bytes to the binary (a size record in the ELF header) rather than 4MB of zeroes.

> [!question]- What goes wrong if you store a pointer to a stack variable in a global or heap-allocated struct, then access it after the function returns?
> The stack frame of the function is "freed" the moment the function returns — the stack pointer moves back up, and subsequent function calls will overwrite those bytes with their own frames and local variables. The pointer in the struct now points to memory that belongs to a different, future stack frame. Reading it gives garbage values; writing through it silently corrupts a different function's local variables or return address. This is undefined behavior and the resulting bug is notoriously hard to reproduce because it depends on what functions are called after the fact.

> [!question]- Why do multiple instances of the same program share one physical copy of the text segment in RAM?
> The text segment contains read-only machine code — every running instance of /usr/bin/ls executes exactly the same instructions. Since no process can modify the text segment (SIGSEGV on any write attempt), the kernel can safely map the same physical pages into every process's virtual address space. Only one copy of the code ever resides in RAM regardless of how many instances are running. The same applies to shared libraries: libstdc++.so is physically loaded once and mapped into every process that uses it, saving potentially hundreds of MB of RAM on a busy system.

> [!question]- How does ASLR affect a developer's ability to debug crashes from /proc/PID/maps or a core dump, and how do you work around it?
> ASLR randomizes the base addresses of the stack, heap, and shared library mappings on every run. A stack address printed in one run is useless for understanding another run's crash — the addresses change. Core dumps and /proc/PID/maps reflect the addresses for that specific run, which is fine for post-mortem debugging of that exact crash. For interactive debugging, disable ASLR per-process with setarch $(uname -m) -R ./program or globally with echo 0 > /proc/sys/kernel/randomize_va_space. GDB also reads the maps from the core dump and adjusts symbol addresses automatically, so ASLR is less of a problem with a proper debugger.

> [!question]- In LDS, the Reactor, ThreadPool, and NBDDriverComm all live in the same process — what memory region does each primarily use, and what would a memory map of the LDS process look like?
> The compiled LDS machine code lives in the text segment (read-only, shared if multiple instances run). Global state (e.g., static members) lives in data/BSS. The Reactor's epoll fd, ThreadPool's worker threads (each with its own stack in the mmap region), and the WPQ's heap-allocated queue nodes all reside on the heap or in thread stacks in the mmap region. The NBD socketpair fds are kernel objects referenced by the fd table, not in the address space directly. /proc/PID/maps would show: the LDS binary text/data/BSS, heap region, one mmap-region stack per worker thread, and multiple shared library mappings (libstdc++, libc, etc.).
