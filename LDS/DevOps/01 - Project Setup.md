# Project Setup & Environment

General reference for the development environment, repo layout, and how everything fits together.

---

## Repository Layout

```
Igit/                          ← top-level git repo (everything lives here)
├── c/                         ← C language exercises
│   ├── arrays/
│   ├── bitwise/
│   ├── serialization/
│   ├── strings/
│   ├── structs/
│   └── ...
│
├── cpp/                       ← C++ exercises and smaller projects
│   ├── shapes/
│   ├── smart_pointer/
│   ├── rcstring/
│   └── ...
│
├── ds/                        ← Data structures (C) — full library
│   ├── src/                   ← Implementations (sll, bst, heap, scheduler, wd, ...)
│   ├── include/               ← Headers
│   ├── test/                  ← Test files
│   ├── bin/                   ← Built test binaries
│   └── makefile
│
├── system_progamming/         ← Linux system programming exercises
│   ├── exe/                   ← Threads, semaphores, signals, ping-pong
│   ├── ipc/                   ← IPC: TCP, UDP, shared memory, named pipe, message queue
│   └── ...
│
├── projects/
│   ├── lds/                   ← ★ Main project — LDS distributed storage system
│   ├── final_project/         ← Framework + concrete C++ project
│   ├── factory/
│   ├── thread_pool/
│   ├── wpq/
│   └── singelton/
│
└── utils/                     ← Shared C utilities (logging macros, etc.)
```

**The LDS project** lives at `Igit/projects/lds/`. It has its own git repo (`.git` inside) separate from the outer `Igit` repo.

---

## Build Environment

| Item | Value |
|---|---|
| Build system | GNU Make |
| C++ compiler | `g++` |
| C++ standard | C++20 (`-std=c++20`) |
| C compiler | `gcc` (for C files like external deps) |
| C standard | `-ansi -pedantic-errors` (in `ds/`) |
| Debug flags | `-g` (debug symbols) |
| Warning level | `-Wall -Wextra -pedantic-errors` |
| Target OS | Linux (server), macOS (BlockClient only) |

→ See [[02 - Build System]] for full Makefile details.

---

## Development vs Runtime Platform

| Component | Develops on | Runs on |
|---|---|---|
| LDS master (server) | Linux | Linux (requires kernel NBD, epoll, inotify) |
| BlockClient | Mac or Linux | Mac or Linux (POSIX sockets only) |
| ds/ scheduler + watchdog | Linux | Linux |
| system_progamming/ exercises | Linux | Linux |

**Mac cannot run the server binary.** `epoll`, `signalfd`, `inotify`, and `ioctl(NBD_*)` are Linux-only. Use a Linux machine or VM for server development.

---

## The `ds/` Library — What's Built There

`Igit/ds/` is a complete C data structures and algorithms library. All implemented from scratch, reviewed by an instructor.

| Module | File | Description |
|---|---|---|
| Singly linked list | `sll.c` | Basic SLL |
| Doubly linked list | `dll.c` | DLL with tail pointer |
| Sorted list | `sorted_list.c` | Sorted DLL with iterator |
| Stack | `stack.c` | Array-based |
| Queue | `queue.c` | Circular buffer |
| Circular buffer | `cbuff.c` | Fixed-size ring buffer |
| Vector | `vector.c` | Dynamic array |
| Priority queue | `pq.c` / `heap_pq.c` | Heap-based PQ |
| Hash set | `hash_set.c` | Chained hash table |
| BST | `bst.c` | Binary search tree |
| RBST | `rbst.c` | Randomised BST |
| Binary trie | `bintrie.c` | Bit-level trie |
| UID | `uid.c` | Unique ID (pid + time + counter) |
| Task | `task.c` | Scheduler task (fn, param, interval, uid) |
| **Scheduler** | `scheduler.c` | ★ Time-ordered task runner (heap PQ-based) |
| **Watchdog** | `wd.c` | ★ Process-resurrection watchdog |
| FSA | `fsa.c` | Fixed-size allocator |
| VSA | `vsa.c` | Variable-size allocator |
| DHCP | `dhcp.c` | IP address allocator (trie-based) |
| Calc | `calc.c` | Expression evaluator (stack-based) |
| Knight tour | `knight_tour.c` | Backtracking solver |
| Recursion | `recursion.c` | Classic recursive algorithms |
| Bitmap | `bitmap.c` | Bit manipulation utilities |

The Scheduler and Watchdog from this library are already complete and can inform the LDS Phase 2/3 implementations.

→ See [[Components/Scheduler]], [[Components/Watchdog]]

---

## The `system_progamming/` Exercises

Hands-on Linux system programming work. Relevant to LDS:

| Exercise | File | Relevance to LDS |
|---|---|---|
| TCP client/server | `ipc/tcp/client.c`, `server.c` | Direct foundation for Phase 2A BlockClient/TCPServer |
| UDP client/server | `ipc/udp/client.c`, `server.c` | Foundation for Phase 2 MinionProxy |
| Broadcast | `ipc/broadcast/` | Foundation for Phase 3 AutoDiscovery |
| Shared memory | `ipc/shared_memory/` | IPC reference |
| Message queue | `ipc/message_queue/` | IPC reference |
| Threads | `exe/threads.c`, `consumer_producer*.c` | Threading patterns |
| Semaphore | `exe/semaphore.c` | Used by Watchdog |
| Signals | `exe/ping_pong.c` | Used by Watchdog (SIGUSR1/SIGUSR2) |

The TCP and UDP exercises are especially relevant — the socket setup code for Phase 2A TCPServer and BlockClient follows the same pattern.

---

## Key Conventions

**Namespace:** All LDS C++ code uses `namespace hrd41 { }`.

**Filename style:**
- C++: PascalCase (`InputMediator.cpp`, `Dispatcher.hpp`)
- C (ds/): snake_case (`scheduler.c`, `heap_pq.h`)
- Tests: `test_` prefix (`test_input_mediator.cpp`)

**Header guards:** `#ifndef __ILRD_CLASSNAME_H__` (or `_HPP_`)

**Known typo in codebase:** `singelton` (not `singleton`) — the filename is `singelton.hpp` and test is `test_singelton.cpp`. This is baked in; changing it would break all includes.

**No exceptions in C code** (`ds/`, `system_progamming/`) — error codes only. C++ code uses exceptions.

---

## Running the Server (Quick Reference)

```bash
# 1. Build
cd Igit/projects/lds
make

# 2. Load the NBD kernel module
sudo modprobe nbd

# 3. Run (requires root for ioctl)
sudo bin/LDS /dev/nbd0 134217728   # 128 MB storage

# 4. Mount (optional, for manual testing)
sudo mkfs.ext4 /dev/nbd0
sudo mount /dev/nbd0 /mnt/test
ls /mnt/test

# 5. Unmount + disconnect
sudo umount /mnt/test
sudo nbd-client -d /dev/nbd0

# 6. Run all tests (no sudo needed)
make run_tests
```

---

## Related Notes

- [[02 - Build System]] — full Makefile reference
- [[03 - Docker Setup]] — Docker environment for Linux
- [[Components/Scheduler]] — C scheduler in ds/
- [[Components/Watchdog]] — C watchdog in ds/
- [[03 - Client-Server Architecture]] — Mac client setup
