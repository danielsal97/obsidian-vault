# Command Pattern — The Machine

## The Model
A frozen function call. A Command object packages the action, the target, and all parameters into a single object that can be stored, queued, transmitted, logged, or executed later. The invoker (the ThreadPool) doesn't know what the command does — only that it has an `execute()`. This lets you queue, prioritize, and parallelize work without the executor knowing anything about the work.

## How It Moves

```
Reactor receives NBD WRITE request:
  action:  write
  target:  LocalStorage
  params:  offset=4096, len=512, data=[...]

Creates Command:
  task = [&storage, offset, len, data]() {
      storage.Write(offset, data);
      driver->SendReply(SUCCESS);
  }

Pushes to WPQ (priority = WRITE):
  WPQ: [WRITE-task] [READ-task] [FLUSH-task]

ThreadPool worker pops WRITE-task:
  task()   ← executes without knowing what it is
```

**The three powers commands give you:**
1. **Decouple creation from execution**: Reactor creates commands instantly; ThreadPool executes them when a worker is free
2. **Prioritize**: WPQ orders commands by priority — WRITE before READ before FLUSH
3. **Parallelize**: commands are value objects — they can execute on any thread safely (if the command manages its own synchronization)

## The Blueprint

```cpp
// LDS command = std::function<void()> — the simplest possible command
using Task = std::function<void()>;

// Reactor creates command:
Task task = [&storage, &driver, offset, len, data = std::move(data)]() {
    try {
        storage.Write(offset, data);
        driver->SendReply(SUCCESS);
    } catch (...) {
        driver->SendReply(ERROR);
    }
};

wpq.push({PRIORITY_WRITE, std::move(task)});

// ThreadPool executes command:
auto [priority, task] = wpq.top(); wpq.pop();
task();   // has no idea what's inside — just calls it
```

**Command vs function pointer:** `std::function` captures state (offset, data, references). A raw function pointer cannot. `std::function` is the C++11 command object.

## Where It Breaks

- **Captured reference outlives command**: `[&storage]` → if `LocalStorage` is destroyed before the task executes (during shutdown), the task holds a dangling reference → UB.
- **Exception in command**: if the task throws and the ThreadPool doesn't catch it, `std::terminate` is called. Commands should handle their own exceptions.
- **Command executed twice**: if you push the same `std::function` to two queues and it captures mutable state, both executions race on that state.

## In LDS

`design_patterns/command/include/ICommand.hpp`

LDS defines `ICommand` as a pure virtual interface with `execute()`. The `std::function<void()>` pattern used in the ThreadPool is the modern equivalent — a type-erased callable that IS-A command without needing inheritance. The WPQ stores `{priority, std::function<void()>}` pairs. When the ThreadPool worker calls `task()`, it is invoking the Command's `execute()` without knowing the type.

## Validate

1. The Reactor creates a WRITE command capturing `data` by value (a 512-byte vector). It creates a READ command capturing nothing. Which command is more expensive to push to the WPQ and why?
2. LDS is shutting down. The WPQ has 10 pending commands. Should the ThreadPool execute them all before exiting, or drop them? What are the consequences of each choice?
3. You want to add a "dry run" mode: commands are logged but not executed. How does the Command pattern make this easy to add?

## Connections

**Theory:** [[Core/Domains/07 - Design Patterns/Theory/05 - Command]]  
**Mental Models:** [[Multithreading Patterns — The Machine]], [[Observer Pattern — The Machine]], [[Reactor Pattern — The Machine]]  
**LDS Implementation:** [[LDS/Infrastructure/Dispatcher]]  
**Runtime Machines:** [[LDS/Runtime Machines/Request Lifecycle — The Machine]]  
**Glossary:** [[WPQ]], [[Templates]]
