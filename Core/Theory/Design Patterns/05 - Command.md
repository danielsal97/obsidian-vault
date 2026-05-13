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

- [[../C++/08 - STL Containers]] — `std::queue`, `std::function` for command queues
- [[../C++/03 - Move Semantics]] — `std::move` when pushing unique_ptr commands
- [[Observer]] — observer often responds by issuing a command
- [[Factory]] — factory can create the right command type based on request

---

## Understanding Check

> [!question]- Why does LDS use lambda closures as commands rather than concrete ReadCommand/WriteCommand classes, and what would the class-based approach add?
> Lambda closures are more concise and require no boilerplate class hierarchy — InputMediator creates the lambda inline, captures the IStorage* and DriverData* it needs, and pushes it to WPQ in a few lines. Worker threads call fn() without caring what type of operation it is. A class-based approach would add value if commands needed: separate per-type logging or metrics (WriteCommand tracks bytes written), a cancel() method (withdrawing a queued write before it executes), or an undo() operation for transactional semantics. For LDS's current use case — dispatch to storage and signal completion — the lambda is simpler and sufficient.

> [!question]- What goes wrong if a command captures DriverData* by pointer and the originating thread destroys the DriverData before the worker thread executes the command?
> The worker thread holds a raw pointer to freed memory. When it calls storage->Read(data) or storage->Write(data), it dereferences a dangling pointer — undefined behavior. This is a classic lifetime hazard with the Command pattern when work is deferred to another thread. The fix is either to transfer ownership into the command (unique_ptr<DriverData>) so the command keeps the data alive, or to use a shared_ptr so both the submitter and the worker hold references and the data lives until the last holder is done. In LDS, DriverData is typically owned by the Reactor handler and kept alive until the completion callback fires.

> [!question]- How does the Command pattern enable undo/redo, and why is this hard to add to LDS's current lambda-based design?
> Undo requires storing enough information to reverse the operation — the pre-execution state or a compensating action. A WriteCommand class can save the old block data in its constructor and restore it in undo(). Lambda captures cannot easily support undo because lambdas have no interface: you cannot call undo() on a std::function<void()> — it only has operator()(). To add undo, you'd need to change from std::function<void()> to a command class with both execute() and undo() methods, or store two lambdas (do/undo) together in a struct. The class hierarchy is the more extensible design for this use case.

> [!question]- What is the difference between the Command pattern and the Strategy pattern, and could you replace one with the other in LDS?
> Strategy encapsulates how a persistent, repeated operation is performed — the algorithm is swapped but the same "slot" is called many times (e.g., which storage backend to use). Command encapsulates a specific, one-time request — it's created, executed once, and discarded (or stored for undo). In LDS, IStorage is a Strategy (injected once, used for all operations), while each lambda pushed to WPQ is a Command (created per request, executed once). You could not replace the Command with a Strategy here because each request has unique parameters (offset, length, data buffer) that are captured in the closure. A Strategy has no per-call state beyond the algorithm itself.

> [!question]- If the WPQ (work item queue) is full and the producer thread blocks trying to push a new Command, what is the risk for the Reactor loop?
> The Reactor loop runs on a single thread. If the InputMediator's push to WPQ blocks inside the Reactor's event handler, the entire epoll_wait loop stalls — no new NBD requests are read, no TCP client data is processed, and no signals are handled. The NBD kernel buffer fills up, back-pressuring the filesystem, and the system appears frozen. The fix is either a non-blocking push that returns an error (which the Reactor handles gracefully) or sizing the WPQ large enough that it never blocks under normal load. A separate thread for I/O submission that buffers independently from the Reactor is the more robust architecture.
