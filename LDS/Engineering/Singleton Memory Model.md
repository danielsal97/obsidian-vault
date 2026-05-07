# Singleton — Memory Model & Double-Checked Locking

This is a senior-level topic. Most developers use Singleton without understanding WHY the memory ordering is required. This explains it completely.

---

## The Problem: Why Not Just a Static Pointer?

```cpp
// NAIVE (broken on multi-core):
static T* instance = nullptr;

T* GetInstance() {
    if (instance == nullptr) {    // check 1
        instance = new T();       // create
    }
    return instance;
}
```

On a multi-core CPU, Thread A and Thread B can both pass the `null` check simultaneously, both call `new T()`, and you get two instances. One gets leaked. This is a data race — undefined behavior.

---

## Adding a Lock (Still Broken — Performance)

```cpp
T* GetInstance() {
    std::lock_guard lock(mutex);  // every call acquires the lock
    if (instance == nullptr) {
        instance = new T();
    }
    return instance;
}
```

Correct, but every call to `GetInstance()` acquires a mutex. The Singleton is called everywhere, constantly. This becomes a bottleneck.

---

## Double-Checked Locking (Correct Implementation)

```cpp
// design_patterns/singleton/include/singelton.hpp
static std::atomic<T*>    s_instance;
static std::unique_ptr<T> s_owner;
static std::mutex         s_mutex;

T* GetInstance() {
    // Fast path: if initialized, return immediately (no lock)
    T* ptr = s_instance.load(std::memory_order_acquire);

    if (!ptr) {
        // Slow path: only executed once in the program's lifetime
        std::lock_guard lock(s_mutex);

        // Check again inside lock — another thread may have initialized
        ptr = s_instance.load(std::memory_order_relaxed);

        if (!ptr) {
            s_owner = std::make_unique<T>();   // construct T
            ptr = s_owner.get();
            s_instance.store(ptr, std::memory_order_release);
        }
    }
    return ptr;
}
```

---

## Why `memory_order_acquire` on the Load?

```
Thread A (initializer):          Thread B (reader):
  new T()                          ptr = s_instance.load(ACQUIRE)
  s_instance.store(RELEASE)
```

`memory_order_release` on the **store** guarantees:
> "All memory writes done BEFORE this store (i.e., constructing T) are visible to anyone who ACQUIRES this pointer."

`memory_order_acquire` on the **load** guarantees:
> "If I see a non-null pointer (from Thread A's release store), then ALL of Thread A's writes before that store are visible to me — including the T object's fields."

**Without acquire/release:** Thread B could read a non-null pointer but see uninitialized fields of T (CPU can reorder the pointer store before the object construction).

---

## Why the Second Check Inside the Lock?

```
Timeline:
  Thread A: load(null), acquires lock
  Thread B: load(null), waits for lock
  Thread A: creates T, stores ptr, releases lock
  Thread B: acquires lock
  → Without second check: Thread B creates SECOND T, destroys first via s_owner.reset()
  → Thread A still holds the old ptr → dangling pointer
```

The second check prevents creating two instances when two threads both see null and both try to acquire the lock.

---

## Why `unique_ptr<T>` for Ownership?

```cpp
static std::unique_ptr<T> s_owner;
```

- `unique_ptr` owns the instance and destroys it at program exit
- Destruction order is defined (reverse of construction)
- No need for explicit `delete` or `std::atexit()`
- Exception-safe: if T's constructor throws, unique_ptr handles cleanup

---

## Static Initialization Order Fiasco (SIOF)

**The problem:** C++ only guarantees initialization order of static variables within the same translation unit. Across TUs (different .cpp files), order is undefined.

```cpp
// file1.cpp
static Logger logger;

// file2.cpp
static DatabaseConn db(logger);  // if db initializes before logger → crash
```

**How Singleton avoids it:**

`s_instance`, `s_mutex`, and `s_owner` are static members with **constant initialization** (atomic default-constructs to 0, mutex to unlocked, unique_ptr to nullptr). This happens before any dynamic initialization — no ordering dependency.

The actual T object is only created on the first call to `GetInstance()`, which happens during program execution (after all statics are initialized).

---

## The Caveat: Nested Singletons

If T's constructor calls another Singleton:
```cpp
class Logger {
    Logger() { Config::GetInstance()->load(); }  // nested singleton call
};
```

If `Config` hasn't been initialized yet and its construction has side effects that depend on Logger... you can get a cycle. Safe pattern: don't call GetInstance() inside a singleton constructor.

---

## Memory Ordering Visual

```
Thread A                       Thread B
---------                      ---------
T fields written (a, b, c)
store(ptr, RELEASE)  ────────► load(ptr, ACQUIRE) → sees non-null
                               reads T.a, T.b, T.c ← ALL VISIBLE
```

Without release/acquire: Thread B might read non-null ptr but see old values of a, b, c.

---

## Related Notes
- [[Singleton]]
- [[Known Bugs]]
