# Linker — The Machine

## The Model
A master electrician who enters the factory only after every station has finished. They have a complete wiring diagram for the entire building — they walk room to room filling in every blank socket with the correct wire address. They are the only person who has ever seen all rooms simultaneously.

## How It Moves

```
InputMediator.o  ─┐
LocalStorage.o   ─┤
TCPDriverComm.o  ─┤──→ [LINKER] ──→ liblds-debug.so / executable
NBDDriverComm.o  ─┤         |
reactor.o        ─┘     1. Build global symbol table
                         2. Walk every relocation entry
                         3. Patch binary: replace 0x00000000 with real address
                         4. Resolve dynamic symbols (write stubs for .so dependencies)
```

**Static vs Dynamic:**
```
Static  (-l:libfoo.a):  copies the .o slices INTO your binary. Self-contained. Larger file.
Dynamic (-lfoo):        writes a stub + path. ld.so fills addresses at process launch.
                        Multiple processes share one copy of the .so in RAM.
```

**WHY dynamic linking exists:** If 50 processes use `libstdc++`, static linking copies it 50 times into RAM. Dynamic linking maps one copy into all 50 address spaces simultaneously — shared physical pages.

## The Blueprint

- **Symbol table**: built by scanning all `.o` files. Every exported name (function, global) gets an address.
- **Relocation**: for every blank slot (`R_X86_64_PLT32`), the linker looks up the symbol name, finds its address in the symbol table, writes it into the binary at the recorded offset.
- **PLT/GOT** (dynamic): Procedure Linkage Table + Global Offset Table — indirection layer so that `ld.so` can patch addresses after the binary is mapped into memory.
- **`-Wl,-rpath`**: bakes a search path into the binary's ELF header. At runtime, `ld.so` checks this path first before `LD_LIBRARY_PATH`.

## Where It Breaks

- **`undefined reference to 'X'`**: blank slot for symbol X was never filled. The `.o` or `.a` containing X was not passed to the linker command.
- **`multiple definition of 'X'`**: two `.o` files both define the same non-static symbol. The linker refuses to choose.
- **`cannot find -lfoo`**: the `.so` or `.a` file doesn't exist in any of the `-L` search paths.
- **Runtime crash "cannot open shared object"**: the `.so` was linked but not present at the `-rpath` location when the process launched.

## In LDS

`Makefile` lines 116–118:
```makefile
$(CXX) $(FLAGS) $(DFLAGS) -shared $(OBJ_CPP) $(THIRD_PARTY_OBJ) -o $(LIB_DIR)/$(LIBRARY_NAME_DEBUG).so
```
This is the linker invocation. `-shared` = produce a `.so`. At this moment, the blank slot in `InputMediator.o` pointing to `LocalStorage::Read` gets filled with the actual virtual address of `LocalStorage::Read` inside the `.so`.

`-Wl,-rpath,$(LIB_DIR)` in the test binary link command bakes the `.so` search path into each test executable so it finds `liblds-debug.so` at runtime without environment variables.

## Validate

1. You add a new `.cpp` file to LDS but forget to add it to `SRC_CPP` in the Makefile. The file defines `NewService::process()`. What exact error message appears and at which build step?
2. LDS uses `-shared` to build a `.so`. If you changed it to build a static `.a` and linked tests against it, what would change in RAM when 3 test processes run simultaneously?
3. `IDriverComm` is a pure virtual interface. `NBDDriverComm` and `TCPDriverComm` both implement it. At link time, which one "wins"? How does the linker know which to use at runtime?

## Connections

**Theory:** [[Core/Theory/Build Process/4 - Linker]]  
**Mental Models:** [[Build Process — The Machine]], [[Assembler — The Machine]], [[Processes — The Machine]]  
**LDS Implementation:** [[LDS/DevOps/Build System]]
