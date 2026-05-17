# Page Fault — The Machine

## The Model

Every memory access goes through the MMU. If the virtual address has no physical page mapped, the MMU raises a #PF (page fault) exception, transfers control to the kernel's fault handler, which resolves the mapping and resumes the instruction that faulted — transparently to the program. The page fault is how the OS implements demand paging, copy-on-write, stack growth, and memory-mapped files. The program never sees it happen.

---

## How It Moves — Demand Paging (anonymous allocation)

```cpp
void* p = mmap(NULL, 4096, PROT_READ|PROT_WRITE,
               MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
*(int*)p = 42;   // <-- page fault here
```

```
mmap() syscall:
  → kernel creates a VMA (virtual memory area) descriptor in the process's mm_struct
  → NO physical page allocated yet
  → returns virtual address — page table entry for this VA is NOT PRESENT
  → cost: ~500ns (syscall + VMA creation)

*(int*)p = 42:
  → CPU translates VA through page table
  → page table entry: PRESENT bit = 0
  → CPU raises #PF exception
      │
      ▼
Kernel page fault handler (do_page_fault):
  → find VMA for the faulting address (RB-tree lookup in mm_struct)
  → VMA found, access is legal (PROT_WRITE matches store)
  → allocate a physical page from the page allocator (get_zeroed_page)
  → zero the page (security: don't leak previous contents)
  → update the page table entry: PA → physical page, PRESENT=1, WRITE=1
  → flush TLB entry for this VA
  → return from fault handler
      │
      ▼
CPU re-executes the faulting instruction:
  → page table walk: PRESENT=1 → physical address found
  → TLB loaded with new mapping
  → store to physical page succeeds
  Cost: ~1-10μs total (first touch per 4KB page)
```

---

## How It Moves — Copy-on-Write After fork()

```cpp
pid_t pid = fork();
if (pid == 0) {
    global_counter++;   // <-- CoW page fault here (child side)
}
```

```
fork() syscall:
  → kernel duplicates page tables: child gets same physical pages as parent
  → all writable entries in BOTH parent and child marked READ-ONLY
  → physical pages shared between parent and child
  Cost: ~50-200μs (page table copy, no physical page copies)

child: global_counter++
  → CPU: write to read-only page → #PF (protection fault)
      │
      ▼
Kernel CoW handler:
  → detect: this is a CoW page (was writable, now shared)
  → allocate new physical page
  → copy content from original page to new page
  → update child's page table: new physical page, WRITE=1
  → update parent's page table: original physical page, WRITE=1 (restore writable)
  → flush TLB for both mappings
  → re-execute the store
  Cost: ~5-20μs (alloc + memcpy 4KB + TLB flush)

After CoW fault:
  parent: maps original page
  child:  maps new copy
  → independent from this point
```

---

## How It Moves — Memory-Mapped File

```cpp
int fd = open("data.bin", O_RDONLY);
void* p = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
uint64_t val = *(uint64_t*)p;   // <-- page fault, reads from disk
```

```
mmap():
  → create VMA, associate with file's inode
  → no pages mapped yet

*(uint64_t*)p:
  → #PF: VA not present
      │
      ▼
Kernel:
  → find VMA → file-backed
  → check page cache: is this file page already in memory?
      → if YES (page cache hit): map existing page → return (~10μs)
      → if NO (page cache miss):
          → allocate physical page
          → submit I/O request to read file data from disk
          → block process (mark TASK_INTERRUPTIBLE)
          → disk read completes (~100μs SSD, ~10ms HDD)
          → page cache filled
          → process wakes
          → map page → return

Cost (cache miss): 100μs-10ms depending on storage
Cost (cache hit):  ~10μs
```

---

## How It Moves — Stack Growth

```cpp
void deep_recursion(int n) {
    char buf[8192];       // large stack frame
    deep_recursion(n-1);  // <-- may fault on first use of buf
}
```

```
Stack grows downward. Kernel pre-maps a guard page below the current stack bottom.

When buf is first accessed:
  → if access is within the guard page region:
      → #PF: guard page hit
      → kernel: is this a valid stack extension? (within rlimit RLIMIT_STACK)
          → YES: allocate new page, extend the stack VMA downward, resume
          → NO: send SIGSEGV (stack overflow)

Stack pages are demand-allocated just like anonymous pages — only faulted in when touched.
```

---

## What Makes a Page Fault Expensive

```
Minimum cost (anonymous, no I/O):
  kernel entry + fault handler + page alloc + TLB flush + return
  → ~1-5μs

CoW fault:
  + memcpy(4KB) + extra TLB flush
  → ~5-20μs

File-backed, page cache hit:
  + inode lookup + page cache search
  → ~10-50μs

File-backed, page cache miss (NVMe):
  + block I/O submission + process sleep + wake
  → ~100μs-1ms

File-backed, page cache miss (HDD):
  + disk seek + rotational delay
  → ~5-15ms
```

---

## Links

→ [[03 - Virtual Memory — The Machine]]
→ [[04 - Paging — The Machine]]
→ [[05 - MMU — The Machine]]
→ [[06 - Page Walk — The Machine]]
→ [[07 - TLB — The Machine]]
→ [[07 - mmap]]
→ [[Memory System — The Machine]]
→ [[Fork and Exec — The Machine]]
