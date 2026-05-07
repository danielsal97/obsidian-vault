# Decision: Why RAII for Resource Management

## Decision

Use **RAII (Resource Acquisition Is Initialization)** for all resources — plugin handles (`dlopen`/`dlclose`), sockets, threads, and observer registrations.

---

## The Problem Without RAII

```cpp
// BAD — manual cleanup, error-prone
Loader* loader = new Loader("plugin.so");
loader->load();

if (some_error) {
    delete loader;   // must remember
    dlclose(handle); // must remember
    return;
}

// ... more code ...

delete loader;       // must remember again
dlclose(handle);     // if exception thrown above, this never runs → LEAK
```

Every early return, every exception = potential resource leak.

---

## RAII Solution

```cpp
// GOOD — automatic cleanup guaranteed
{
    Loader loader("plugin.so");  // acquires in constructor
    loader.load();

    if (some_error) {
        return;  // Loader destructor called automatically → dlclose
    }
    // ... more code ...
}
// Loader destructor called here too → always cleaned up
```

The destructor **always** runs, even if an exception is thrown.

---

## RAII in LDS

| Resource | RAII Wrapper | On Destruction |
|---|---|---|
| Plugin `.so` handle | `Loader` | `dlclose(handle)` |
| Observer registration | `CallBack<T,Sub>` | `dispatcher.UnRegister(this)` |
| Thread | `std::thread` + RAII wrapper | `join()` |
| UDP socket | `MinionProxy` destructor | `close(sock_fd)` |
| Background threads | `Watchdog`, `AutoDiscovery` | `Stop()` + `join()` |

---

## CallBack RAII Example

```cpp
// CallBack registers in constructor, unregisters in destructor
class CallBack {
public:
    CallBack(Dispatcher* d, Sub* s, Method m)
        : dispatcher_(d) {
        dispatcher_->Register(this);  // acquire
    }
    ~CallBack() {
        dispatcher_->UnRegister(this);  // release automatically
    }
};
```

This means you can never forget to unregister an observer — it happens when the `CallBack` object goes out of scope.

---

## The C++ Rule

> **If a class manages a resource, it should release it in its destructor.**

This is the single rule that makes RAII work. C++ guarantees destructors run deterministically (unlike garbage-collected languages).

---

## Related Notes
- [[PNP]]
- [[Observer]]
