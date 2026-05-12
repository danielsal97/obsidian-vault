# Virtual Functions and Polymorphism

---

## The Problem

Without virtual functions, calling a method through a base pointer always calls the base version:

```cpp
struct Animal {
    void speak() { std::cout << "..."; }
};

struct Dog : Animal {
    void speak() { std::cout << "Woof"; }
};

Animal* a = new Dog();
a->speak();   // prints "..." — calls Animal::speak, not Dog::speak
              // the type of the pointer determines which function is called
```

With virtual functions, the actual object's type determines which function is called:

```cpp
struct Animal {
    virtual void speak() { std::cout << "..."; }
};

Animal* a = new Dog();
a->speak();   // prints "Woof" — runtime dispatch
```

---

## How the vtable Works

Every class with at least one virtual function gets a **vtable** — a table of function pointers, one per virtual function. Every instance of that class gets a hidden pointer (`vptr`) to the class's vtable.

```
Dog object in memory:
┌──────────────────┐
│ vptr ──────────────────────→ Dog vtable
│ (other fields)   │          [0] Dog::speak
└──────────────────┘          [1] Dog::~Dog
                               [2] ...

Animal* a = &dog;
a->speak();
// 1. Load vptr from object
// 2. Look up speak() in vtable (index 0)
// 3. Call Dog::speak
```

Cost: one pointer per object (8 bytes), one indirect call per virtual dispatch. Usually negligible.

---

## override and final

```cpp
struct Base {
    virtual void f(int x);
};

struct Derived : Base {
    void f(int x) override;   // compiler checks: does Base have f(int)?
                               // typo or signature change → compile error
    
    void f(float x) override; // ERROR — Base has no f(float)
};

struct Leaf final : Derived {   // no class may inherit from Leaf
    void f(int x) override final;  // no class may override this f
};
```

Always use `override`. It catches typos and signature mismatches at compile time.

---

## Pure Virtual Functions and Abstract Classes

A pure virtual function (`= 0`) has no implementation in the base class. A class with any pure virtual function is **abstract** — cannot be instantiated.

```cpp
struct IStorage {
    virtual void Read(DriverData* d) = 0;    // pure virtual
    virtual void Write(DriverData* d) = 0;   // pure virtual
    virtual ~IStorage() = default;
};

// IStorage s;   // ERROR — abstract class

struct LocalStorage : IStorage {
    void Read(DriverData* d) override { ... }
    void Write(DriverData* d) override { ... }
};

IStorage* s = new LocalStorage();   // OK — concrete class
s->Read(data);                       // virtual dispatch to LocalStorage::Read
```

Interfaces in C++ are abstract classes with only pure virtual functions.

---

## Virtual Destructor — Critical Rule

**Without virtual destructor:** deleting a derived object through a base pointer only calls the base destructor — derived's resources leak.

```cpp
struct Base {
    ~Base() { std::cout << "Base dtor\n"; }
};

struct Derived : Base {
    int* m_data = new int[100];
    ~Derived() { delete[] m_data; }
};

Base* p = new Derived();
delete p;   // calls ~Base only — m_data leaks
```

**With virtual destructor:**
```cpp
struct Base {
    virtual ~Base() = default;   // always add this to polymorphic base classes
};

delete p;   // calls ~Derived() first, then ~Base() — correct
```

**Rule:** if a class has any virtual function, give it a virtual destructor.

---

## Inheritance and Method Resolution

```
          ICommand (pure virtual Execute())
              │
    ┌─────────┼─────────┐
    │         │         │
ReadCommand WriteCommand FlushCommand
```

```cpp
ICommand* cmd = factory.Create("WRITE", data);
cmd->Execute();   // calls WriteCommand::Execute at runtime
```

The factory returns an `ICommand*`. The caller doesn't know or care which concrete type it is — it just calls `Execute()`. The vtable dispatches to the right implementation.

---

## Slicing

Copying a derived object into a base object silently loses the derived data:

```cpp
Dog dog;
Animal a = dog;   // sliced — Dog's extra data is gone
a.speak();        // calls Animal::speak (no vtable involved — value type)
```

Always use **pointers or references** for polymorphic types:
```cpp
Animal& a = dog;  // no slice — reference to Dog
a.speak();        // calls Dog::speak via vtable
```

---

## virtual vs non-virtual — When to Use Each

| | Virtual | Non-virtual |
|---|---|---|
| Dispatch | Runtime (vtable) | Compile time |
| Override | Derived class can override | Hides base version (dangerous) |
| Cost | Indirect call + potential cache miss | Direct call |
| Use when | Concrete type known only at runtime | Type known at compile time |

Use virtual when you need runtime polymorphism — heterogeneous containers, factory-created objects, plugin interfaces.

Use templates (static polymorphism) when the type is known at compile time and you want zero overhead.

---

## LDS Examples

| Interface | Concrete | Relationship |
|---|---|---|
| `IStorage` | `LocalStorage` | Factory/Reactor calls via `IStorage*` |
| `IDriverComm` | `NBDDriverComm` | InputMediator uses `IDriverComm*` |
| `ICommand` | `ReadCommand`, `WriteCommand` | ThreadPool executes via `ICommand*` |
| `ICallBack<Msg>` | `CallBack<Msg,Sub>` | Dispatcher stores `vector<ICallBack*>` |

---

## Understanding Check

> [!question]- What goes wrong if you delete a derived object through a base pointer and the base class has no virtual destructor?
> The compiler sees a `Base*` and calls `~Base()` directly — there is no virtual dispatch because the destructor is not in the vtable. `~Derived()` never runs, so any resources the derived class owns (heap buffers, file descriptors, mutexes) are never released. In LDS, if `IStorage` lacked a virtual destructor, deleting a `LocalStorage*` through an `IStorage*` would leak the internal `m_buf` vector and leave the mutex in an undefined state.

> [!question]- Why does object slicing silently break polymorphism, and how does using a reference or pointer prevent it?
> When you assign a derived object to a base *value*, the compiler copies only the base subobject — the derived fields are truncated and, critically, the `vptr` is overwritten with the base class's vtable pointer. There is no dynamic dispatch on a value type. A pointer or reference stores the address of the original derived object and its `vptr` unchanged, so vtable lookup still reaches the derived override.

> [!question]- How does the vtable dispatch work mechanically, and what is its cost compared to a direct function call?
> Each object with virtual functions carries a hidden `vptr` pointing to its class's vtable (an array of function pointers). A virtual call loads the `vptr` (one memory read), indexes into the table (one pointer-sized offset), and calls through the function pointer (one indirect branch). A direct call is a single branch to a known address. The indirect call prevents inlining and can miss the branch predictor and instruction cache, which is why tight loops over large heterogeneous polymorphic containers can be slower than template-based approaches.

> [!question]- Why does calling a virtual function inside a constructor not dispatch to the derived override, and what real bug can this cause?
> During construction of `Base`, the object's dynamic type *is* `Base` — the derived part has not been constructed yet. The `vptr` points to `Base`'s vtable. If you call a virtual `init()` inside `Base`'s constructor hoping to reach `Derived::init()`, you instead call `Base::init()`. If `Derived::init()` would have accessed derived members (not yet constructed), the call would be UB. In LDS, a base class that calls a virtual `onConnect()` from its constructor would silently run the base no-op, not the derived handler, every time.

> [!question]- In LDS the `ICommand` interface is used with a factory that creates `ReadCommand` or `WriteCommand` at runtime. Why can templates not replace this runtime polymorphism here, and when would templates be the better choice?
> The factory receives the command type as a runtime value (the NBD request type from the kernel driver). Templates resolve types at compile time — you would need one factory instantiation per command type, which is impossible when the type is not known until the program runs. Templates are the better choice in `Dispatcher<Msg>`, where the message type is fixed per subscriber at registration time: you get zero-overhead dispatch with no vtable and the compiler can inline the callback entirely.
