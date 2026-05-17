# Runtime Traversal Paths

Five explicit walks through the machine. Each shows the transition path — what calls what, what blocks where, what wakes when.

Start with [[Linux Runtime — The Machine]] if you want the full map first.

---

## Traversal 1 — Networking: Socket → ThreadPool

A TCP packet arrives. Trace it from hardware interrupt to your application code executing.

```
[Hardware]
  NIC receives Ethernet frame on wire
  → DMA engine writes frame bytes to kernel RX ring buffer (no CPU yet)
  → NIC raises hardware interrupt
        │
        ▼
[Kernel — interrupt context]
  CPU pauses current thread → enters kernel interrupt handler
  → ksoftirqd / NAPI poll: pull from RX ring
  → Ethernet layer: strip header
  → IP layer: validate checksum, TTL, routing
  → TCP layer: validate checksum, find socket (4-tuple hash lookup)
  → append payload to socket receive buffer (sk_buff)
  → socket is readable: add fd to epoll ready list
  → wake any task sleeping in epoll_wait()
        │
        ▼
[User space — Reactor thread]
  epoll_wait() returns: fd=sock_fd, events=EPOLLIN
  → Reactor looks up handler for this fd
  → calls handler.onReadable()
  → recv(fd, buf, len, MSG_DONTWAIT)  [kernel: copy sk_buff → userspace]
  → Reactor does NOT process the data
  → creates Command object: {type=READ, data=buf, len=n}
  → pushes Command to ThreadPool WPQ (priority lane)
  → returns to epoll_wait() immediately
        │
        ▼
[User space — Worker thread]
  WPQ.Pop() → Execute() on worker thread
  → application logic runs: parse, respond, store
  → send() reply: kernel copies to socket send buffer → TCP → NIC
```

**Notes this traversal activates:**
- Hardware: [[Networking Stack — The Machine]] § DMA
- Kernel: [[04 - epoll — The Machine]], [[02 - TCP Sockets — The Machine]]
- Reactor: [[01 - Reactor Pattern — The Machine]], [[03 - Reactor — The Machine]]
- ThreadPool: [[01 - Multithreading Patterns — The Machine]], [[06 - ThreadPool]]

---

## Traversal 2 — Memory: malloc → Cache

`new Foo()` is called. Trace from C++ operator new to the CPU reading bytes.

```
[C++ runtime]
  new Foo()
  → operator new(sizeof(Foo))
  → malloc(n)
        │
        ▼
[allocator — glibc ptmalloc2]
  check free list (bins) for a chunk of size n
  → found: return pointer immediately (nanoseconds, no syscall)
  → not found:
      → brk(new_break) OR mmap(NULL, n, MAP_ANONYMOUS)
      → kernel: extends virtual address space (VMA added to mm_struct)
      → no physical page mapped yet — just virtual range reserved
      → return virtual address
        │
        ▼
[first write to returned address]
  CPU generates virtual address → MMU translates
  → page table entry for this VA: NOT PRESENT
  → CPU raises #PF (page fault exception)
        │
        ▼
[kernel — page fault handler]
  → looks up VMA: is this address in a valid mapping? yes
  → allocates physical page from free frame pool
  → writes PTE: VA → physical page, PRESENT | WRITABLE
  → returns from exception
        │
        ▼
[CPU resumes — same instruction retried]
  MMU translates VA → PA (physical address)
  → TLB miss (first access): 4-level page table walk ~20 cycles
  → TLB loaded with this mapping
  → CPU accesses physical memory
        │
        ▼
[cache hierarchy]
  physical address → cache lookup
  → L1 miss (cold): check L2 → L3 → DRAM
  → DRAM access: ~100ns, loads 64-byte cache line
  → L1 loaded: subsequent accesses ~0.5ns
  → CPU completes the store
```

**Notes this traversal activates:**
- Allocator: [[08 - malloc and free — The Machine]], [[24 - Allocators — The Machine]]
- Virtual memory: [[03 - Virtual Memory — The Machine]], [[04 - Paging — The Machine]]
- Page fault: [[Page Fault — The Machine]], [[06 - Page Walk — The Machine]]
- TLB: [[07 - TLB — The Machine]]
- Cache: [[08 - Cache Hierarchy — The Machine]], [[09 - Cache Hierarchy — The Machine (deep)]]

---

## Traversal 3 — Startup: exec() → main()

The kernel runs your binary. Trace what happens before the first line of your code executes.

```
[kernel — exec() syscall]
  execve("/path/to/lds", argv, envp)
  → flush old address space (unmap all VMAs)
  → open ELF binary
  → read ELF header: magic bytes, arch, entry point address
  → PT_LOAD segments: map .text, .data, .bss into new address space
  → PT_INTERP: if present → load dynamic linker (ld.so) into address space
  → kernel jumps to ld.so entry point (NOT main() yet)
        │
        ▼
[dynamic linker — ld.so runs before main()]
  → reads .dynamic section: list of needed shared libraries
  → for each .so: open → mmap into address space → resolve symbols
  → process relocations: fill in GOT/PLT entries with real addresses
  → run each .so's __attribute__((constructor)) functions (plugins!)
  → run .init_array of the main binary: global C++ constructors
        │
        ▼
[C++ runtime — global constructors]
  → Singleton instances: any global Singleton<T>::GetInstance() used statically
  → global loggers, registries, factory tables initialized
  → LDS: Factory::GetInstance() created here
        │
        ▼
[main() executes]
  → program code runs with all globals initialized
```

**Notes this traversal activates:**
- ELF: [[05 - Linker — The Machine]], [[01 - Build Process — The Machine]]
- Process startup: [[Program Startup — The Machine]], [[Fork and Exec — The Machine]]
- Constructors: [[01 - RAII — The Machine]], [[01 - Singleton]]
- LDS startup: [[02 - main() Wiring Explained]]

---

## Traversal 4 — Concurrency: Thread Spawn → Work Execution

`pthread_create()` fires. A worker wakes, takes a task, executes it.

```
[parent thread]
  pthread_create(&tid, NULL, worker_fn, arg)
  → libc: clone(CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND, ...)
        │
        ▼
[kernel — clone() syscall]
  → allocate task_struct for new thread
  → copy (share) file descriptor table, address space, signal handlers
  → allocate NEW kernel stack for this thread
  → allocate NEW user-space stack (mmap, ~8MB by default)
  → add task to CFS run queue: vruntime = current min_vruntime
  → return: both threads now runnable
        │
        ▼
[scheduler]
  → CFS picks thread with lowest vruntime on each CPU core
  → context switch: save old thread's registers → load new thread's registers
  → CR3 unchanged (same process = same page tables = no TLB flush)
  → new thread starts at clone() return (or at worker_fn for new thread)
        │
        ▼
[worker thread — idle loop]
  WPQ.Pop():
    → lock mutex protecting the queue
    → queue empty: condition_variable.wait(lock)
    → pthread blocks: FUTEX_WAIT syscall, thread removed from run queue
        │
        ▼
[Reactor thread — enqueues work]
  WPQ.Push(cmd):
    → lock mutex
    → queue.push(cmd) 
    → condition_variable.notify_one()
    → FUTEX_WAKE: kernel marks one sleeping worker as TASK_RUNNING
    → unlock mutex
        │
        ▼
[worker thread — woken]
  FUTEX_WAKE returns → condition_variable.wait() returns
  → WPQ.Pop() returns cmd
  → cmd.Execute() runs application logic on this worker thread
```

**Notes this traversal activates:**
- Thread spawn: [[04 - Threads and pthreads — The Machine]], [[07 - Threading Deep Dive]]
- Scheduler: [[11 - Scheduler — The Machine]], [[10 - Context Switch — The Machine]]
- Futex: [[01 - Multithreading Patterns — The Machine]], [[02 - Memory Ordering — The Machine]]
- ThreadPool: [[04 - ThreadPool and WPQ — The Machine]], [[06 - ThreadPool]]

---

## Traversal 5 — Plugin: File Write → Self-Registration

A `.so` plugin file is dropped into the watched directory. Trace how it registers itself without any restart.

```
[filesystem]
  plugin.so written to /plugins/
  → write completes, file handle closed (fd closed by writer)
        │
        ▼
[kernel — inotify]
  inotify subsystem: IN_CLOSE_WRITE event generated
  → event written to inotify fd's read buffer
  → inotify fd becomes readable
  → if epoll is watching inotify fd: add to ready list
        │
        ▼
[Reactor — inotify fd becomes readable]
  epoll_wait() returns inotify fd
  → DirMonitor::onReadable() called
  → reads inotify event struct: {wd, mask=IN_CLOSE_WRITE, name="plugin.so"}
  → DirMonitor fires Observer notification: m_dispatcher.Notify(path)
        │
        ▼
[Observer → PNP (plugin loader)]
  PNP::OnNewPlugin(path) called
  → dlopen(path, RTLD_NOW | RTLD_DEEPBIND)
  → kernel: mmap .so ELF sections into address space
  → dynamic linker: resolve symbols
  → run __attribute__((constructor)) in .so
        │
        ▼
[plugin constructor — runs inside dlopen()]
  Singleton<Factory>::GetInstance()->Add("plugin_key", []{ return new PluginClass(); })
  → plugin is now registered in Factory
  → no restart, no manual wiring
```

**Notes this traversal activates:**
- inotify: [[06 - Inotify]], [[05 - DirMonitor]], [[07 - Why IN_CLOSE_WRITE not IN_CREATE]]
- Observer: [[05 - Observer Pattern Internals]], [[02 - Observer Pattern — The Machine]]
- Plugin loading: [[07 - PNP]], [[08 - Plugin Loading Internals]], [[05 - Plugin System — The Machine]]
- Factory: [[04 - Factory Pattern — The Machine]], [[Factory]]

---

## Where To Go Next

After reading traversals, go deep on one node:

| Want to understand | Go to |
|---|---|
| Why the Reactor doesn't block | [[03 - Reactor — The Machine]] |
| How ThreadPool priority works | [[04 - ThreadPool and WPQ — The Machine]] |
| What epoll actually does in kernel | [[04 - epoll — The Machine]] |
| How the page table walk works | [[06 - Page Walk — The Machine]] |
| Why RAII protects mid-traversal failures | [[01 - RAII — The Machine]] |
| Full LDS pipeline in one diagram | [[01 - LDS System — The Machine]] |
