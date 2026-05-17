# Factory

**Location:** `design_patterns/factory/include/factory.hpp`  
**Status:** ✅ Implemented  
**Layer:** Tier 2 — Framework

---

## What It Does

A runtime object registry. You register a creator function under a key; later, any code creates objects by key without knowing the concrete type. Used primarily for the plugin system — plugins self-register at `dlopen` time.

---

## Interface

```cpp
template <typename Base, typename Key, typename Args>
class Factory {
public:
    using CreateFunc = std::function<std::shared_ptr<Base>(Args)>;

    void Add(const Key& key, CreateFunc fn);          // register creator
    std::shared_ptr<Base> Create(const Key& key, Args& args);  // make object
};
```

Factory has a **private constructor** — only accessible through:
```cpp
Singleton<Factory<Base, Key, Args>>::GetInstance()
```

This guarantees exactly one global factory per type combination.

---

## How Plugins Use It

```cpp
// In sample_plugin.cpp — runs automatically on dlopen:
__attribute__((constructor))
void init_plugin() {
    auto factory = Singleton<PluginFactory>::GetInstance();
    factory->Add("main", [](std::nullptr_t) {
        return make_shared<function<void()>>(&SamplePlugin::main);
    });
}

// Anywhere in the app:
auto fn = factory->Create("main", args);
(*fn)();
```

The factory becomes a **self-populating registry** — no app code needs to know plugin names at compile time.

---

## Internal Storage

```cpp
std::unordered_map<Key, CreateFunc> m_createTable;
```

`Create()` calls `m_createTable.at(key)(args)` — throws `std::out_of_range` if key not registered.

---

## Type Parameters in LDS

| Base | Key | Args | Used For |
|---|---|---|---|
| `function<void()>` | `string` | `nullptr_t` | Plugin commands |
| `ICommand` | `DriverData::ActionType` | `shared_ptr<DriverData>` | Read/WriteCommand (Phase 2) |

---

## Related Notes
- [[Factory]] — deep dive with diagrams
- [[Engineering/Plugin Loading Internals]] — how plugins self-register
- [[Design Patterns/Singleton]] — Factory is always a Singleton
