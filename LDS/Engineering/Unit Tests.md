# Unit Tests (`/test/unit/`)

## Purpose

Individual unit test source files for specific components of the Local Cloud system. These files are compiled into test binaries in `/bin/`.

## Test Files

| Test File | Component | Validates | Binary |
|-----------|-----------|-----------|--------|
| `test_plugin_load.cpp` | Loader, Plugin System | Direct plugin loading | `test_plugin_load` |
| `test_pnp_main.cpp` | PNP, DirMonitor | Filesystem monitoring & loading | `test_pnp_main` |
| `test_dir_monitor.cpp` | DirMonitor | File event detection | `test_dir_monitor` |
| `test_inotify_debug.cpp` | inotify | Low-level inotify API | `test_inotify_debug` |
| `test_command_demo.cpp` | Command Pattern | Command creation & execution | `test_command_demo` |
| `test_logger.cpp` | Logger | Log output & levels | `test_logger` |
| `test_msg_broker.cpp` | MessageBroker | Message passing | `test_msg_broker` |
| `test_singelton.cpp` | Singleton | Instance uniqueness | `test_singelton` |
| `test_thread_pool.cpp` | ThreadPool | Task execution | `test_thread_pool` |
| `test_wpq.cpp` | Work Queue | Thread-safe queueing | `test_wpq` |

## Running Tests

```bash
# Run all
make test

# Run individual
./bin/test_plugin_load
./bin/test_thread_pool
./bin/test_logger
```

## Test Categories

### Phase 1: Plugin Loading Tests

- **test_plugin_load.cpp** — Single plugin: load .so, verify static constructor, verify destructor
- **test_pnp_main.cpp** — Multiple plugins with monitoring: directory watch, concurrent loading
- **test_dir_monitor.cpp** — Filesystem events: create/modify/delete, inotify detection, ordering
- **test_inotify_debug.cpp** — Low-level inotify API, Linux kernel behavior

### Framework Tests

- **test_logger.cpp** — Log levels, filtering, thread safety
- **test_thread_pool.cpp** — Enqueue tasks, parallel execution, collect results
- **test_wpq.cpp** — FIFO ordering, blocking operations, thread safety
- **test_singelton.cpp** — One instance created, global access, thread safety
- **test_msg_broker.cpp** — Send/receive messages, request/response, multiple clients
- **test_command_demo.cpp** — Create commands, execute with parameters, return results

## Adding New Tests

### Step 1: Create Test File
```cpp
// test/unit/test_new_component.cpp
#include <iostream>
#include "new_component.hpp"

int main() {
    NewComponent comp;
    assert(comp.validate());
    std::cout << "✅ All tests passed" << std::endl;
    return 0;
}
```

### Step 2: Update Makefile
```makefile
test_new_component: test/unit/test_new_component.cpp
    $(CXX) $(CFLAGS) -o bin/test_new_component \
           test/unit/test_new_component.cpp $(LIBS)
```

## Debugging

```bash
# GDB
gdb ./bin/test_plugin_load
(gdb) run
(gdb) bt    # Backtrace on crash

# Memory leaks
valgrind ./bin/test_plugin_load

# Race conditions
valgrind --tool=helgrind ./bin/test_thread_pool
```

## Phase 1 Validation Checklist

- [x] Plugin loads successfully
- [x] Plugin unloads cleanly
- [x] Multiple plugins load simultaneously
- [x] Filesystem events detected
- [x] Auto-initialization works
- [x] Error handling works
- [x] No memory leaks
- [x] Thread-safe operations

## Related Notes
- [[Testing]]
- [[Plugins]]
- [[Utilities Framework]]

---

**Location**: `test/unit/` | **Status**: ✅ Active test suite
