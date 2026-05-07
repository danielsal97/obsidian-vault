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
