# Factory Pattern

Creates objects without the caller knowing or caring about the concrete type. The factory decides which class to instantiate.

---

## Simple Factory Function

```cpp
class IStorage {
public:
    virtual void Read(DriverData* d) = 0;
    virtual void Write(DriverData* d) = 0;
    virtual ~IStorage() = default;
};

class LocalStorage : public IStorage { ... };
class RemoteStorage : public IStorage { ... };

// Factory function:
std::unique_ptr<IStorage> CreateStorage(const std::string& type) {
    if (type == "local")  return std::make_unique<LocalStorage>();
    if (type == "remote") return std::make_unique<RemoteStorage>();
    throw std::invalid_argument("unknown storage type: " + type);
}

// Caller doesn't know which concrete class it got:
auto storage = CreateStorage(config.storage_type);
storage->Write(&data);   // works regardless of which type was created
```

---

## Factory Method Pattern (virtual)

The creation logic is in a virtual method — subclasses override it to create different types:

```cpp
class StorageFactory {
public:
    virtual std::unique_ptr<IStorage> create() = 0;
    virtual ~StorageFactory() = default;
};

class LocalStorageFactory : public StorageFactory {
public:
    std::unique_ptr<IStorage> create() override {
        return std::make_unique<LocalStorage>();
    }
};

class RemoteStorageFactory : public StorageFactory {
public:
    std::unique_ptr<IStorage> create() override {
        return std::make_unique<RemoteStorage>();
    }
};

// Use:
std::unique_ptr<StorageFactory> factory = std::make_unique<LocalStorageFactory>();
auto storage = factory->create();
```

This lets you swap the factory at runtime — unit tests inject a `MockStorageFactory`.

---

## Abstract Factory (family of related objects)

Creates families of objects that belong together:

```cpp
class IDriverFactory {
public:
    virtual std::unique_ptr<IStorage> createStorage() = 0;
    virtual std::unique_ptr<IComm> createComm() = 0;
};

class LinuxDriverFactory : public IDriverFactory {
    std::unique_ptr<IStorage> createStorage() override { return make_unique<LocalStorage>(); }
    std::unique_ptr<IComm> createComm() override { return make_unique<NBDDriverComm>(); }
};

class TestDriverFactory : public IDriverFactory {
    std::unique_ptr<IStorage> createStorage() override { return make_unique<MockStorage>(); }
    std::unique_ptr<IComm> createComm() override { return make_unique<MockComm>(); }
};
```

---

## Return Type: unique_ptr

Always return `unique_ptr` from factory functions. Ownership is clear: the caller owns the created object. If shared ownership is needed, the caller can move it into a `shared_ptr`.

```cpp
std::unique_ptr<IStorage> CreateStorage(...);   // ✓ clear ownership transfer
IStorage* CreateStorage(...);                   // ✗ who deletes? memory leak risk
```

See [[../C++/02 - Smart Pointers]].

---

## Why Factories Matter

Without factory: caller must know the concrete class, include its header, and `new` it directly. Changing the implementation requires changing all callers.

With factory: caller depends only on the interface (`IStorage`). The factory is the only place that knows about `LocalStorage`. Adding a `NetworkStorage` only changes the factory — not the callers.

This is **dependency inversion** — depend on abstractions, not concrete classes.

---

## Template Factory

```cpp
template<typename T, typename... Args>
std::unique_ptr<T> make(Args&&... args) {
    return std::make_unique<T>(std::forward<Args>(args)...);
}
```

`std::make_unique` is already this pattern for a single type. Custom template factories add registration, type lookup, or construction policies on top.

---

## LDS Context

In LDS, `InputMediator` is constructed with `IStorage*` — the factory decision happens outside it, in `LDS.cpp` (or `main`):

```cpp
// LDS.cpp:
auto storage = std::make_unique<LocalStorage>(path, size);
auto mediator = std::make_unique<InputMediator>(storage.get());
```

A factory function could wrap this to allow different storage backends based on config.

---

## Related Notes

- [[Singleton]] — single instance, global access
- [[Observer]] — factory often creates observers
- [[../C++/05 - Inheritance]] — factory returns base pointer to derived object
- [[../C++/02 - Smart Pointers]] — unique_ptr for factory ownership

---

## Understanding Check

> [!question]- Why does the factory return std::unique_ptr<IStorage> rather than IStorage*, and what specific memory safety problem does this solve?
> Returning a raw IStorage* transfers ownership without any mechanism to enforce deletion. Every call site must remember to delete the returned pointer, and exceptions between the factory call and the delete will leak the object. unique_ptr encodes ownership in the type system: the destructor automatically deletes the object when it goes out of scope, and unique_ptr cannot be copied — only moved — preventing accidental double-frees. The caller can always move it into a shared_ptr if shared ownership is later needed, but the factory's contract is unambiguous: you own this, and you cannot forget to clean it up.

> [!question]- What is the difference between a simple factory function and the Factory Method pattern, and when would LDS benefit from the Factory Method approach?
> A simple factory function (CreateStorage("local")) is a free function that switches on a type string — the entire creation decision lives in one place. The Factory Method pattern adds a level of indirection: a StorageFactory base class with a virtual create() method, overridden by LocalStorageFactory and RemoteStorageFactory. The Factory Method is useful when the factory itself needs to be swappable at runtime — a test framework injects MockStorageFactory, while production uses LinuxStorageFactory. LDS would benefit from this if integration tests needed to swap the entire driver stack (storage + comm) atomically, which the Abstract Factory variant enables cleanly.

> [!question]- What goes wrong if a caller caches the raw pointer returned by CreateStorage("local") and the unique_ptr it came from is destroyed?
> unique_ptr owns the allocated object — when it is destroyed (goes out of scope), it calls delete on the managed pointer. Any raw pointer to that object becomes a dangling pointer. Subsequent accesses through the raw pointer are undefined behavior: the memory may have been reallocated for something else, producing silent data corruption, or the OS may have reclaimed the page, causing a segfault. This is exactly why the factory should return unique_ptr and callers should store and extend lifetime via the smart pointer — the ownership chain remains clear and the raw pointer (if needed) is only obtained from a live unique_ptr.

> [!question]- How does the factory pattern enforce the Dependency Inversion Principle in LDS, and what would violate it?
> Dependency Inversion says high-level modules should depend on abstractions, not concrete implementations. InputMediator depends on IStorage* — it has no #include of LocalStorage.h and no knowledge of how LocalStorage works. The factory (in LDS.cpp or main) is the single point that knows about LocalStorage and creates it. This is correct. Violation would be InputMediator directly constructing auto storage = std::make_unique<LocalStorage>(path, size) inside its constructor — now the mediator is coupled to LocalStorage, its constructor parameters, and its header, making it impossible to unit test without the real filesystem.

> [!question]- If LDS adds a new NetworkStorage backend, what changes and what does NOT change with the factory pattern in place?
> What changes: the factory function gains a new branch (if (type == "network") return make_unique<NetworkStorage>(...)), and NetworkStorage.h/cpp are added to the build. What does NOT change: InputMediator, the Reactor, the ThreadPool, any tests that use MockStorage, and any code that calls storage->Read() or storage->Write(). None of those callers need to be recompiled or modified because they depend only on IStorage. This is the key benefit — adding a new implementation extends the factory in one place without touching any consumers.
