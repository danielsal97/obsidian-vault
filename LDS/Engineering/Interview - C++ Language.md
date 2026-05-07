# Interview — C++ Language Fundamentals

Questions you will be asked about C++ itself, regardless of which project you're discussing.

---

## Memory: Stack vs Heap

**Q: What's the difference between stack and heap allocation?**

Stack: automatic, allocated on function entry, freed on return. Size limited (~8MB). No fragmentation. No explicit free needed.

Heap: manual (`new`/`malloc`). Survives function scope. Can be any size. Must be freed explicitly — or use RAII.

```cpp
void f() {
    int x = 5;                    // stack — destroyed when f() returns
    int* p = new int(5);          // heap — lives until delete
    std::vector<int> v(1000);     // v itself is on stack; its buffer is on heap
}                                 // x destroyed; p leaks; v's destructor frees buffer
```

**Where is this in LDS?**  
`LocalStorage` holds `std::vector<char> m_storage` — the vector object is on the stack (or wherever LocalStorage is allocated), but the `char` buffer it owns is on the heap and freed by vector's destructor automatically.

---

## RAII

**Q: What is RAII?**

Resource Acquisition Is Initialization. Bind a resource's lifetime to an object's lifetime. Constructor acquires, destructor releases. Works automatically — no `try/catch` needed for cleanup.

```cpp
// Without RAII
void f() {
    int fd = open("file", O_RDONLY);
    if (something_fails()) {
        close(fd);   // must not forget this
        return;
    }
    close(fd);
}

// With RAII
class FileGuard {
    int m_fd;
public:
    FileGuard(const char* path) : m_fd(open(path, O_RDONLY)) {}
    ~FileGuard() { if (m_fd >= 0) close(m_fd); }
};

void f() {
    FileGuard guard("file");
    if (something_fails()) return;  // destructor closes fd automatically
}
```

**Where is this in LDS?**  
`ICallBack` destructor calls `m_disp->UnRegister(this)` — subscribing is the acquisition, unsubscribing is automatic cleanup. `Loader` destructor calls `dlclose(handle)`. `NBDDriverComm` destructor closes the NBD fd.

---

## Smart Pointers

**Q: What is `shared_ptr`? What is `unique_ptr`? When do you use each?**

`unique_ptr` — sole ownership. Non-copyable, movable. Zero overhead vs raw pointer. Destructor calls `delete`.

`shared_ptr` — shared ownership. Reference-counted. Destructor decrements count; when count hits 0, deletes. Slightly heavier than `unique_ptr`.

Use `unique_ptr` by default. Use `shared_ptr` when ownership is genuinely shared (multiple holders, lifetime not statically determinable).

**Q: What is `weak_ptr`?**

Non-owning observer of a `shared_ptr`. Does not increment ref count. Must be upgraded to `shared_ptr` via `.lock()` before use. Returns null if the object was already deleted. Breaks reference cycles.

**Where is this in LDS?**  
`DriverData` requests are passed as `shared_ptr<DriverData>` — the driver creates it, passes to InputMediator, which passes to LocalStorage. Multiple code paths hold it; lifetime is not statically clear → `shared_ptr` is correct.

---

## Move Semantics

**Q: What is a move constructor? When is it called?**

A move constructor takes ownership of another object's resources (heap allocations, file descriptors) without copying them. The source object is left in a valid but unspecified state.

```cpp
std::vector<int> a(1000);   // allocates 1000 ints on heap
std::vector<int> b = std::move(a);  // b takes a's buffer; a is now empty
// No copy — just pointer transfer. O(1) instead of O(n).
```

Move is called automatically for temporaries, or explicitly with `std::move`. The compiler prefers move over copy when the source won't be used again.

**Q: What is the Rule of Five?**

If a class needs a custom destructor, it probably needs all five: destructor, copy constructor, copy assignment, move constructor, move assignment. Or explicitly `= delete` the ones you don't want.

**Where is this in LDS?**  
`Reactor`, `NBDDriverComm`, `InputMediator` all have `= delete` on copy constructor and copy assignment — they manage OS resources (fds, threads) that can't be copied. This prevents accidental double-close.

---

## Virtual Functions and Polymorphism

**Q: What is a virtual function? How does it work?**

A virtual function is dispatched at runtime through the vtable — a table of function pointers per class. When you call `ptr->Method()` through a base class pointer, the CPU looks up the concrete type's implementation via the vtable.

```cpp
struct Base { virtual void f() { } };
struct Derived : Base { void f() override { } };

Base* p = new Derived();
p->f();   // calls Derived::f() — runtime dispatch via vtable
```

**Q: Why does a base class need a virtual destructor?**

Without it, `delete base_ptr` calls only `~Base()`, skipping `~Derived()`. Resource leak.

```cpp
Base* p = new Derived();
delete p;   // ~Base() only if NOT virtual — leak
            // ~Derived() then ~Base() if virtual — correct
```

**Where is this in LDS?**  
`IStorage` is an abstract base class with pure virtual `Read` and `Write`. `LocalStorage` implements them. `IDriverComm` is the same for `NBDDriverComm`. `ICommand` is the abstract interface for all commands. `ICallBack<Msg>` is the observer interface.

---

## Templates

**Q: What is a template? When do you use one instead of virtual functions?**

A template is compile-time parameterization. The compiler generates a separate class/function for each type used. No runtime overhead — no vtable, no pointer indirection.

Use templates when:
- The type is known at compile time
- You need zero-overhead abstractions
- You'd otherwise need to cast `void*`

Use virtual when:
- The concrete type is chosen at runtime
- You want to store heterogeneous objects in a container

```cpp
// Template: one Dispatcher<int>, one Dispatcher<string> — separate compiled types
template<typename Msg>
class Dispatcher { std::vector<ICallBack<Msg>*> m_subs; };

// Virtual: one ICommand*, dispatch to any concrete command at runtime
class ICommand { virtual void Execute() = 0; };
```

**Where is this in LDS?**  
`Dispatcher<Msg>` and `CallBack<Msg, Sub>` are templates — the message type is fixed at compile time, zero overhead. `ICommand` is virtual — commands are created at runtime by the Factory and dispatched polymorphically by the ThreadPool. Two different tools for two different situations.

---

## const Correctness

**Q: What does `const` mean on a method?**

A `const` method promises not to modify the object's observable state. It can be called on `const` objects and `const` references.

```cpp
size_t SchedSize(const sched_ty* scheduler);   // C style: const pointer param
size_t Size() const;                            // C++ style: const this
```

**Q: What is `mutable`?**

Allows a member to be modified even inside a `const` method. Correct use: internal caching/lazy computation that doesn't change observable state. Incorrect use: working around const-correctness.

---

## Inheritance and Slicing

**Q: What is object slicing?**

Copying a derived object into a base object loses the derived data:

```cpp
Derived d;
Base b = d;   // sliced — Derived's extra fields gone
```

Always pass polymorphic objects by pointer or reference, never by value.

---

## nullptr vs NULL vs 0

`nullptr` — type-safe null pointer literal (`std::nullptr_t`). Prefers pointer overloads. Use always in C++11+.  
`NULL` — typically `0` or `((void*)0)`. Ambiguous in overload resolution.  
`0` — integer zero. Can accidentally match an `int` overload instead of a pointer one.

---

## Key C++20 Used in LDS

| Feature | Where |
|---|---|
| `std::atomic<bool>` | Reactor stop flag |
| `std::shared_mutex` | LocalStorage read/write lock (after bug #9 fix) |
| `std::function<void(int)>` | Reactor handler, callbacks |
| Lambda captures `[&]`, `[this]` | LDS.cpp wiring, CallBack |
| `std::shared_ptr<T>` | DriverData lifetime management |
| `= delete` | Preventing copy of resource-owning classes |
| `override` | Enforced override checking on virtual methods |
