# Smart Pointers — The Machine

## The Model
Three robots, each holding a balloon (heap object). `unique_ptr`: one robot, one balloon — when the robot dies, the balloon pops. `shared_ptr`: multiple robots share one balloon — the last robot to die pops it (atomic reference counter). `weak_ptr`: a robot with binoculars — it can see the balloon but cannot keep it alive; it checks before touching.

## How It Moves

```
unique_ptr<T>:
  robot A holds balloon
  A goes out of scope → balloon destroyed
  A moves to B: A drops balloon, B picks it up → still one balloon

shared_ptr<T>:
  robot A creates balloon, counter = 1
  robot B copies A's ptr, counter = 2
  A goes out of scope, counter = 1 (still alive)
  B goes out of scope, counter = 0 → balloon destroyed

weak_ptr<T>:
  robot C watches the balloon (counter not incremented)
  C wants to touch it: lock() → creates a temporary shared_ptr
    if counter was 0 (balloon already popped) → lock() returns nullptr
    if counter > 0 → temporary shared_ptr prevents popping during use
```

## The Blueprint

```cpp
// unique_ptr — default choice for heap objects:
auto storage = std::make_unique<LocalStorage>(size);
storage->Read(offset, len);
// destroyed when 'storage' goes out of scope

// Transfer ownership:
auto other = std::move(storage);   // storage is now null
// storage.get() == nullptr

// shared_ptr — for shared ownership:
auto driver = std::make_shared<TCPDriverComm>(fd);
auto mediator = std::make_shared<InputMediator>(driver);
// both hold the TCPDriverComm — it lives as long as either does

// weak_ptr — break cycles:
std::weak_ptr<InputMediator> observer = mediator;
if (auto m = observer.lock()) {
    m->Notify(request);   // safe — m keeps mediator alive during this call
}
```

**Why `make_shared` not `new`:**
- `shared_ptr<T>(new T())` = two allocations (T + control block)
- `make_shared<T>()` = one allocation (T + control block together) → faster, fewer fragmentation points

**Why `make_unique` not `new`:** exception safety. `func(new A(), new B())` can leak if the first `new` succeeds but the second throws before the `unique_ptr` is constructed.

## Where It Breaks

- **Shared_ptr cycle**: A holds `shared_ptr<B>`, B holds `shared_ptr<A>` → both have count ≥ 1 forever → neither is ever destroyed → leak. Break with `weak_ptr`.
- **Raw pointer extracted and outlived the smart pointer**: `T* raw = uptr.get(); uptr.reset(); raw->method();` → use-after-free.
- **Copying a `unique_ptr`**: compile error. You must `std::move` it — intentional design.

## In LDS

`services/mediator/include/InputMediator.hpp`

`InputMediator` holds a `std::shared_ptr<IDriverComm> m_driver`. This is the Strategy pattern expressed through `shared_ptr` — the driver (either `TCPDriverComm` or `NBDDriverComm`) is injected at construction and shared between `InputMediator` and its tests. The test creates a mock driver as `shared_ptr`, injects it, and both the test and the mediator share ownership — the mock isn't destroyed while either holds a reference.

## Validate

1. `InputMediator` holds `shared_ptr<IDriverComm>`. The test also holds the same `shared_ptr`. The test goes out of scope. Is the `IDriverComm` object destroyed? Why?
2. You have a `shared_ptr<LocalStorage>` with count=3. You call `.get()` and store the raw pointer. All three `shared_ptr`s go out of scope. `LocalStorage` is destroyed. You use the raw pointer. What happens?
3. Why should `IDriverComm` have a virtual destructor, given that it's accessed via `shared_ptr<IDriverComm>`?

## Connections

**Theory:** [[02 - Smart Pointers]]  
**Mental Models:** [[RAII — The Machine]], [[Move Semantics — The Machine]], [[Strategy Pattern — The Machine]], [[Inheritance — The Machine]]  
**LDS Implementation:** [[LDS/Application/LocalStorage]] — shared ownership of mediator/driver  
**Runtime Machines:** [[LDS/Runtime Machines/InputMediator — The Machine]]  
**Glossary:** [[shared_ptr]], [[RAII]]
