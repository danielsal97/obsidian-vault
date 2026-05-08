# Learning Curriculum

Ordered by interview relevance for a C++ systems/backend role.
Each topic links to the Engineering vault file — no content here.
LDS tie-in shows which project component to think about while studying.

**Time estimates:** ~30 hrs total across all 4 tiers.

---

## Tier 1 — Must Know Cold (Week 1–2, ~12 hrs)

*These come up in almost every C++ interview. Study these first.*

### C++ Core
| # | Topic | Est. | LDS Tie-in |
|---|---|---|---|
| 1 | [[Engineering/C++/RAII\|RAII]] | 45 min | Every fd, socket, thread in LDS owns its own resource |
| 2 | [[Engineering/C++/Smart Pointers\|Smart Pointers]] | 45 min | `unique_ptr<ICommand>` moved into work queue |
| 3 | [[Engineering/C++/Move Semantics\|Move Semantics]] | 45 min | Commands moved into WPQ; fd nulled after move |
| 4 | [[Engineering/C++/Virtual Functions\|Virtual Functions]] | 45 min | `IDriverComm`, `IStorage`, `IMediator` — the whole interface layer |
| 5 | [[Engineering/C++/Templates\|Templates]] | 45 min | `Dispatcher<T>`, `CallBack<T,Sub>` — zero-cost event routing |
| 6 | [[Engineering/C++/Effective C++ - Meyers\|Effective C++ — Meyers]] | 1 hr | Cross-cuts everything above |

### Concurrency
| # | Topic | Est. | LDS Tie-in |
|---|---|---|---|
| 7 | [[Engineering/Concurrency/Multithreading Patterns\|Multithreading Patterns]] | 1 hr | ThreadPool worker loop, WPQ condition variable |
| 8 | [[Engineering/Concurrency/Memory Ordering\|Memory Ordering]] | 1 hr | Reactor shutdown flag, atomic in thread pool |
| 9 | [[Engineering/Linux/Threads - pthreads\|Threads — pthreads]] | 1 hr | pthreads under the ThreadPool abstraction |

### Linux Fundamentals
| # | Topic | Est. | LDS Tie-in |
|---|---|---|---|
| 10 | [[Engineering/Linux/Processes\|Processes]] | 45 min | Watchdog forks minion; zombie prevention |
| 11 | [[Engineering/Linux/Signals\|Signals]] | 45 min | Reactor uses `signalfd` — why not `sigaction` |
| 12 | [[Engineering/Linux/File Descriptors\|File Descriptors]] | 45 min | NBD fd, epoll fd, socket fds — all managed by Reactor |

---

## Tier 2 — Strong Understanding (Week 3–4, ~10 hrs)

*Systems role requirements. Networking is heavily LDS-relevant.*

### Networking
| # | Topic | Est. | LDS Tie-in |
|---|---|---|---|
| 13 | [[Engineering/Networking/Sockets TCP\|Sockets TCP]] | 1 hr | `TCPDriverComm` — accept, recv loop, send |
| 14 | [[Engineering/Networking/UDP Sockets\|UDP Sockets]] | 45 min | Master↔minion async protocol with MSG_ID retry |
| 15 | [[Engineering/Networking/epoll\|epoll]] | 1 hr | The Reactor's core — the whole event loop |
| 16 | [[Engineering/Networking/IPC Overview\|IPC Overview]] | 45 min | `socketpair` for NBD fd passing |
| 17 | [[Engineering/Networking/Overview\|Networking Overview]] | 1 hr | OSI bottom-up — wire to application |

### Memory
| # | Topic | Est. | LDS Tie-in |
|---|---|---|---|
| 18 | [[Engineering/Memory/Process Memory Layout\|Process Memory Layout]] | 45 min | LDS master process: text, stack per thread, heap for storage |
| 19 | [[Engineering/Memory/Stack vs Heap\|Stack vs Heap]] | 45 min | Worker threads + large I/O buffers |
| 20 | [[Engineering/Memory/Memory Errors and Tools\|Memory Errors and Tools]] | 45 min | ASan clean run — job search checklist item |

### C++ / C
| # | Topic | Est. | LDS Tie-in |
|---|---|---|---|
| 21 | [[Engineering/C++/STL Containers\|STL Containers]] | 45 min | `priority_queue` in WPQ; iterator invalidation |
| 22 | [[Engineering/C++/Inheritance\|Inheritance]] | 45 min | `ICommand` hierarchy; virtual destructor rule |
| 23 | [[Engineering/C++/Exception Handling\|Exception Handling]] | 45 min | RAII + exceptions — the interplay |
| 24 | [[Engineering/C/Memory - malloc and free\|Memory — malloc and free]] | 45 min | What's under `new`; heap internals |
| 25 | [[Engineering/C/Strings\|Strings]] | 45 min | C-string pitfalls; safe buffer handling |

---

## Tier 3 — Good Depth (Week 5–6, ~6 hrs)

*LDS is built on these patterns. You can explain them from direct experience.*

### Design Patterns (all in LDS)
| # | Topic | Est. | LDS Tie-in |
|---|---|---|---|
| 26 | [[Engineering/Design Patterns/Reactor\|Reactor]] | 1 hr | IS the Reactor — you built it |
| 27 | [[Engineering/Design Patterns/Observer\|Observer]] | 45 min | `Dispatcher<T>` / `CallBack<T>` — inotify events |
| 28 | [[Engineering/Design Patterns/Factory\|Factory]] | 45 min | `CommandFactory` — runtime command creation |
| 29 | [[Engineering/Design Patterns/Command\|Command]] | 45 min | `ICommand` + WPQ priority ordering |
| 30 | [[Engineering/Design Patterns/Strategy\|Strategy]] | 45 min | `IDriverComm` — swap NBD ↔ TCP without touching mediator |
| 31 | [[Engineering/Design Patterns/Singleton\|Singleton]] | 30 min | Thread-safe Logger via C++11 magic statics |

### Build System
| # | Topic | Est. | LDS Tie-in |
|---|---|---|---|
| 32 | [[Engineering/Build Process/1 - Preprocessor\|1 — Preprocessor]] | 30 min | Header guards in every LDS interface file |
| 33 | [[Engineering/Build Process/2 - Compiler\|2 — Compiler]] | 45 min | Template instantiation; `-O2` vs `-O0` UB exposure |
| 34 | [[Engineering/Build Process/3 - Assembler\|3 — Assembler]] | 30 min | ELF symbols; what the linker sees |
| 35 | [[Engineering/Build Process/4 - Linker\|4 — Linker]] | 45 min | `dlopen`/`dlsym` for plugin system; shared lib |

### C++ / C
| # | Topic | Est. | LDS Tie-in |
|---|---|---|---|
| 36 | [[Engineering/C++/Type Casting\|Type Casting]] | 45 min | `reinterpret_cast` in `dlsym` — know why it's safe here |
| 37 | [[Engineering/C++/Operator Overloading\|Operator Overloading]] | 30 min | Canonical forms; copy-and-swap |
| 38 | [[Engineering/C/Bitwise Operations\|Bitwise Operations]] | 45 min | Protocol field packing/unpacking in wire protocol |
| 39 | [[Engineering/C/Serialization\|Serialization]] | 1 hr | LDS wire protocol — the whole reason this matters |

---

## Tier 4 — Deep Dives (Week 7–8, ~4 hrs)

*Differentiators. Most candidates don't know these well.*

| # | Topic | Est. | LDS Tie-in |
|---|---|---|---|
| 40 | [[Engineering/Linux/mmap\|mmap]] | 45 min | Alternative to `pread`/`pwrite` for LocalStorage |
| 41 | [[Engineering/Linux/Shared Memory\|Shared Memory]] | 45 min | Why LDS uses sockets not shared mem |
| 42 | [[Engineering/Linux/Semaphores\|Semaphores]] | 45 min | Watchdog heartbeat; `sem_timedwait` |
| 43 | [[Engineering/C/Undefined Behavior\|Undefined Behavior]] | 1 hr | Data race in LDS is UB, not just wrong value |
| 44 | [[Engineering/C/Structs and Unions\|Structs and Unions]] | 30 min | `DriverData` struct; wire protocol packing |
| 45 | [[Engineering/C/File IO\|File IO]] | 30 min | `pread`/`pwrite` semantics in LocalStorage |
| 46 | [[Engineering/C/Bitwise Operations\|Bitwise Operations]] | — | *(covered in Tier 3)* |

---

## Interview Prep (Week 8)

Once all tiers are done, shift to active practice:

1. [[LDS/Engineering/Interview Guide]] — 3-min pitch + cold Q&A
2. Re-read [[LDS/System Overview]] and [[LDS/Request Lifecycle]] — can you explain end-to-end?
3. Go through [[LDS/Engineering/Known Bugs]] — pick 2–3 to describe as debugging stories
4. Practice explaining each design pattern decision: *why* Reactor, *why* Observer, *why* Strategy
