---
name: RAII — Resource Acquisition Is Initialization
type: cpp
---

# RAII — Resource Acquisition Is Initialization

**[Wikipedia →](https://en.wikipedia.org/wiki/Resource_acquisition_is_initialization)** | **[cppreference →](https://en.cppreference.com/w/cpp/language/raii)**

A C++ idiom: tie a resource's lifetime to a stack object. When the object is constructed, acquire the resource. When the object is destroyed (scope exits, exception fires, stack unwinds), release it automatically. The destructor is the guarantee.

## The Problem Without RAII

```cpp
// ❌ Manual resource management — fragile
void loadPlugin(const char* path) {
    void* handle = dlopen(path, RTLD_NOW);
    if (!handle) return;

    doWork(handle);    // if this throws...
    dlclose(handle);   // ...this never runs → resource leak
}
```

## The Solution With RAII

```cpp
// ✅ RAII — destructor always runs
class PluginHandle {
public:
    PluginHandle(const char* path) : handle_(dlopen(path, RTLD_NOW)) {}
    ~PluginHandle() { if (handle_) dlclose(handle_); }
private:
    void* handle_;
};

void loadPlugin(const char* path) {
    PluginHandle handle(path);    // acquired
    doWork(handle);               // if this throws...
}                                 // ~PluginHandle() runs → always released ✅
```

## RAII in LDS — Where It's Used

| Resource | RAII holder | Released when |
|----------|-------------|---------------|
| Plugin `.so` handle | `Loader` destructor | Loader goes out of scope |
| Observer registration | `CallBack` destructor | CallBack destroyed |
| Mutex lock | `std::lock_guard` | Lock guard's scope ends |
| Worker threads | `ThreadPool` destructor | ThreadPool destroyed |
| UDP socket | `MinionProxy` destructor | MinionProxy destroyed |
| `DriverData` buffer | `shared_ptr<DriverData>` | Last owner releases it |

## Why It Matters for LDS

LDS is multi-threaded. Exceptions on worker threads, plugin load failures, and network errors can all cause early returns. RAII ensures that no matter how a scope exits, every resource is cleaned up — no fd leaks, no dangling callbacks, no orphaned threads.

→ Full reasoning: [[Why RAII]]

## Related
- [[shared_ptr]] — RAII for heap-allocated objects
- [[Observer]] — CallBack uses RAII for observer registration
- [[Plugin Loading Internals]] — Loader RAII for dlopen handles
