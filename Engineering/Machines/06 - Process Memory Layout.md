# Process Memory Layout — The Machine

## The Model
A multi-floor building where each floor has a fixed purpose. The ground floor holds the code. Higher floors hold data. Two elevators grow toward each other from opposite ends — the heap grows upward, the stack grows downward. They must never collide.

## How It Moves

```
High address  ┌─────────────────────┐
              │   Kernel space      │  ← invisible, protected — syscall elevator only
              ├─────────────────────┤
              │   Stack             │  ← grows DOWN ↓ (function calls push frames)
              │   [frame: main]     │
              │   [frame: Read]     │
              │   ...               │
              ├─ - - - - - - - - - -┤  ← stack and heap grow toward each other
              │   (unmapped gap)    │
              ├─ - - - - - - - - - -┤
              │   Heap              │  ← grows UP ↑ (malloc/new adds here)
              ├─────────────────────┤
              │   BSS               │  ← uninitialized globals (zeroed at start)
              ├─────────────────────┤
              │   Data              │  ← initialized globals and statics
              ├─────────────────────┤
              │   Text (.text)      │  ← compiled code — read-only, shared between threads
Low address   └─────────────────────┘
```

**WHY this layout:** Text is read-only and shared — multiple threads use the same code without copying it. Stack is per-function-call, automatically managed. Heap is dynamic — lives as long as you keep it alive.

**Virtual vs physical:** These addresses are virtual. The kernel maps them to physical RAM pages lazily. A 1GB heap allocation doesn't consume 1GB of physical RAM until you actually write to it.

## The Blueprint

- **Text segment**: your compiled functions. `&LocalStorage::Read` is an address here.
- **Data**: `static int counter = 5;` lives here — initialized before main() runs.
- **BSS**: `static int counter;` (no initializer) — the OS zero-fills this section at startup. Takes no space in the `.o` file.
- **Heap**: managed by `malloc`/`new`. `brk()` or `mmap()` syscall expands it.
- **Stack**: managed by the CPU. Each function call pushes a frame (local variables, return address, saved registers). `ret` pops it.
- **Stack overflow**: stack grows too deep (infinite recursion) → collides with heap → segfault.

## Where It Breaks

- **Segfault**: accessing an address in the unmapped gap (null dereference → address 0, always unmapped)
- **Stack overflow**: recursion too deep; stack collides with heap
- **Heap corruption**: writing past an allocated block tramples the allocator's metadata
- **Use-after-free**: heap block returned to allocator, then accessed — the allocator may have reused it for something else

## In LDS

`services/local_storage/src/LocalStorage.cpp`

`LocalStorage` has a `std::shared_mutex m_mutex` as a member variable. When a `LocalStorage` object is created with `new` (heap) or as a global (data/BSS), that mutex lives in the same memory region as the object. The pointer `m_data` inside `LocalStorage` points to the heap. The `Read`/`Write` method stack frames (local variables `offset`, `len`) live on the stack during the call and vanish when the function returns.

## Validate

1. A global `std::atomic<bool> g_running = true;` in LDS — which segment is it in? What initializes it?
2. `LocalStorage::Read` allocates a local `char buf[512]`. Where in the building does this buffer live, and when is it destroyed?
3. Two threads in the LDS ThreadPool call `LocalStorage::Read` simultaneously. They execute the same code (`.text`). Do they share the same stack? Explain the physical layout.
