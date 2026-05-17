# C++ Object Lifetime — The Machine

## The Model

Every C++ object has a birthplace (where it was constructed) and an end (where its destructor runs). RAII ties resource ownership to object lifetime: the resource is acquired in the constructor and released in the destructor. Because destructors run deterministically at scope exit — even during exception unwinding — resources cannot leak if RAII is used correctly.

## How It Moves — Stack Object

```cpp
{
    FileHandle fh("config.txt");    // constructor: opens file, stores fd
    fh.read(buf, 128);              // normal use
    throw std::runtime_error("!");  // exception thrown here
}
// stack unwind: fh's destructor fires automatically
// FileHandle::~FileHandle() closes the fd — no leak
```

```
Stack frame for this scope:
  → [fh object] lives at a stack address
  → constructor runs: fd = open("config.txt", ...)
  → exception thrown: stack unwinding begins
      → runtime walks the unwind table (in .eh_frame ELF section)
      → finds destructors for all objects in scope
      → calls FileHandle::~FileHandle() → close(fd)
      → continues unwinding to catch block
```

## How It Moves — unique_ptr

```cpp
auto p = std::make_unique<Foo>(args);   // Foo() constructed on heap
use(*p);
// p goes out of scope: unique_ptr<Foo>::~unique_ptr() calls delete p.get()
// Foo::~Foo() destructor runs, memory freed
```

The unique_ptr IS the RAII wrapper. Its destructor calls `delete`. The pointer itself lives on the stack; the Foo lives on the heap. When the stack frame is destroyed, the unique_ptr destructor fires, deleting the heap Foo.

## How It Moves — Move Semantics

```cpp
unique_ptr<Foo> a = make_unique<Foo>();   // a owns Foo
unique_ptr<Foo> b = std::move(a);          // transfer ownership
// a is now nullptr — moved-from
// b owns Foo
// when b goes out of scope: Foo is deleted
// when a goes out of scope: destructor on nullptr → no-op
```

Move constructor: steal the resource from the source, leave source in a valid empty state. O(1) even for large objects because the data itself is not copied — only the pointer to it.

## How It Moves — shared_ptr

```cpp
shared_ptr<Foo> a = make_shared<Foo>();   // control block: refcount=1
{
    shared_ptr<Foo> b = a;                // refcount=2
}   // b destroyed: refcount=1, Foo NOT deleted yet
// a destroyed: refcount=0, Foo::~Foo() runs, memory freed
```

Control block (refcount + weakcount) is allocated once, alongside the Foo when using `make_shared`. The control block uses atomic operations for the refcount — threadsafe, but not free (atomic increment/decrement on every copy).

## Destructor Order

- Multiple local objects: destructors run in REVERSE declaration order (last declared = first destroyed)
- Vector<T>: destructor runs on each element, last index first
- Derived class: derived destructor runs first, then base destructor automatically (if virtual)
- Global objects: destructors run after main() returns, in reverse construction order

## Links

→ [[01 - RAII]] — RAII theory and patterns
→ [[02 - Smart Pointers]] — unique_ptr, shared_ptr, weak_ptr
→ [[03 - Move Semantics]] — rvalue references, move semantics
→ [[09 - Exception Handling]] — exception safety levels, noexcept
→ [[01 - RAII — The Machine]]
→ [[02 - Smart Pointers — The Machine]]
→ [[03 - Move Semantics — The Machine]]
