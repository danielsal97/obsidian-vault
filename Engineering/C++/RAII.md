# RAII — Resource Acquisition Is Initialization

RAII is the most important C++ idiom. It binds a resource's lifetime to an object's lifetime. The constructor acquires the resource; the destructor releases it. No matter how the scope exits — normal return, exception, early return — the destructor always runs.

---

## The Problem Without RAII

```cpp
void f() {
    int fd = open("file.txt", O_RDONLY);
    
    if (something_fails()) {
        close(fd);   // must remember this
        return;
    }
    
    process(fd);
    
    close(fd);   // must remember this too
}
```

Every exit path must manually release the resource. Add an exception and you've leaked it. Add more resources and the cleanup logic explodes.

---

## The Solution — RAII Wrapper

```cpp
class FileGuard {
    int m_fd;
public:
    explicit FileGuard(const char* path)
        : m_fd(open(path, O_RDONLY)) {}
    
    ~FileGuard() {
        if (m_fd >= 0) close(m_fd);
    }
    
    int get() const { return m_fd; }
    
    // Non-copyable — can't have two owners closing the same fd
    FileGuard(const FileGuard&) = delete;
    FileGuard& operator=(const FileGuard&) = delete;
};

void f() {
    FileGuard guard("file.txt");   // opens on construction
    
    if (something_fails()) return;   // destructor closes fd automatically
    
    process(guard.get());
}   // destructor closes fd automatically
```

The destructor runs at scope exit regardless of how the scope exits — return, exception, fall-through. You cannot forget to release.

---

## How Destructors Are Guaranteed to Run

C++ guarantees: for every fully-constructed object, its destructor runs when it goes out of scope. This is a language guarantee, not a convention.

```cpp
void f() {
    FileGuard a("a.txt");
    FileGuard b("b.txt");
    
    throw std::runtime_error("oops");
    
    // Stack unwinding: b's destructor runs, then a's destructor runs
    // Both files are closed even though an exception was thrown
}
```

Stack unwinding — when an exception propagates, C++ destroys all local objects in reverse construction order before the exception continues up the call stack.

---

## Standard Library RAII

The entire C++ standard library is built on RAII:

| Resource | RAII wrapper |
|---|---|
| Heap memory | `std::unique_ptr`, `std::shared_ptr` |
| Mutex | `std::lock_guard`, `std::unique_lock` |
| File | `std::fstream` |
| Thread | `std::thread` (join on destruction) |
| Any container | `std::vector`, `std::string`, etc. |

```cpp
{
    std::lock_guard<std::mutex> lock(m_mutex);   // locks here
    m_data.push_back(x);
}   // unlocks here — even if push_back throws
```

---

## RAII vs try/catch

RAII is better than try/catch for cleanup because:
- You can't forget it
- It composes — multiple resources clean up automatically in reverse order
- It works for all exit paths including exceptions you didn't anticipate

```cpp
// BAD — fragile, easy to miss a path:
void f() {
    int* p = new int[100];
    try {
        risky();
        delete[] p;
    } catch (...) {
        delete[] p;
        throw;
    }
}

// GOOD — automatic, impossible to leak:
void f() {
    auto p = std::make_unique<int[]>(100);
    risky();
}   // p freed automatically
```

---

## Writing a Good RAII Class

Rules:
1. Constructor acquires the resource
2. Destructor releases it — must not throw
3. Delete copy constructor and copy assignment (or implement deep copy)
4. Optionally implement move constructor and move assignment

```cpp
class SocketGuard {
    int m_fd = -1;
public:
    explicit SocketGuard(int domain, int type)
        : m_fd(socket(domain, type, 0)) {
        if (m_fd < 0) throw std::runtime_error(strerror(errno));
    }
    
    ~SocketGuard() {
        if (m_fd >= 0) close(m_fd);
    }
    
    // Move — transfer ownership
    SocketGuard(SocketGuard&& other) noexcept : m_fd(other.m_fd) {
        other.m_fd = -1;   // source no longer owns it
    }
    
    SocketGuard& operator=(SocketGuard&& other) noexcept {
        if (this != &other) {
            if (m_fd >= 0) close(m_fd);
            m_fd = other.m_fd;
            other.m_fd = -1;
        }
        return *this;
    }
    
    SocketGuard(const SocketGuard&) = delete;
    SocketGuard& operator=(const SocketGuard&) = delete;
    
    int get() const { return m_fd; }
};
```

---

## RAII in LDS

| Resource | RAII owner | What it does |
|---|---|---|
| NBD file descriptor | `NBDDriverComm` destructor | `close(m_nbdFd)` |
| Plugin `.so` handle | `Loader` destructor | `dlclose(handle)` |
| Observer subscription | `ICallBack` destructor | `m_disp->UnRegister(this)` |
| Heap buffer | `std::vector<char>` in `LocalStorage` | freed by vector destructor |
| Mutex | `std::lock_guard` in `LocalStorage` | unlocked at scope exit |

---

## Understanding Check

> [!question]- Why must the RAII destructor never throw an exception?
> If a destructor throws while the stack is already unwinding due to another exception, `std::terminate()` is called and the program aborts. Since destructors are the cleanup mechanism, a throwing destructor means resources are left unreleased with no recovery path. Mark all destructors `noexcept` — log the error instead.

> [!question]- What goes wrong if you forget to set `other.m_fd = -1` in the move constructor of `SocketGuard`?
> Both the source (`other`) and the destination objects will hold the same file descriptor. When the source is destroyed (e.g., at end of scope after `std::move`), its destructor calls `close(m_fd)`. The destination now owns a closed (or reallocated) fd — any subsequent `read`/`write` through it is operating on the wrong file or returns errors silently. The second `close` in the destination's destructor is also a double-close.

> [!question]- Why does the `FileGuard` in LDS delete the copy constructor instead of implementing it?
> A file descriptor is an OS-level token — duplicating it requires `dup()` and both copies must be independently closed. A naive copy that shares the raw integer means whichever object destructs first closes the fd, leaving the other with a dangling descriptor. Deleting copy forces all callers to be explicit (use `std::move` or pass by reference), making ownership unambiguous at compile time.

> [!question]- RAII guarantees cleanup on exception, but what happens if the *constructor itself* throws before the resource is acquired?
> The destructor is only called for *fully constructed* objects. If the constructor throws (e.g., `socket()` fails and you throw before assigning `m_fd`), the destructor is never invoked — but that is safe because no resource was acquired. The invariant holds: the destructor runs if and only if the constructor completed, which is exactly when the resource exists.

> [!question]- In LDS the `Reactor` and `NBDDriverComm` both hold file descriptors managed by their destructors. Why is it important that these objects are non-copyable, and what real bug could arise from accidental copying?
> If `NBDDriverComm` were copied (before `= delete` on the copy constructor), both the original and the copy would store the same `m_nbdFd` integer. The first to destruct closes the NBD socket; the second's destructor then calls `close()` on the already-closed (or reallocated) file descriptor number. In a running server this could silently close an unrelated fd that the OS recycled to the same number — corrupting an active client connection or plugin handle with no compiler warning.
