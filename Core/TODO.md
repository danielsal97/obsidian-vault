# **Tomorrow TODO — Core Vault Migration + Missing Systems/C++ Deepening**

## **Goal**

Restructure **Core only** into a domain-centric systems-engineering second brain optimized for:

- runtime intuition
- execution-flow understanding
- machine-level reasoning
- long-term learning
- AI retrieval
- deep systems intuition

The vault should be ordered by:

- foundational dependency
- runtime understanding
- progressive systems intuition

so concepts naturally build into:

- execution-flow reasoning
- debugging intuition
- compiler/runtime understanding
- long-term engineering knowledge

---

# **Final Approved Architecture**

```text
Core/
├── 00 START HERE.md
├── Glossary/
├── Tracks/
├── Portals/
├── _Archive/
└── Domains/
    ├── 00 - Build Process/
    ├── 01 - Memory/
    ├── 02 - C/
    ├── 03 - C++/
    ├── 04 - Linux/
    ├── 05 - Concurrency/
    ├── 06 - Networking/
    ├── 07 - Design Patterns/
    ├── 08 - Algorithms/
    └── 09 - DevOps/
```

Inside each domain:

```text
Theory/
Mental Models/
Runtime Flow/
Tradeoffs/
Debugging/
Interview/
```

---

# **Important Architectural Rules**

- Restructure **Core only**
- Keep:
    - START HERE
    - Tracks
    - Glossary
    - Portals
    - _Archive
- Keep `Portals/` for now and only update links.
- Do NOT put `LDS/` inside each domain.
- LDS remains its own top-level coherent project system.

---

# **Canonical Ownership Rule**

One primary note per concept.

Related domains:

- cross-link
- never duplicate full explanations

Primary domain = where the concept is first fundamentally learned in the progression.

Examples:

```text
RAII → 03 - C++
epoll → 06 - Networking
mmap → 04 - Linux
Memory Ordering → 05 - Concurrency
Virtual Memory → 01 - Memory
```

---

# **Approved Migration Decisions**

## **Build Process**

Own domain:

```text
Domains/00 - Build Process/
```

---

## **gdb Debugging**

Move to:

```text
Domains/04 - Linux/Debugging/01 - gdb Debugging
```

---

## **Linux and Networking Q&A**

Split into:

```text
Domains/04 - Linux/Interview/01 - Linux Q&A
Domains/06 - Networking/Interview/01 - Networking Q&A
```

---

# **Migration Execution Plan**

## **Phase 1 — Create Domain Structure**

Create:

- Core/Domains/
- all domain folders
- all subfolders

No files moved yet.

---

## **Phase 2 — Move Theory Files**

Move all:

- Theory/*  
    into:
- Domains/*/Theory/

Keep numbering.

---

## **Phase 3 — Move Mental Models**

Move:

- flat Mental Models/*  
    into:
- per-domain Mental Models/

Renumber from 01 within each domain.

---

## **Phase 4 — Move Tradeoffs**

Move:

- Tradeoffs/*  
    into:
- matching domain Tradeoffs/

---

## **Phase 5 — Move Interview Q&A**

Move:

- Tracks/Interview Preparation/*  
    into:
- Domains/*/Interview/

Split Linux + Networking Q&A.

Delete old Interview Preparation folder.

---

## **Phase 6 — Rewrite START HERE**

Update navigation:

- by domains
- not by old parallel folder trees

Preserve:

- learning flow
- guided entry
- ordered progression

---

## **Phase 7 — Update Tracks**

Update:

- Learning Curriculum
- Interview Prep Track

to new domain paths.

---

## **Phase 8 — Update Portals**

Keep Portals for now.  
Only update links.

---

## **Phase 9 — Update All Wiki Links**

Update:

- all path changes
- all renumbering
- all moved files

Verify:

- no broken links
- no orphan references

---

## **Phase 10 — Cleanup**

Delete empty:

- Theory/
- Mental Models/
- Tradeoffs/
- Tracks/Interview Preparation/

Commit and push.

---

# **Commit Message**

```text
restructure Core into domain-centric systems engineering brain
```

---

# **Missing / Underdeveloped Topics Remaining**

These are the next major deepening areas after migration.

---

# **C++ LANGUAGE & OBJECT MODEL**

## **Constructors / Initialization**

- explicit constructors
- implicit conversions
- conversion operators
- initialization order
- member initialization order bugs
- static initialization order fiasco
- temporary objects
- lifetime extension rules
- copy elision
- NRVO / RVO
- aggregate initialization
- brace initialization
- delegating constructors
- perfect forwarding
- forwarding references
- universal references

## **Compiler-Generated Behavior**

- implicit copy constructor
- implicit move constructor
- implicit copy assignment
- implicit move assignment
- implicit destructor
- Rule of 3
- Rule of 5
- Rule of 0
- compiler-generated hidden costs
- hidden temporaries
- object lifetime visualization

## **Object Model**

- object layout in memory
- vptr/vtable layout
- object slicing
- polymorphic object layout
- multiple inheritance layout
- virtual inheritance
- empty base optimization
- padding/alignment
- ABI implications

---

# **RESOURCE MANAGEMENT & RAII**

- deterministic destruction
- ownership models
- ownership transfer
- move-only types
- resource lifetime
- exception-safe cleanup
- custom deleters
- allocator-aware design
- resource leaks
- dangling references
- use-after-free
- double free
- cyclic references
- weak_ptr internals
- shared_ptr control block internals
- intrusive reference counting

---

# **SMART POINTERS**

## **std::unique_ptr**

- ownership transfer
- custom deleters
- array specialization
- move semantics interaction

## **std::shared_ptr**

- reference counting internals
- control block layout
- atomic reference count cost
- thread-safety semantics
- cyclic ownership problems

## **std::weak_ptr**

- cycle breaking
- expired semantics
- lock() behavior

---

# **MOVE SEMANTICS**

- move constructor internals
- move assignment internals
- moved-from states
- noexcept move semantics
- move vs copy tradeoffs
- forwarding references
- std::move vs std::forward
- perfect forwarding internals
- move elision
- copy elision

---

# **TEMPLATES & GENERIC PROGRAMMING**

## **Core Templates**

- template instantiation
- code bloat
- template specialization
- partial specialization
- variadic templates
- fold expressions
- type traits
- constexpr
- consteval
- concepts

## **Advanced Generic Programming**

- SFINAE
- CRTP
- TMP basics
- detection idiom
- policy-based design
- tag dispatching

## **Runtime Intuition**

- generated code size
- instantiation explosion
- compile-time cost
- binary-size implications

---

# **VIRTUAL FUNCTIONS & POLYMORPHISM**

- vtable generation
- vptr mechanics
- virtual dispatch cost
- dynamic dispatch internals
- pure virtual semantics
- interface vs implementation inheritance
- NVI pattern
- multiple inheritance pitfalls
- diamond inheritance
- RTTI internals
- dynamic_cast cost
- object slicing

---

# **EXCEPTION SAFETY**

- stack unwinding
- exception propagation
- noexcept
- destructor exception rules

## **Exception Guarantees**

- basic guarantee
- strong guarantee
- no-throw guarantee

## **Runtime Safety**

- RAII during unwinding
- exception-safe assignment
- commit/rollback idioms

---

# **STL / CONTAINER INTERNALS**

## **std::vector**

- growth strategy
- reallocation behavior
- iterator invalidation
- move vs copy during resize
- contiguous memory implications
- cache locality
- allocation patterns

## **std::unordered_map**

- hashing
- collisions
- rehashing
- cache behavior

## **std::map**

- tree layout
- allocation overhead
- iterator guarantees

## **Container Tradeoffs**

- locality
- allocation count
- branch prediction effects
- cache implications
- fragmentation

---

# **PERFORMANCE & OPTIMIZATION**

- hidden allocations
- temporary object costs
- branch prediction
- cache misses
- false sharing
- memory locality
- allocator overhead
- small object optimization
- copy costs
- move costs
- inlining tradeoffs
- pass-by-value vs const&
- virtual dispatch overhead
- instruction-cache effects

---

# **COMPILER & MACHINE INTUITION**

MOST IMPORTANT deepening area.

## **Compiler Behavior**

- what compiler generates
- hidden temporaries
- optimization passes
- alias analysis
- escape analysis
- devirtualization
- inlining decisions

## **Generated Assembly Understanding**

- stack frames
- calling conventions
- register passing
- object destruction flow
- function prologue/epilogue
- return-value optimization

## **Memory Visualization**

- stack growth
- heap allocations
- object layout
- reference-count updates
- allocator interaction

---

# **CONCURRENCY & MEMORY MODEL**

- atomics
- acquire/release semantics
- sequential consistency
- memory ordering
- fences
- lock-free basics
- ABA problem
- false sharing
- cache coherence
- synchronization cost

---

# **SYSTEMS-ORIENTED C++**

- allocator-aware design
- cache-friendly design
- data-oriented design
- NUMA implications
- thread-local storage
- syscall cost
- mmap allocators
- memory pools
- arena allocators
- intrusive containers

---

# **LINUX / RUNTIME EXECUTION**

- ELF loading
- dynamic linker internals
- process startup
- stack initialization
- argc/argv/envp layout
- mmap-backed allocations
- page faults during allocation
- copy-on-write after fork
- scheduler interactions

---

# **Missing Mental Model Notes**

Add:

- Object Layout — The Machine
- VTables — The Machine
- Copy Elision — The Machine
- Exception Unwinding — The Machine
- std::vector — The Machine
- shared_ptr — The Machine
- weak_ptr — The Machine
- Templates — The Machine (deeper)
- Allocators — The Machine
- Cache Locality — The Machine
- False Sharing — The Machine
- Context Switch — The Machine
- Atomics — The Machine
- Memory Ordering — The Machine
- Scheduler — The Machine

---

# **Highest ROI Next Priorities**

1. Virtual Memory deeper
2. Page Walk deeper
3. Cache Hierarchy deeper
4. malloc/free internals
5. std::vector internals
6. object layout
7. move semantics internals
8. shared_ptr internals
9. compiler-generated behavior
10. exception safety
11. atomics + memory ordering
12. synchronization internals

These topics unlock massive systems intuition.