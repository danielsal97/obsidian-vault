# Make and CMake — The Machine

## The Model
CMake is the architect who draws blueprints. Make is the foreman who reads the blueprints and runs the assembly line — but only the parts that have changed since last time. The dependency graph is their shared contract.

## How It Moves

```
CMakeLists.txt
      |
      v CMake
Makefile  (or build.ninja)
      |
      v Make
[Check timestamps: is .o older than .cpp?]
      |
  YES ──→ recompile that .cpp → new .o
  NO  ──→ skip (nothing changed)
      |
      v
[Check: is executable older than any .o?]
      |
  YES ──→ relink
  NO  ──→ done
```

**WHY incremental builds:** A large project with 1000 `.cpp` files takes 10 minutes to build from scratch. Changing one file and rebuilding should take 3 seconds — only that file's `.o` and the final link step. Make tracks this via file modification timestamps.

**WHY CMake over raw Makefiles:** CMake generates correct Makefiles for any platform (Linux/Mac/Windows) and any build system (Make/Ninja). It also tracks header dependencies automatically with `-MMD -MP`.

## The Blueprint

**Makefile anatomy:**
```makefile
target: dependency1 dependency2
	recipe command   # TAB — not spaces, or Make breaks

%.o: %.cpp           # pattern rule — applies to all .cpp → .o
	$(CXX) -c $< -o $@   # $< = first dep, $@ = target
```

**CMakeLists.txt anatomy:**
```cmake
cmake_minimum_required(VERSION 3.16)
project(LDS)
set(CMAKE_CXX_STANDARD 20)

add_library(lds SHARED src/LocalStorage.cpp src/InputMediator.cpp)
target_include_directories(lds PUBLIC include/)

add_executable(test_lds test/test_input_mediator.cpp)
target_link_libraries(test_lds PRIVATE lds GTest::gtest_main)
```

**PRIVATE/PUBLIC/INTERFACE:** Controls whether include paths/flags propagate to targets that link against this one.

## Where It Breaks

- **`missing separator`**: recipe line uses spaces instead of TAB
- **Stale build**: header changed but Make doesn't know — fixed by `-MMD -MP` which auto-generates dependency rules
- **`No rule to make target`**: source file listed in Makefile doesn't exist
- **CMake cache stale**: delete `build/` and re-run `cmake` after changing `CMakeLists.txt` structure

## In LDS

`/Users/danielsa/Desktop/lds-project/Igit/projects/lds/Makefile`

- **Lines 36–38**: `find` commands build `SRC_CPP` — the complete source manifest
- **Lines 72–111**: pattern rules `.cpp → .o` — Make checks timestamps here
- **Line 116**: the shared library link rule
- **`-MMD -MP` flags** in the compile rules: these tell the compiler to emit `.d` dependency files alongside each `.o`. Make includes these `.d` files, so if `LocalStorage.hpp` changes, `LocalStorage.o` is marked stale automatically.

## Validate

1. You change one line in `LocalStorage.hpp`. Which `.o` files does Make recompile, and why?
2. The Makefile uses `$(CXX) -c $< -o $@`. What are `$<` and `$@` in the context of compiling `InputMediator.cpp`?
3. CMake `target_link_libraries(test_lds PRIVATE lds)` uses `PRIVATE`. If you changed it to `PUBLIC`, what would change for anything that links against `test_lds`?
