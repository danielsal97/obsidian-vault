# Make and CMake

Two build systems. Make is the standard on Linux; CMake generates Make (or Ninja) files and is the modern C++ standard.

---

## Make

### How Make Works

Make reads a `Makefile` and builds targets. It compares timestamps: if a dependency is newer than the target, it rebuilds.

```makefile
# Rule format:
target: dependency1 dependency2
	recipe (must be TAB-indented, not spaces)
```

### Basic Makefile

```makefile
CXX      := g++
CXXFLAGS := -std=c++20 -Wall -Wextra -O2

# Final binary depends on object files
app: main.o utils.o
	$(CXX) main.o utils.o -o app

# Each .o depends on its .cpp (and implicitly its .h)
main.o: main.cpp main.h
	$(CXX) $(CXXFLAGS) -c main.cpp -o main.o

utils.o: utils.cpp utils.h
	$(CXX) $(CXXFLAGS) -c utils.cpp -o utils.o

# Phony: not a real file — always run when asked
.PHONY: clean
clean:
	rm -f *.o app
```

### Automatic Variables

```makefile
$@   — the target name
$<   — the first dependency
$^   — all dependencies
$*   — stem of the target (without extension)

# Example: compile any .cpp → .o
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@
```

### Auto-discover Source Files

```makefile
SRC := $(shell find src -name "*.cpp")
OBJ := $(SRC:.cpp=.o)           # replace .cpp with .o
DEP := $(OBJ:.o=.d)             # dependency files

app: $(OBJ)
	$(CXX) $(OBJ) -o $@

-include $(DEP)                 # auto-generated header deps

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -MMD -MP -c $< -o $@
```

`-MMD -MP` — tells the compiler to generate `.d` files tracking which headers each `.cpp` includes. Make includes these so changes to `.h` files trigger a rebuild of all affected `.cpp` files.

### Shared Library Target

```makefile
LIBFLAGS := -fPIC -shared

lib/libfoo.so: $(OBJ)
	$(CXX) $(LIBFLAGS) $(OBJ) -o $@
```

### Useful Make Flags

```bash
make -j4       # parallel build using 4 jobs
make -j$(nproc) # use all CPU cores
make -n        # dry run — print commands without running
make -B        # force rebuild everything
make VERBOSE=1 # see full compiler commands (if Makefile supports it)
```

---

## CMake

CMake generates build files (Makefile, Ninja, Visual Studio, Xcode) from a `CMakeLists.txt`. It's the standard for cross-platform C++ projects.

### Minimal CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.20)
project(MyProject VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Executable
add_executable(app src/main.cpp src/utils.cpp)

# Include directories
target_include_directories(app PRIVATE include/)

# Compiler flags
target_compile_options(app PRIVATE -Wall -Wextra -O2)
```

### Build with CMake

```bash
# Out-of-source build (standard practice):
mkdir build && cd build
cmake ..           # configure — generates Makefile or Ninja files
cmake --build .    # build
cmake --build . -j$(nproc)  # parallel

# Or:
cmake -B build     # configure (modern syntax)
cmake --build build
```

### Libraries in CMake

```cmake
# Static library:
add_library(foo STATIC src/foo.cpp)

# Shared library:
add_library(foo SHARED src/foo.cpp)

# Link to an executable:
target_link_libraries(app PRIVATE foo)
```

**PRIVATE / PUBLIC / INTERFACE:**
- `PRIVATE` — only this target uses the dependency
- `PUBLIC` — this target and anything that links against it
- `INTERFACE` — only propagated to dependents, not used by this target itself

### Find and Link External Libraries

```cmake
# Find a system library:
find_package(Threads REQUIRED)
target_link_libraries(app PRIVATE Threads::Threads)

# GTest:
find_package(GTest REQUIRED)
target_link_libraries(test_binary GTest::GTest GTest::Main)
```

### Build Types

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Debug    # -g, no optimization
cmake -B build -DCMAKE_BUILD_TYPE=Release  # -O3, NDEBUG
cmake -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo  # -O2 -g
```

### Enable Testing (CTest)

```cmake
enable_testing()

add_executable(run_tests test/test_storage.cpp)
target_link_libraries(run_tests GTest::GTest GTest::Main app_lib)

add_test(NAME StorageTests COMMAND run_tests)
```

```bash
cd build && ctest           # run all tests
ctest --output-on-failure   # show output only on failure
```

---

## Make vs CMake

| | Make | CMake |
|---|---|---|
| Config file | `Makefile` | `CMakeLists.txt` |
| Output | Binary directly | Generates Makefile/Ninja/etc |
| Cross-platform | Linux/Mac | Linux, Mac, Windows, embedded |
| Dependency tracking | Manual (`-MMD`) | Automatic |
| Finding libraries | Manual `pkg-config` | `find_package()` |
| Large projects | Gets messy | Scales well |
| Learning curve | Low | Medium |

**LDS uses Make.** If you want to modernise it, add a `CMakeLists.txt` alongside the existing `Makefile` — both can coexist.

---

## Understanding Check

> [!question]- You change a `.h` header file. Make doesn't rebuild the `.cpp` files that include it. Why, and how do you fix it?
> Make only knows what you told it. If your rule says `main.o: main.cpp`, it doesn't know about `main.h`. Fix: use `-MMD -MP` compiler flags to auto-generate `.d` dependency files, then `-include $(DEP)` in the Makefile. These `.d` files list every header each `.cpp` transitively includes — Make reads them automatically.

> [!question]- What does `make -j$(nproc)` do and why isn't it always on by default?
> `-j` runs independent build steps in parallel (one per CPU core). It's not the default because if the Makefile has incorrect dependencies (a target that should depend on another but doesn't say so), parallel builds can fail non-deterministically in ways that serial builds hide. Fix dependency declarations first, then use `-j`.

> [!question]- CMake `PRIVATE` vs `PUBLIC` on `target_link_libraries` — when does the difference matter?
> If library A links B as `PUBLIC`, then any target C that links A also gets B automatically. If `PRIVATE`, C doesn't see B. Use `PUBLIC` when B's headers are exposed in A's own headers (consumers need B to compile against A). Use `PRIVATE` when B is an internal implementation detail.

> [!question]- What is an out-of-source build in CMake and why is it the standard practice?
> Running `cmake ..` from a `build/` subdirectory puts all generated files (Makefiles, `.o` files, binaries) in `build/`, leaving the source tree clean. This makes `git status` clean, lets you have multiple build configurations (Debug, Release) in separate directories, and makes `rm -rf build/` a clean reset without touching source files.

> [!question]- The LDS Makefile builds a shared library `libfoo-debug.so`. What flag is required and why?
> `-fPIC` (Position Independent Code). Shared libraries can be loaded at any virtual address — they don't know at compile time where they'll land. `-fPIC` makes the compiler use relative addressing (GOT/PLT) instead of absolute addresses, so the code works correctly regardless of load address.
