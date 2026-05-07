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
