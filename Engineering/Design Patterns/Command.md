# Command Pattern

Encapsulates a request as an object, so it can be queued, logged, undone, or passed around without the caller knowing how to execute it.

---

## Structure

```
Invoker ──── holds ────► ICommand (interface)
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
               ReadCmd   WriteCmd   FlushCmd
                    │
               executes
                    ▼
               Receiver (the actual work — LocalStorage, Socket, etc.)
```

---

## Implementation

```cpp
// Command interface:
class ICommand {
public:
    virtual void execute() = 0;
    virtual ~ICommand() = default;
};

// Concrete commands:
class ReadCommand : public ICommand {
    IStorage* m_storage;
    DriverData* m_data;
public:
    ReadCommand(IStorage* s, DriverData* d) : m_storage(s), m_data(d) {}
    void execute() override { m_storage->Read(m_data); }
};

class WriteCommand : public ICommand {
    IStorage* m_storage;
    DriverData* m_data;
public:
    WriteCommand(IStorage* s, DriverData* d) : m_storage(s), m_data(d) {}
    void execute() override { m_storage->Write(m_data); }
};

// Invoker — just calls execute():
class CommandQueue {
    std::queue<std::unique_ptr<ICommand>> m_queue;
public:
    void enqueue(std::unique_ptr<ICommand> cmd) {
        m_queue.push(std::move(cmd));
    }
    void run_all() {
        while (!m_queue.empty()) {
            m_queue.front()->execute();
            m_queue.pop();
        }
    }
};
```

---

## Lambda Shortcut (Modern C++)

Instead of a class hierarchy, use `std::function`:

```cpp
std::queue<std::function<void()>> work_queue;

work_queue.push([&storage, &data]() { storage.Read(&data); });
work_queue.push([&storage, &data]() { storage.Write(&data); });

while (!work_queue.empty()) {
    work_queue.front()();
    work_queue.pop();
}
```

This is how LDS `InputMediator` works — it creates lambdas and pushes them to `WPQ` (work item queue). The worker threads just call `fn()` — they don't know if it's a read or write.

---

## Undo / Redo

The classic use case — storing commands lets you reverse them:

```cpp
class ICommand {
public:
    virtual void execute() = 0;
    virtual void undo() = 0;
};

std::stack<std::unique_ptr<ICommand>> history;

// Execute and record:
auto cmd = std::make_unique<WriteCommand>(storage, data, old_value);
cmd->execute();
history.push(std::move(cmd));

// Undo:
history.top()->undo();
history.pop();
```

---

## Queuing and Delayed Execution

Commands decouple "who decided to do the work" from "when and where it runs":

```cpp
// Main thread creates commands and pushes to queue:
queue.push(make_unique<ReadCommand>(storage, &request_data));

// Worker thread pulls and executes:
while (true) {
    auto cmd = queue.pop();   // blocks until work available
    cmd->execute();
}
```

This is the Thread Pool / Work Queue pattern — command objects are the work items.

---

## LDS Context

In LDS, lambdas act as anonymous commands:

```cpp
// InputMediator creates the command:
auto work = [this, data]() {
    if (data->m_type == READ) m_storage->Read(data);
    else                       m_storage->Write(data);
};

// Pushes to WPQ (Work Item Queue):
m_wpq.push(std::move(work));

// Worker thread calls it:
work();
```

`ReadCommand` and `WriteCommand` as separate classes would add more structure (separate logging, metrics per command type) but the lambda approach is simpler for this case.

---

## When to Use

- **Work queues / thread pools** — commands are work items
- **Undo/redo** — store history of operations
- **Macros** — record and replay sequences of commands
- **Transactions** — group commands, execute or roll back atomically

---

## Related Notes

- [[../C++/STL Containers]] — `std::queue`, `std::function` for command queues
- [[../C++/Move Semantics]] — `std::move` when pushing unique_ptr commands
- [[Observer]] — observer often responds by issuing a command
- [[Factory]] — factory can create the right command type based on request
