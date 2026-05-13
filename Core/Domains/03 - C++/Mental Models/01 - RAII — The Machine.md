# RAII — The Machine

## The Model
A contract between an object and the stack: when the object is constructed, it acquires a resource; when the object is destroyed (stack unwinds), it releases the resource. The stack's lifetime IS the resource's lifetime. No manual cleanup — the destructor is the cleanup.

## How It Moves

```
{                                    ← scope opens
  std::lock_guard<std::mutex> lock(m);   ← constructor: acquires mutex
  LocalStorage::Read(offset, len);
  // work happens...
  
  // exception thrown!
  // OR normal scope exit
}                                    ← scope closes: destructor called
                                       lock released automatically
                                       even if exception was thrown
```

**Without RAII:**
```cpp
m.lock();
doWork();       // throws exception
m.unlock();     // NEVER REACHED → mutex locked forever → deadlock
```

**With RAII:**
```cpp
std::lock_guard<std::mutex> lk(m);
doWork();       // throws exception
// lk destructor called during stack unwind → mutex unlocked automatically
```

**Stack unwinding:** when an exception propagates, C++ calls the destructor of every local object in reverse order of construction. RAII guarantees resources are released even in exception paths — paths you may not have thought to test.

## The Blueprint

RAII resources in LDS:
| RAII wrapper | Resource acquired | Resource released |
|---|---|---|
| `std::lock_guard` | mutex lock | mutex unlock |
| `std::unique_ptr` | heap memory (new) | heap memory (delete) |
| `std::shared_ptr` | heap memory (new) | heap memory (delete, ref count → 0) |
| `std::fstream` | file descriptor (open) | file descriptor (close) |
| `std::thread` | OS thread | join (if joined) |
| `std::jthread` | OS thread | automatic join |

**Custom RAII:**
```cpp
class FileDescriptor {
    int m_fd;
public:
    FileDescriptor(const char* path) : m_fd(open(path, O_RDONLY)) {}
    ~FileDescriptor() { if (m_fd >= 0) close(m_fd); }
    int get() const { return m_fd; }
    // Delete copy (can't duplicate fd ownership):
    FileDescriptor(const FileDescriptor&) = delete;
    FileDescriptor& operator=(const FileDescriptor&) = delete;
};
```

## Where It Breaks

- **Raw pointer return from factory**: `new T()` returned as raw pointer — caller must `delete`. Use `unique_ptr` instead.
- **Shared ownership without `shared_ptr`**: two objects both think they own the same resource → double-free.
- **RAII object in a container that gets cleared**: clearing a `vector<lock_guard>` calls destructors in order — this is correct RAII behavior, but the ordering may surprise you.

## In LDS

`services/local_storage/src/LocalStorage.cpp`

Every `Read` and `Write` uses:
```cpp
std::shared_lock<std::shared_mutex> lock(m_mutex);   // Read
// OR
std::unique_lock<std::shared_mutex> lock(m_mutex);   // Write
```

These `lock` objects are RAII. When `Read` returns — whether normally or via exception — the shared lock is released. There is no `m_mutex.unlock()` call anywhere. The destructor handles it. This is why `LocalStorage` is thread-safe without any manual unlock calls.

## Validate

1. `LocalStorage::Read` acquires a `shared_lock`. It calls a function that throws. What happens to the lock? Who releases it?
2. You have a function that opens a file, reads data, and closes it. Rewrite it so it cannot leak the file descriptor even if an exception is thrown.
3. The LDS ThreadPool destructor must join all worker threads before the pool is destroyed. Why is this a RAII responsibility, and what happens if you forget it?

## Connections

**Theory:** [[Core/Domains/03 - C++/Theory/01 - RAII]]  
**Mental Models:** [[Smart Pointers — The Machine]], [[Exception Handling — The Machine]], [[Threads and pthreads — The Machine]], [[Stack vs Heap — The Machine]]  
**LDS Implementation:** [[LDS/Decisions/Why RAII]], [[LDS/Application/LocalStorage]] — shared_mutex RAII  
**Runtime Machines:** [[LDS/Runtime Machines/ThreadPool and WPQ — The Machine]]  
**Glossary:** [[RAII]], [[shared_ptr]]
