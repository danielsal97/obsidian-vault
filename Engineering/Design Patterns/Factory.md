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

See [[../C++/Smart Pointers]].

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
- [[../C++/Inheritance]] — factory returns base pointer to derived object
- [[../C++/Smart Pointers]] — unique_ptr for factory ownership
