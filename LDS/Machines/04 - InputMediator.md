# LDS InputMediator — The Machine

## The Model
A post office sorting clerk who speaks two languages. The Reactor hands the clerk a package (fd) and says "someone sent you something." The clerk has a lookup table pinned to the wall (`m_handlers` map) — each slot has a command type (READ, WRITE, FLUSH...) and a sealed envelope with instructions. The clerk opens the package (`ReceiveRequest()`), reads the type label, finds the matching envelope, opens it, and executes — all without knowing what's inside. The Reactor has already left. The clerk's job is to be fast: decode → look up → hand off, then immediately be ready for the next package.

## How It Moves

```
Construction — InputMediator(driver, storage):
  m_driver = driver   ← raw pointer to IDriverComm (NBD or TCP)
  m_storage = storage ← raw pointer to IStorage (LocalStorage or RAID01)
  SetupHandlers()     ← pins the lookup table on the wall

SetupHandlers() — wires one lambda per command type:
  m_handlers[READ]       = [this](data) { m_storage->Read(data);  m_driver->SendReply(data); }
  m_handlers[WRITE]      = [this](data) { m_storage->Write(data); m_driver->SendReply(data); }
  m_handlers[FLUSH]      = [this](data) { data->m_status = SUCCESS; m_driver->SendReply(data); }
  m_handlers[TRIM]       = [this](data) { data->m_status = SUCCESS; m_driver->SendReply(data); }
  m_handlers[DISCONNECT] = [this](data) { /* no-op */ }
  m_handlers[GET_SIZE]   = [this](data) { data->m_len = m_storage->GetDataSize(data->m_offset);
                                          data->m_status = SUCCESS; m_driver->SendReplay(data); }

Notify(fd):                          ← called by Reactor from main thread
  (void)fd                           ← fd ignored — single driver, no demux needed
  auto request = m_driver->ReceiveRequest()    ← blocks briefly to read the request from fd
  m_handlers.at(request->m_type)(request)      ← O(log n) map lookup, then call the lambda
  return                             ← Reactor gets control back immediately
```

**Why `(void)fd`:**
`Notify(int fd)` is the IMediator interface — it receives the fd that became readable. LDS's Reactor only watches one driver fd, so the fd is known: there's only one driver. The fd parameter is ignored — it's there for interface compliance (future multi-fd Mediators could use it to demux).

**The lambda captures `this`:**
Each lambda in `m_handlers` captures `this` by reference — safe because the lambdas live as long as `InputMediator` lives (they're stored as `m_handlers` members). The lambda accesses `m_driver` and `m_storage` through `this` at call time.

**Phase 1 vs Phase 2 in SetupHandlers:**
The WRITE lambda calls `m_storage->Write(data)` — in Phase 1 this hits `LocalStorage::Write` (in-memory). In Phase 2, swapping `LocalStorage*` for `RAID01Manager*` via `IStorage*` makes the WRITE lambda send to two Raspberry Pi minions automatically. The Mediator lambda is unchanged.

## The Blueprint

```cpp
// mediator/include/InputMediator.hpp:
class InputMediator : public IMediator {
    IDriverComm* m_driver;
    IStorage* m_storage;
    std::map<int, std::function<void(std::shared_ptr<DriverData>)>> m_handlers;
    void SetupHandlers();
public:
    explicit InputMediator(IDriverComm* driver, IStorage* storage);
    void Notify(int fd) override;
};

// mediator/src/InputMediator.cpp — Notify():
void InputMediator::Notify(int fd) {
    (void)fd;
    auto request = m_driver->ReceiveRequest();
    m_handlers.at(request->m_type)(request);
}

// SetupHandlers() — READ handler:
m_handlers[DriverData::READ] = [this](std::shared_ptr<DriverData> request) {
    m_storage->Read(request);
    m_driver->SendReply(request);
};
```

**`m_handlers.at()` vs `m_handlers[]`:**
`at()` throws `std::out_of_range` if the key doesn't exist. `[]` would insert a default-constructed `function` for unknown command types and then call it (undefined behavior — calling an empty `std::function` throws `bad_function_call`). `at()` is safer: unknown type → controlled exception.

## Where It Breaks

- **Slow handler = Reactor starvation**: `m_storage->Write(data)` takes 50ms (network to minion). Reactor is blocked in `Notify()` for 50ms — no other requests are served. Fix: push a `WriteCommand` object to the ThreadPool instead of executing inline. The current Phase 1 code executes synchronously — the ThreadPool is a separate component that Phase 2 integrates.
- **Handler throws**: An exception from `m_storage->Read()` propagates through the lambda, through `Notify()`, and out of `m_io_handler(fd)` in the Reactor's event loop. The Reactor dies. Catch in Notify or in the handler lambda.
- **`m_handlers.at()` on unknown type**: If the driver sends a command type not in the map, `at()` throws `out_of_range`. Currently there's no catch — the Reactor loop would terminate.
- **Non-owning raw pointers**: `m_driver` and `m_storage` are raw pointers — InputMediator does NOT own them. If the driver or storage is destroyed while InputMediator is live → dangling pointer. Caller (`main()`) must ensure lifetime ordering.

## In LDS

`services/mediator/include/InputMediator.hpp` + `src/InputMediator.cpp`

The bridge between the Reactor and all back-end components. Wired in `main()`:
```cpp
NBDDriverComm driver("/dev/nbd0", storageSize);
LocalStorage  storage(storageSize);
InputMediator mediator(&driver, &storage);
Reactor reactor;
reactor.SetHandler([&mediator](int fd){ mediator.Notify(fd); });
reactor.Run();
```

`InputMediator` is the only component that knows about both the driver protocol (READ/WRITE/FLUSH) and the storage interface — it's the translator. Everything else is isolated by interfaces.

## Validate

1. A FLUSH request arrives. Trace exactly which methods are called, in order, from `Notify()` to the final response reaching the kernel. Does `m_storage` get involved?
2. The `m_handlers` map is populated in `SetupHandlers()` called from the constructor. After construction, is it safe to call `Notify()` from multiple threads simultaneously? What data structure would break?
3. Replace the raw pointer `IDriverComm* m_driver` with `std::shared_ptr<IDriverComm>`. What problem does this solve? What constraint does it impose on the caller in `main()`?
