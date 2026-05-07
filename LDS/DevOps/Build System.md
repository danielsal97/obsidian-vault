# Build System

**Tool:** GNU Make (not CMake)  
**Makefile:** `Igit/projects/lds/Makefile` — single file at project root  
**Compiler:** `g++` (C++20) for all `.cpp`, `gcc` for any `.c` files

---

## Compiler Flags

```makefile
FLAGS := -Wall -Wextra -std=c++20 -pedantic-errors \
         -Idesign_patterns/*/include \
         -Iservices/*/include \
         -Iutilities/*/include \
         -Iplugins/include \
         -Iexternal/Inotify_cpp \
         -Iexternal/Inotify_cpp/inotify

DFLAGS := -g          # debug symbols
PIC_FLAG := -fPIC     # position-independent code (required for shared library)
```

**`-pedantic-errors`** — treats all warnings as errors. Code must be strictly conforming C++20.  
**`-fPIC`** — all source files compile as position-independent so they can be linked into the `.so`.  
**No `-O2/-O3`** — currently debug-only build. Release mode not set up yet.

---

## Output Structure

```
bin/          ← test binaries, app binary, plugin .so files
lib/          ← libfoo-debug.so (the shared library)
debug/        ← .o object files (intermediate, gitignored)
```

All three are **gitignored** — generated on every build.

---

## The Shared Library Pattern

All component source files (`design_patterns/*/src/*.cpp`, `services/*/src/*.cpp`, `utilities/*/src/*.cpp`, `plugins/src/*.cpp`) compile into a single shared library:

```
lib/libfoo-debug.so
```

Every test binary and the app binary then link against this `.so`:

```makefile
$(CXX) $(FLAGS) $(DFLAGS) -L$(LIB_DIR) -Wl,-rpath,$(LIB_DIR) test.cpp -o bin/test -lfoo-debug -pthread
```

**Why shared library instead of static linking?**
- Plugins (`.so` files loaded via `dlopen`) require a shared runtime
- Tests can be rebuilt quickly — only the test `.cpp` recompiles, not all components
- `LD_LIBRARY_PATH` not needed because `-Wl,-rpath,$(LIB_DIR)` bakes the library path into the binary

---

## Make Targets

| Target | What it does |
|---|---|
| `make` / `make all` | Build library + all app binaries + all test binaries + plugins |
| `make test` | Same as `all` (ensures everything compiles) |
| `make run_tests` | Build everything, then run every `bin/test_*` binary in sequence |
| `make app` | Build app binaries only (`bin/LDS`, `bin/app`) |
| `make plugins` | Build plugin `.so` files only (`bin/sample_plugin.so`) |
| `make test_nbd` | Run NBD integration tests (requires `sudo`, runs shell scripts) |
| `make clean` | Delete `debug/`, `lib/`, `bin/` entirely |

**Daily workflow:**
```bash
make run_tests          # build + run all tests
make && bin/LDS /dev/nbd0 134217728   # build + run the server
```

---

## Test Binaries (as of Phase 1)

| Binary | Source | Tests |
|---|---|---|
| `bin/test_command_demo` | `test/unit/test_command_demo.cpp` | Command pattern |
| `bin/test_singelton` | `test/unit/test_singelton.cpp` | Singleton |
| `bin/test_dir_monitor` | `test/unit/test_dir_monitor.cpp` | inotify DirMonitor |
| `bin/test_msg_broker` | `test/unit/test_msg_broker.cpp` | Observer/Dispatcher |
| `bin/test_plugin_load` | `test/unit/test_plugin_load.cpp` | Plugin loading |
| `bin/test_pnp_main` | `test/unit/test_pnp_main.cpp` | PNP orchestration |
| `bin/test_logger` | `test/unit/test_logger.cpp` | Logger |
| `bin/test_thread_pool` | `test/unit/test_thread_pool.cpp` | ThreadPool |
| `bin/test_wpq` | `test/unit/test_wpq.cpp` | Priority queue |
| `bin/test_input_mediator` | `test/unit/test_input_mediator.cpp` | InputMediator |

No test framework (no gtest/catch2) — tests use plain `assert()` and print pass/fail manually. Adding gtest is a Phase 5 task.

---

## Adding a New Component

1. Create source files in the right directory:
   ```
   services/network/include/TCPServer.hpp
   services/network/src/TCPServer.cpp
   ```

2. **Nothing else needed** — the Makefile uses `find` to automatically discover all `*/src/*.cpp` files:
   ```makefile
   SRC_CPP := $(shell find design_patterns utilities services plugins -path "*/src/*.cpp" -type f)
   ```
   The new `.cpp` is picked up automatically on the next `make`.

3. Add include paths if needed:
   ```makefile
   FLAGS := ... -Iservices/network/include
   ```

---

## Adding a New Test

1. Create `test/unit/test_mycomponent.cpp`

2. Add the binary name to `TEST_BINARIES` in the Makefile:
   ```makefile
   TEST_BINARIES := \
       ... \
       $(BIN_DIR)/test_mycomponent
   ```

3. `make run_tests` will now build and run it.

---

## External Dependencies

| Dependency | Location | How used |
|---|---|---|
| `Inotify_cpp` | `external/Inotify_cpp/` | C++ wrapper for Linux `inotify` — used by DirMonitor |
| `third_party/` | `third_party/` | Reserved, currently empty |

No package manager (`apt`, `brew`, `conan`, `vcpkg`). All dependencies are vendored in the repo.

**Linux-only syscalls used** (code will not compile/run on macOS for the server binary):
- `inotify_init`, `inotify_add_watch` — file system monitoring
- `epoll_create1`, `epoll_ctl`, `epoll_wait` — event loop
- `signalfd` — signal handling via file descriptor
- `ioctl(NBD_SET_SOCK)`, `ioctl(NBD_DO_IT)` — kernel NBD interface

The **BlockClient** (Mac side) uses only POSIX sockets — compiles and runs on macOS.

---

## Namespace

All LDS code lives in namespace `hrd41`:

```cpp
namespace hrd41 {
    class Reactor { ... };
    class InputMediator { ... };
}
```

`hrd41` is the course/organisation namespace. Every header and source file uses it. No anonymous namespaces in public headers.

---

## Gitignore Summary

Ignored (generated):
- `debug/`, `lib/`, `bin/` — build artifacts
- `*.o`, `*.so`, `*.a` — compiled objects and libraries
- `.vscode/`, `.cache/`, `compile_commands.json`, `.clangd` — IDE files
- `.DS_Store` — macOS metadata
- `Dockerfile`, `docker-compose.yml` — Docker files (tracked separately)
- `docs/`, `*.md` except `README.md` — documentation (tracked in Obsidian vault instead)

Tracked:
- All `.cpp`, `.hpp`, `.h`, `.c` source files
- `Makefile`
- `README.md`
- `external/` — vendored dependencies
