# Memory Errors and Tools

---

## Memory Leak

Allocated memory is never freed. Accumulates until process exits (or runs out of memory).

```c
void f() {
    int* p = malloc(100);
    // forgot to free — 100 bytes leaked every call to f()
}
```

**In long-running servers:** a small leak per request eventually exhausts memory. Process slows, then OOM-killed.

**Detection:** Valgrind, ASan (leak sanitizer), `/proc/PID/status` (watch VmRSS grow).

---

## Use-After-Free

Accessing memory after `free()`. The freed memory may be reallocated to something else — you're corrupting unrelated data.

```c
int* p = malloc(4);
free(p);
*p = 5;   // UB — p is now in malloc's free list
          // this may corrupt malloc's bookkeeping metadata
```

Often causes crashes far from the actual bug — memory is corrupted silently, crash happens when corrupted data is used.

**Detection:** ASan (immediately detects the access), Valgrind.

---

## Double Free

Calling `free()` on the same pointer twice. Corrupts malloc's free list.

```c
free(p);
// ... some code ...
free(p);   // UB — p is already in the free list
```

Modern allocators often detect this and abort. Classic symptom: "free(): double free detected in tcache 2".

**Prevention:** set pointer to NULL after free:
```c
free(p);
p = NULL;
free(p);   // free(NULL) is a no-op — always safe
```

---

## Buffer Overflow / Overread

Writing/reading past the end of an allocated buffer. Overwrites adjacent memory — could be another variable, return address, or malloc metadata.

```c
char buf[8];
strcpy(buf, "this is too long");   // writes 17 bytes into 8-byte buffer
                                    // overwrites whatever is after buf
```

**Stack buffer overflow:** overwrites return address → attacker can redirect execution. Classic exploitation technique. Prevented by stack canaries, ASLR, NX bit.

**Heap buffer overflow:** overwrites malloc metadata or adjacent heap object.

**Detection:** ASan, Valgrind, compiler's `-fstack-protector`.

---

## Stack Overflow

Stack pointer moves past the guard page — OS sends SIGSEGV.

```c
void infinite_recursion() {
    infinite_recursion();   // each call uses stack frame → stack overflow
}

void bad() {
    int arr[10000000];   // 40MB on stack — exceeds ~8MB limit
}
```

---

## Uninitialized Memory Read

Reading a variable before writing a value to it. Contains whatever was previously at that address.

```c
int x;
printf("%d\n", x);   // garbage value — undefined behavior

char buf[64];
send(fd, buf, 64);   // may send uninitialized stack data — security issue
```

**Detection:** Valgrind (MemCheck), MSan (MemorySanitizer: `g++ -fsanitize=memory`).

---

## Tools

### Valgrind

```bash
valgrind ./program
valgrind --leak-check=full --track-origins=yes ./program
```

- Detects: leaks, use-after-free, uninitialized reads, invalid reads/writes
- Works on unmodified binaries
- Slow: 10-50x overhead
- Shows full stack trace at allocation and use

### AddressSanitizer (ASan)

```bash
g++ -fsanitize=address -g program.cpp -o program
./program
```

- Detects: use-after-free, heap/stack/global buffer overflow, use-after-return, leaks
- Fast: ~2x overhead
- Requires recompilation
- Output includes allocation site and access site

```
ERROR: AddressSanitizer: heap-use-after-free on address 0x602000000010
READ of size 4 at 0x602000000010 thread T0
    #0 0x401234 in main /home/user/test.cpp:15
    
0x602000000010 was previously freed at:
    #0 0x401200 in main /home/user/test.cpp:12
```

### MemorySanitizer (MSan)

```bash
g++ -fsanitize=memory -g program.cpp -o program
```

- Detects: uninitialized memory reads
- Reports which variable was not initialized and where it was used

### UBSanitizer (UBSan)

```bash
g++ -fsanitize=undefined -g program.cpp -o program
```

- Detects: signed integer overflow, null pointer dereference, misaligned access, invalid enum value, VLA bounds

### Combine All

```bash
g++ -fsanitize=address,undefined -g program.cpp -o program
```

---

## Best Practices to Avoid Memory Errors

**C:**
- Always check `malloc` return value
- Set pointer to `NULL` after `free`
- Use `strncpy`, `snprintf` instead of `strcpy`, `sprintf`
- Use Valgrind in development

**C++:**
- Use `unique_ptr` / `shared_ptr` — no manual `delete`
- Use `std::vector`, `std::string` — no manual bounds management
- Use `at()` instead of `[]` when you want bounds checking
- Compile with ASan during development:
  ```makefile
  make CXXFLAGS="-fsanitize=address -g"
  ```

---

## Understanding Check

> [!question]- Why does use-after-free often cause crashes far from the actual bug site rather than at the point of the bad access?
> After free(), the memory is returned to malloc's free list. If a subsequent allocation reuses that block, the freed region now contains live data for a completely different object. When the use-after-free write occurs, it silently corrupts that new object's fields — not the old one. The program continues normally until the new object is used and the corrupted data causes an error, which could be thousands of instructions later in an unrelated code path. This temporal distance between cause and symptom makes use-after-free one of the hardest bugs to diagnose without tools like ASan.

> [!question]- What goes wrong if you use ASan and Valgrind together on the same binary?
> ASan works by replacing the system allocator with its own instrumented allocator and inserting shadow memory checks around every memory access at compile time. Valgrind also instruments memory at runtime by replacing allocator calls and intercepting memory accesses. Running both simultaneously causes conflicts: ASan's shadow memory region interferes with Valgrind's instrumentation, and Valgrind may misinterpret ASan's intentional poison bytes as legitimate allocations or accesses. Use one or the other for a given debugging session — ASan for speed and compile-time precision, Valgrind when you need to work on an unmodified binary or need its specific memcheck output format.

> [!question]- Why is sending uninitialized stack data in a network buffer both a bug and a security vulnerability?
> Functionally, the receiver gets garbage bytes that may cause protocol parsing errors or crashes. From a security standpoint, those uninitialized bytes may contain fragments of previous stack frames: passwords, cryptographic keys, pointers, or other sensitive data that was on the stack before this function was called. An attacker can read the received buffer and reconstruct information they should not have. This is the class of vulnerability exploited by Heartbleed (which returned uninitialized heap memory over TLS). The fix is to always initialize buffers before sending: memset(buf, 0, sizeof(buf)) or use calloc instead of malloc.

> [!question]- When would you use MSan (MemorySanitizer) instead of ASan (AddressSanitizer), and why can't ASan catch uninitialized reads?
> ASan detects memory that is accessed outside its valid allocation bounds or after it has been freed — it tracks the validity of memory regions (allocated vs. freed vs. out-of-bounds). It does not track whether the bytes within a valid allocation have been written with meaningful data. MSan tracks the initialization state of every byte: it marks memory as "uninitialized" when allocated and "initialized" when written, then reports a read of any uninitialized byte. Use MSan specifically when hunting for logic bugs caused by reading garbage values from uninitialized variables or buffers — a class ASan cannot see because the memory address is technically valid.

> [!question]- In a long-running LDS minion process, how would you detect a small per-request memory leak without restarting the service?
> Watch /proc/PID/status and specifically the VmRSS field over time — if it grows steadily proportional to request count without plateauing, a leak is likely. More precisely, track VmRSS before and after a known-clean idle period to separate fragmentation from actual leaks. For online leak detection without recompilation, attach Valgrind with --pid or use the heap profiler built into jemalloc/tcmalloc (malloc_stats_print). In development, build with -fsanitize=address,leak and run a representative workload — ASan's leak sanitizer prints all live allocations at process exit with full stack traces. In production, gperftools' heap profiler can sample allocations with low overhead.
