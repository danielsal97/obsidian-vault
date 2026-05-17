# Exception Handling — The Machine

## The Model
An emergency ejection system. `throw` fires the ejector seat. The runtime scans upward through the call stack like an elevator going up — at each floor (stack frame), it checks: does this floor have a `catch` that fits? If yes, land here. If no, destroy everything on this floor (call destructors) and go up one more. If no floor fits, `std::terminate()` kills the process.

## How It Moves

```
LocalStorage::Read() → throws std::out_of_range
  Stack unwind begins:
  
  Frame 4: LocalStorage::Read    — no catch → ~lock_guard called (mutex released) → up
  Frame 3: InputMediator::Notify — no catch → ~unique_lock called → up
  Frame 2: Reactor::Dispatch     — catch(std::exception& e) → LAND HERE
                                    log error, continue loop
  Frame 1: main                  — never reached
```

**Stack unwinding guarantee:** EVERY local object's destructor is called during the climb — in reverse construction order. RAII relies on this guarantee. It is why `lock_guard` releases the mutex even when an exception is thrown.

**Exception safety levels:**
- **No-throw** (`noexcept`): function never throws. Move constructors should be `noexcept`.
- **Strong** (commit or rollback): if the operation fails, state is unchanged.
- **Basic**: if the operation fails, state is valid but unspecified.
- **None**: if the operation fails, state may be invalid (broken invariants). Avoid.

## The Blueprint

```cpp
// Throw:
if (offset + len > m_data.size())
    throw std::out_of_range("Read past end of storage");

// Catch by reference (not by value — avoids slicing):
try {
    storage->Read(offset, len);
} catch (const std::out_of_range& e) {
    LOG_ERROR("Out of range: " + std::string(e.what()));
} catch (const std::exception& e) {
    LOG_ERROR("Error: " + std::string(e.what()));
} catch (...) {
    LOG_ERROR("Unknown exception");
}

// noexcept — promise to the compiler:
NBDDriverComm(NBDDriverComm&& o) noexcept : m_fd(o.m_fd) { o.m_fd = -1; }
```

**`std::terminate` triggers when:**
- Exception thrown but no matching `catch` found (unhandled exception)
- Exception thrown inside a destructor during stack unwind (two simultaneous exceptions)
- `noexcept` function throws

## Where It Breaks

- **Catch by value**: `catch (std::exception e)` slices derived exception types
- **Throwing in destructor**: if a second exception is thrown while already unwinding, `std::terminate` kills the program. Destructors must be `noexcept`.
- **Performance**: exception handling adds overhead only when an exception is actually thrown. Normal execution path has near-zero cost.

## In LDS

`services/local_storage/src/LocalStorage.cpp`

`LocalStorage::Read` and `Write` validate offsets. If a client sends an out-of-bounds request, throwing `std::out_of_range` unwinds the stack safely — the `shared_lock` RAII guard releases the mutex before the exception reaches the Reactor's catch block. The Reactor can then send an error reply to the client and continue serving other requests. Without RAII + exceptions, a bounds check failure would require careful manual unlock before every return path.

## Validate

1. `LocalStorage::Read` holds a `shared_lock` and throws. Does the mutex get released? Who releases it and when?
2. A destructor in LDS throws. Simultaneously, another exception is being unwound. What happens to the LDS process?
3. The Reactor's event loop has `catch (...)`. `LocalStorage::Read` throws. `InputMediator::Notify` doesn't catch it. What is the exception's exact path through the call stack before the Reactor catches it?

## Connections

**Theory:** [[09 - Exception Handling]]  
**Mental Models:** [[RAII — The Machine]], [[Undefined Behavior — The Machine]], [[Threads and pthreads — The Machine]]  
**LDS Implementation:** [[LDS/Application/LocalStorage]] — bounds check via out_of_range  
**Runtime Machines:** [[LDS/Runtime Machines/Reactor — The Machine]]
