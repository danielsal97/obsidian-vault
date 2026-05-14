# Vault Architecture Status — 2026-05-14

## Structure Health

The domain-centric migration is complete and START HERE is well-structured, but the migration left critical link debt: `Tracks/01 - Learning Curriculum.md` has approximately 60 broken links and `Tracks/02 - Interview Prep Track.md` has 23+, because both still use the pre-migration `Engineering/` path prefix that no longer exists. This is the highest-priority fix in the vault — the Tracks are unreachable. Beyond that: the C++ domain is the strongest with 25 mental models covering the object model, smart pointers, move semantics, STL internals, copy elision, and allocators, but is missing its most important deepening layer per the TODO — Compiler & Machine Intuition (calling conventions, stack frames, inlining, devirtualization). Linux and Concurrency have broken Theory/Mental Model pairings: Context Switch and Scheduler have MMs but no Theory files; Atomics and False Sharing same. The Runtime Machines are solid and cross-link well; ELF/dynamic linker content is covered there even if not yet in a standalone Theory file. LDS is structurally complete with 9 broken links in Architecture/03 and ~20 orphan files not reachable from START HERE.

---

## Core Vault — What Exists

**00 - Build Process** ✅
- Theory: Preprocessor, Compiler, Assembler, Linker, Make/CMake (5 files)
- Mental Models: all 5 topics + Make/CMake = 6 The Machine notes
- Missing: Tradeoffs/, Debugging/, Interview/, Runtime Flow/

**01 - Memory** ⚠️
- Theory: Process Layout, Stack vs Heap, Virtual Memory, Paging, MMU, Page Walk, TLB, Cache Hierarchy, Memory Errors (9 files)
- Mental Models: all 9 + Cache Hierarchy deep + Allocators/Pools = 10 notes
- Broken pairing: Allocators/Pools (MM10) has no Theory counterpart in this domain (malloc/free Theory lives in 02 - C)
- Missing: Tradeoffs/, Interview/, Runtime Flow/; Theory gaps: Allocators Theory note in Memory domain, swap mechanics, OOM killer, huge pages, ptmalloc arena/tcache/per-thread cache internals

**02 - C** ✅
- Theory: Pointers, malloc/free, Strings, Structs/Unions, File IO, Bitwise, Serialization, Undefined Behavior (8 files)
- Mental Models: all 8 topics = 8 The Machine notes
- Missing: Tradeoffs/, Interview/, Debugging/

**03 - C++** ⚠️
- Theory: RAII, Smart Pointers, Move Semantics, Templates, Inheritance, Virtual Functions, Operator Overloading, STL Containers, Exception Handling, Type Casting, Effective C++ Meyers, Versions/C++11–20 + Comparison = 16 files
- Mental Models: 25 notes — MM01–16 matching Theory topics, MM17–25 machine-level deep dives (std::vector, VTables, Object Layout, Exception Unwinding, Move Semantics deep, shared_ptr, Copy Elision, Allocators, weak_ptr)
- Interview: C++ Language Q&A ✅
- Partial/shallow: perfect forwarding (reference collapsing not fully worked through), SFINAE (one paragraph, no enable_if/void_t examples, no immediate-context vs hard-error distinction), variadic templates (no pack expansion mechanics, no sizeof...), noexcept (per-context mentions only, no unified spec file), virtual inheritance/diamond (missing vbase pointer cost and most-derived construction rule), object slicing (mentioned in 3 files, never standalone), constexpr/consteval (version file mentions only, no "when is it actually compile-time" treatment)
- Missing entirely: Tradeoffs/, Debugging/, Runtime Flow/
- Missing topics: Compiler & Machine Intuition (calling conventions, stack frames, inlining decisions, devirtualization, optimization passes — TODO marks this "MOST IMPORTANT"), Constructor/Initialization (explicit, init order, static init order fiasco, aggregate/brace init, delegating ctors, lifetime extension), Compiler-Generated Behavior (Rule of 0, when dtor suppresses implicit move, hidden temporaries), CRTP/TMP/detection idiom/policy-based design/tag dispatch, NVI pattern, RTTI internals, vtable thunks for multiple inheritance, exception commit/rollback/move-and-swap/scope guards, std::unordered_map bucket layout, std::map red-black tree layout, SoA vs AoS / data-oriented design, thread-local storage internals

**04 - Linux** ⚠️
- Theory: Processes, File Descriptors, Signals, Threads/pthreads, Shared Memory, Semaphores, mmap, Kernel (8 files)
- Mental Models: Processes, File Descriptors, Signals, Threads/pthreads, Shared Memory, Semaphores, Kernel, mmap, gdb Debugging, Context Switch, Scheduler = 11 notes
- Debugging: gdb Debugging ✅
- Interview: Linux Q&A ✅
- Broken pairing: Context Switch (MM10) and Scheduler (MM11) have Mental Models but NO Theory counterparts — the only domain with orphaned MMs
- Note: ELF loading, dynamic linker, argc/argv/envp, CoW-after-fork ARE covered via Runtime Machines (Program Startup, Fork and Exec, Page Fault) — not missing from vault, only missing as canonical Theory files
- Missing: Tradeoffs/, Runtime Flow/; Theory gaps: Context Switch theory, Scheduler/CFS theory, ELF/dynamic linker standalone Theory note

**05 - Concurrency** ⚠️
- Theory: Multithreading Patterns, Memory Ordering (2 files — thin)
- Mental Models: Multithreading Patterns, Memory Ordering, False Sharing, Atomics = 4 notes
- Tradeoffs: Why ThreadPool over inline execution ✅
- Interview: Concurrency Q&A ✅
- Broken pairing: Atomics (MM04) and False Sharing (MM03) have Mental Models but NO Theory counterparts
- Missing: Runtime Flow/, Debugging/; Theory gaps: Atomics theory, False Sharing theory, lock-free basics, ABA problem, Cache Coherence standalone note, futex internals, condition variables

**06 - Networking** ✅
- Theory: Overview, Sockets TCP, UDP Sockets, epoll, IPC Overview (5 files)
- Mental Models: Networking Overview, TCP Sockets, UDP Sockets, epoll, IPC Overview = 5 notes
- Tradeoffs: Why epoll over select/poll, Why UDP vs TCP = 2 files ✅
- Interview: Networking Q&A ✅
- Missing: Debugging/, Runtime Flow/; Theory gaps: raw sockets, HTTP/protocol framing, TLS overview, DNS, zero-copy sendfile

**07 - Design Patterns** ✅
- Theory: Reactor, Observer, Singleton, Factory, Command, Strategy (6 files)
- Mental Models: all 6 = 6 The Machine notes
- Missing: Tradeoffs/, Interview/, Debugging/, Runtime Flow/

**08 - Algorithms** ❌
- Theory: Data Structures, Big-O and Complexity (2 files — skeleton only)
- Mental Models: Data Structures, Big-O and Complexity = 2 notes
- Interview: Data Structures Q&A ✅
- Missing: most algorithm topics — sorting, searching, trees, graphs, dynamic programming, heaps, hash tables deep dive, string algorithms

**09 - DevOps** ❌
- Theory: Docker (1 file)
- Mental Models: Docker = 1 note
- Missing: everything else — CI/CD, containers deep, orchestration, systemd, deployment patterns

---

## Core Vault — Missing (Priority Order)

1. **C++ constructor/initialization internals** — explicit constructors, initialization order, static init order fiasco, RVO/NRVO, delegating constructors, forwarding references — no Theory note exists; highest ROI per TODO
2. **C++ compiler-generated behavior** — Rule of 3/5/0, implicit copy/move/dtor, hidden temporaries, compiler-generated costs — no note exists
3. **C++ Tradeoffs/ folder** — pass-by-value vs const&, virtual dispatch cost vs static dispatch, move vs copy, unique_ptr vs shared_ptr, inlining tradeoffs — entirely absent
4. **Linux/04 - Linux/Theory: ELF loading + dynamic linker** — process startup sequence, argc/argv/envp, .init_array — referenced in Runtime Machines but no canonical Theory home
5. **Concurrency Theory gaps** — atomics Theory note, false sharing Theory note, futex internals, lock-free basics, condition variables, ABA problem — only 2 Theory files exist for the whole domain
6. **Memory/Interview/** — no interview Q&A for the Memory domain despite it being foundational
7. **C++ Runtime Flow/** — generated assembly, calling conventions, stack frame layout, prologue/epilogue — TODO marks this "MOST IMPORTANT deepening area"
8. **Algorithms domain deepening** — sorting (quicksort, mergesort internals), trees (BST, red-black), hash tables deep dive, graphs (BFS/DFS), dynamic programming — currently 2 skeleton files
9. **C++ SFINAE/CRTP/Concepts** — advanced template techniques have no Theory notes; Template Mental Model exists but shallow on these
10. **Linux Context Switch + Scheduler Theory files** — MM10 and MM11 have no Theory counterparts; the only broken Theory/MM pairing in the Linux domain
11. **Cache Coherence standalone note** — MESI protocol, coherence traffic, write-invalidate — concept is embedded across multiple files but no dedicated note
12. **Memory Allocators Theory note** (in 01 - Memory) — MM10 (Allocators and Memory Pools) has no Theory home in its own domain; malloc/free lives in 02 - C
13. **Linux Tradeoffs/** — fork vs thread, signalfd vs sigaction, mmap vs malloc — rationale lives only in LDS/Decisions, absent from Core
14. **C++ exception guarantees Theory** — basic/strong/no-throw, exception-safe assignment, commit/rollback, move-and-swap, scope guards — Exception Handling Theory file exists but doesn't reach this depth
15. **Memory domain gaps** — swap mechanics, OOM killer behavior, huge pages, ptmalloc arena/tcache/per-thread cache internals

---

## Critical Link Debt

These are confirmed broken links affecting navigation — fix before adding new content.

### Tracks/01 - Learning Curriculum.md — ~60 broken links (HIGHEST PRIORITY)
All links use the pre-migration `Engineering/` path prefix (e.g. `[[Engineering/Build Process/...]]`, `[[Engineering/Memory/...]]`). The `Engineering/` folder does not exist — content migrated to `Domains/`. Every single link in this file is broken. This is the largest structural debt in the vault.
- Fix: batch-replace `Engineering/Build Process/` → `Domains/00 - Build Process/`, `Engineering/Memory/` → `Domains/01 - Memory/`, etc. across all domain prefixes.

### Tracks/02 - Interview Prep Track.md — 23+ broken links
- All `[[Engineering/...]]` prefixed links (same old path issue as above)
- `LDS/Engineering/Interview Guide` → should be `LDS/Interview/01 - Interview Guide`
- `LDS/Engineering/Known Bugs` → should be `LDS/Debugging/03 - Known Bugs`
- `LDS/Manager/Job Search Plan` → should be `LDS/Roadmap/11 - Job Search Plan`
- `[[LDS/System Overview]]` → should be `LDS/Architecture/01 - System Overview`
- `[[LDS/Request Lifecycle]]` → should be `LDS/Architecture/08 - Request Lifecycle`
- `[[Strategy/Progress Tracker]]` → should be `LDS/Roadmap/03 - Progress Tracker`
- `LDS/Engineering/Interview - C++ Language`, `Interview - Concurrency`, `Interview - Linux & Networking`, `Interview - Data Structures` — these files DO NOT EXIST anywhere in the vault; need to be created or removed

### Portals/02 - Build Runtime Intuition.md — 3 broken LDS paths
Three LDS links use `../../../LDS/` depth. From `Core/Portals/`, correct depth is `../../LDS/`. The extra `../` resolves outside the vault root.

---

## Broken Links Requiring Immediate Fix

Specific dangling wikilinks confirmed by reviewer-cpp — these silently fail in Obsidian graph view.

| File | Broken link | Correct target |
|---|---|---|
| [[Domains/03 - C++/Mental Models/22 - shared_ptr — The Machine]] | `[[04 - Atomics — The Machine]]` | File does not exist yet — needs creating at `Domains/05 - Concurrency/Mental Models/04 - Atomics — The Machine` (already listed as missing) |
| [[Domains/03 - C++/Mental Models/25 - weak_ptr — The Machine]] | `[[04 - Atomics — The Machine]]` | Same — same dangling ref in second file |
| [[Domains/03 - C++/Mental Models/12 - C++11 — The Machine]] | `[[Core/Domains/03 - C++/Theory/C++11]]` | `[[Domains/03 - C++/Theory/Versions/01 - C++11]]` |
| [[Domains/03 - C++/Mental Models/13 - C++14 — The Machine]] | `[[Core/Domains/03 - C++/Theory/C++14]]` (likely) | `[[Domains/03 - C++/Theory/Versions/02 - C++14]]` |
| [[Domains/03 - C++/Mental Models/14 - C++17 — The Machine]] | `[[Core/Domains/03 - C++/Theory/C++17]]` (likely) | `[[Domains/03 - C++/Theory/Versions/03 - C++17]]` |
| [[Domains/03 - C++/Mental Models/15 - C++20 — The Machine]] | `[[Core/Domains/03 - C++/Theory/C++20]]` (likely) | `[[Domains/03 - C++/Theory/Versions/04 - C++20]]` |
| [[Domains/03 - C++/Mental Models/04 - Templates — The Machine]] | `[[Observer Pattern — The Machine]]`, `[[Factory Pattern — The Machine]]`, `[[Strategy Pattern — The Machine]]` | Bare names — may resolve if Obsidian finds unique filenames; verify in graph view. Actual files: `Domains/07 - Design Patterns/Mental Models/` |
| [[LDS/Architecture/03 - Client-Server Architecture]] | `[[Components/TCPServer]]` | `[[Linux Integration/04 - TCPServer\|TCPServer]]` |
| [[LDS/Architecture/03 - Client-Server Architecture]] | `[[Components/BlockClient]]` | `[[Linux Integration/01 - BlockClient\|BlockClient]]` |

---

## LDS Vault — What Exists

**Architecture/** — 10 files: System Overview, Three-Tier Architecture, Client-Server, Concurrency Model, App Layer, NBD Layer, RAID01 Explained, Request Lifecycle, Services, Wire Protocol Spec ✅
- Note: Architecture/03 (Client-Server) contains two broken links — `[[Components/TCPServer]]` and `[[Components/BlockClient]]`; actual files are `Linux Integration/04 - TCPServer` and `Linux Integration/01 - BlockClient`
- Architecture/09 (Services) is a pre-LDS framing doc with stale bare links; may need archiving or rewrite

**Infrastructure/** — 11 files: Singleton, Singleton Memory Model, Reactor, Reactor Component, Observer Internals, ThreadPool, Threading Deep Dive, Dispatcher, Logger, Utilities Framework, Utils Helpers ✅

**Application/** — 11 files: LocalStorage, RAID01Manager, MinionProxy, ResponseManager, Scheduler, Watchdog, Plugins, AutoDiscovery, Commands, Factory, Factory Component, InputMediator ✅

**Linux Integration/** — 8 files: BlockClient, NBDDriverComm, NBD Protocol Deep Dive, TCPServer, DirMonitor, Inotify, PNP, Plugin Loading Internals ✅

**Runtime Machines/** — 10 machines: LDS System, Request Lifecycle, Reactor, ThreadPool+WPQ, Plugin System, LocalStorage, NBDDriverComm, TCPDriverComm, RAID01Manager, InputMediator ✅
- No `[[../Core/...]]` back-links inside individual machine files — Core cross-refs exist at START HERE level only

**Decisions/** — 7 files covering all major design choices (RAII, Observer, Templates vs Virtual, UDP vs TCP, TCP for Client, signalfd, IN_CLOSE_WRITE) ✅

**UML/** — 7 diagrams: Class Diagram, NBD Handshake, Plugin Loading, Read Request, Write Request, Minion State Diagram, Phase Dependencies ✅
- UML/06 (Minion state: Discovering→Connected→Active→Degraded→Failed→Rebalancing) — relevant for Phase 3/Watchdog and interview prep; not linked
- UML/07 (Phase dependency graph + critical path) — critical for sprint planning; not linked

**Phases/** — 7 phase documents (Phase 1–6) ⚠️
- Phases/06 (Phase 5 - Integration & Testing) and Phases/07 (Phase 6 - Optimization & Polish) not linked from START HERE

**Roadmap/** — 11 files ⚠️ — only 3 of 11 linked from START HERE (Roadmap, Project Status, Phase 2A Execution Plan); 8 are orphaned

**Flows/** — 1 file: Write Request End-to-End ⚠️ (Read Request flow missing)

**Debugging/** — 4 files: Testing, Unit Tests, Known Bugs, 2026-05-01 daily log ⚠️
- Debugging/04 (2026-05-01) is a daily study log, misplaced in Debugging/; should move to Journal/ or similar

**Glossary/** — 11 LDS-specific terms ⚠️
- Glossary/01 - Key Terms.md (the index glossary) is not linked from START HERE Vocabulary section

**Interview/** — 2 files: Interview Guide, main() Wiring Explained ✅

---

## LDS Vault — Orphan / Unreachable Files

Files confirmed to exist but **not linked from `LDS/00 START HERE.md`**:

**Architecture**
- [[LDS/Architecture/05 - App Layer]] — not in START HERE Architecture section
- [[LDS/Architecture/09 - Services]] — stale pre-LDS doc; review for archiving

**UML** (high value — both should be linked)
- [[LDS/UML/06 - State Diagram - Minion]] — Minion lifecycle state machine; needed for Phase 3/Watchdog and interview prep
- [[LDS/UML/07 - Phase Dependencies]] — full build dependency graph + critical path; needed for sprint planning

**Infrastructure** (deep-dive files)
- [[LDS/Infrastructure/02 - Singleton Memory Model]]
- [[LDS/Infrastructure/04 - Reactor — Component]]
- [[LDS/Infrastructure/07 - Threading Deep Dive]]
- [[LDS/Infrastructure/08 - Dispatcher]]
- [[LDS/Infrastructure/11 - Utils Helpers]]

**Application**
- [[LDS/Application/Commands]]
- [[LDS/Application/Factory]]
- [[LDS/Application/Factory — Component]]
- [[LDS/Application/AutoDiscovery]]
- [[LDS/Application/InputMediator]] (reachable via Runtime Machines only)

**Phases**
- [[LDS/Phases/06 - Phase 5 - Integration & Testing]]
- [[LDS/Phases/07 - Phase 6 - Optimization & Polish]]

**Roadmap** (8 of 11 unlinked)
- [[LDS/Roadmap/02 - The Plan]], [[LDS/Roadmap/03 - Progress Tracker]], [[LDS/Roadmap/05 - Timeline & Milestones]], [[LDS/Roadmap/06 - Phase 2 Execution Plan]], [[LDS/Roadmap/08 - Risk Register]], [[LDS/Roadmap/09 - Test Strategy]], [[LDS/Roadmap/10 - Lessons Learned]], [[LDS/Roadmap/11 - Job Search Plan]]

**Glossary**
- [[LDS/Glossary/01 - Key Terms]] — the index; not linked from Vocabulary section
- [[LDS/Glossary/04 - EIO]], [[LDS/Glossary/07 - IoT]], [[LDS/Glossary/10 - Raspberry Pi]]

**Debugging / misplaced**
- [[LDS/Debugging/04 - 2026-05-01]] — daily study log, should be in Journal/ not Debugging/

**Broken links (confirmed)**
- `Architecture/03 - Client-Server Architecture.md` contains `[[Components/TCPServer]]` and `[[Components/BlockClient]]` — the `Components/` folder does not exist; correct paths are `Linux Integration/04 - TCPServer` and `Linux Integration/01 - BlockClient`

---

## LDS Vault — Recommended START HERE Additions

Priority order per reviewer-lds:

1. **UML section** — add `[[UML/06 - State Diagram - Minion|State Diagram: Minion]]` and `[[UML/07 - Phase Dependencies|Phase Dependencies]]`
2. **Build Phases section** — add `[[Phases/06 - Phase 5 - Integration & Testing|Phase 5]]` and `[[Phases/07 - Phase 6 - Optimization & Polish|Phase 6]]`
3. **Fix broken links** in `Architecture/03` — replace `[[Components/TCPServer]]` → `[[Linux Integration/04 - TCPServer|TCPServer]]` and `[[Components/BlockClient]]` → `[[Linux Integration/01 - BlockClient|BlockClient]]`
4. **Runtime Machines** — add `[[../Core/...]]` back-links inside individual machine files (Reactor→epoll, ThreadPool→pthreads, RAID01Manager→UDP sockets)
5. **Roadmap section** — add a sub-index or collapsible block for the 8 unlinked Roadmap files
6. **Vocabulary section** — add `[[Glossary/01 - Key Terms|Key Terms]]` as the lead entry
7. **Layer 3 — Application** — add `[[Application/Commands|Commands]]`, `[[Application/Factory|Factory]]`, `[[Application/AutoDiscovery|AutoDiscovery]]`, `[[Application/InputMediator|InputMediator]]`
8. **Layer 1 — Core Infrastructure** — add `[[Infrastructure/08 - Dispatcher|Dispatcher]]`, `[[Infrastructure/07 - Threading Deep Dive|Threading Deep Dive]]`
9. **Architecture section** — add `[[Architecture/05 - App Layer|App Layer]]`; review Architecture/09 for archiving vs rewrite
10. **Flows section** — create `LDS/Flows/02 - Read Request — End to End.md` and link it
11. **Housekeeping** — move `Debugging/04 - 2026-05-01` to a `Journal/` folder

---

## Next Actions

**Link debt — fix before adding content**

1. **Fix `Tracks/01 - Learning Curriculum.md`** (~60 broken links) — batch-replace all `Engineering/<domain>/` prefixes with the correct `Domains/00 - Build Process/`, `Domains/01 - Memory/`, etc. paths. Largest single structural debt in the vault.

2. **Fix `Tracks/02 - Interview Prep Track.md`** (23+ broken links) — correct the `Engineering/` prefixes, fix the four LDS path errors, and decide whether to create or remove the four missing interview files (`Interview - C++ Language`, `Interview - Concurrency`, `Interview - Linux & Networking`, `Interview - Data Structures`).

3. **Fix C++ Mental Models broken links** — in MM22 and MM25, update `[[04 - Atomics — The Machine]]` once that file exists; in MM12–15 fix `Theory/C++11` → `Theory/Versions/01 - C++11` etc.; verify MM04 Template bare-name links resolve in graph view.

4. **Fix `Architecture/03 - Client-Server Architecture.md`** — replace `[[Components/TCPServer]]` and `[[Components/BlockClient]]` with correct `Linux Integration/` paths.

5. **Fix `Portals/02 - Build Runtime Intuition.md`** — change `../../../LDS/` depth to `../../LDS/` in the 3 affected LDS links.

**Core vault — content gaps (highest ROI per TODO)**

6. **Write C++ Compiler & Machine Intuition notes** — `Domains/03 - C++/Runtime Flow/` covering: calling conventions (System V AMD64 ABI, register passing rdi/rsi/rdx/rcx/r8/r9, stack alignment, spill), stack frame layout (frame pointer, return address, local layout, prologue/epilogue), inlining decisions, devirtualization, optimization pass effects (-O2 vs -O3). TODO marks this "MOST IMPORTANT deepening area."

7. **Write C++ Constructor/Initialization Theory note** — `Domains/03 - C++/Theory/12 - Constructor Internals.md` covering explicit, init-list order vs declaration order, member init order bugs, static init order fiasco, aggregate/brace init, delegating ctors, lifetime extension rules. Second-highest TODO priority.

8. **Write C++ Compiler-Generated Behavior Theory note** — `Domains/03 - C++/Theory/13 - Compiler Generated Behavior.md` covering Rule of 0/3/5, when defining a destructor suppresses implicit move, hidden temporaries.

9. **Add Linux Theory files for Context Switch and Scheduler** — `Domains/04 - Linux/Theory/09 - Context Switch.md` and `10 - Scheduler.md`; these are the only MMs in the vault with no Theory counterpart.

10. **Add Concurrency Theory files for Atomics and False Sharing** — `Domains/05 - Concurrency/Theory/03 - Atomics.md` and `04 - False Sharing.md`; same broken-pairing issue. Also creates the target for the dangling MM22/MM25 link once named correctly.

11. **Create `Domains/03 - C++/Tradeoffs/`** — pass-by-value vs const&, move vs copy, unique_ptr vs shared_ptr, virtual vs static dispatch, noexcept tradeoffs. Only domain with zero Tradeoffs coverage.

12. **Add Memory domain Theory gaps** — `Domains/01 - Memory/Theory/10 - Allocators.md` (Theory home for MM10), plus notes on swap mechanics, OOM killer, huge pages, ptmalloc arena/tcache internals.

13. **Create `Domains/01 - Memory/Interview/`** — Memory Q&A covering virtual memory, TLB, cache hierarchy, page faults. High interview frequency; only foundational domain with no interview file.

14. **Write C++ SFINAE/CRTP/Advanced Templates Theory note** — `Domains/03 - C++/Theory/14 - Advanced Templates.md` covering SFINAE (immediate context vs hard error, enable_if, void_t), CRTP, TMP basics, detection idiom, policy-based design, tag dispatch, fold expressions, code bloat/instantiation explosion.

15. **Write Linux ELF/dynamic linker Theory note** — `Domains/04 - Linux/Theory/09 - ELF and Dynamic Linker.md` (or renumber around Context Switch/Scheduler). Gives Program Startup and Fork and Exec a canonical Theory home.

**LDS vault — link hygiene**

16. **Update `LDS/00 START HERE.md`** — add UML/06 and UML/07 (high-value orphans), Phases/06–07, Glossary/01 as lead Vocabulary entry, Application layer orphans (Commands, Factory, AutoDiscovery, InputMediator), Roadmap sub-index for the 8 unlinked files.

17. **Add Core back-links inside LDS Runtime Machines files** — Reactor → `[[../Core/Domains/06 - Networking/Theory/04 - epoll|epoll]]`; ThreadPool → `[[../Core/Domains/04 - Linux/Theory/04 - Threads - pthreads|pthreads]]`; RAID01Manager → `[[../Core/Domains/06 - Networking/Theory/03 - UDP Sockets|UDP sockets]]`.

18. **Create `LDS/Flows/02 - Read Request — End to End.md`** and link from START HERE Flows section.

19. **Move `LDS/Debugging/04 - 2026-05-01.md`** to a new `LDS/Journal/` folder.
