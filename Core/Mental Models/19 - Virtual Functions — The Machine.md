# Virtual Functions — The Machine

## The Model
A dispatch table (vtable) attached to every class with virtual functions. Each object holds a hidden pointer to its class's table. The table is a list of function pointers — one slot per virtual function. Calling a virtual function = follow the hidden pointer to the table, look up slot N, call whatever is there. Different classes have different tables, so the same slot N calls different code.

## How It Moves

```
IDriverComm vtable:           NBDDriverComm vtable:       TCPDriverComm vtable:
┌─────────────────────┐       ┌─────────────────────┐     ┌─────────────────────┐
│ slot 0: SendReply   │──?    │ slot 0: &NBD::Send   │     │ slot 0: &TCP::Send  │
│ slot 1: RecvRequest │       │ slot 1: &NBD::Recv   │     │ slot 1: &TCP::Recv  │
└─────────────────────┘       └─────────────────────┘     └─────────────────────┘

Object layout:
  NBDDriverComm object:   [ vptr → NBD vtable | m_fd | m_buf | ... ]
  TCPDriverComm object:   [ vptr → TCP vtable | m_socket | ... ]

InputMediator holds: shared_ptr<IDriverComm> m_driver
  m_driver->SendReply(req)
    1. Load vptr from object (first 8 bytes)
    2. Load function pointer from vtable[0]
    3. Call it
  Result: always calls the right SendReply for whatever object is there
```

## The Blueprint

```cpp
class IDriverComm {
public:
    virtual void SendReply(const Request& req) = 0;   // pure virtual = slot must be filled
    virtual Request RecvRequest() = 0;
    virtual ~IDriverComm() = default;                  // MUST be virtual
};

class NBDDriverComm : public IDriverComm {
public:
    void SendReply(const Request& req) override { ... }   // fills slot 0
    Request RecvRequest() override { ... }                // fills slot 1
};
```

**`= 0` (pure virtual):** the slot exists but is empty. Any class that inherits without filling it becomes abstract — cannot be instantiated. Forces derived classes to implement the interface.

**Virtual destructor:** if you `delete` a `IDriverComm*` that actually points to a `NBDDriverComm`, without a virtual destructor only `IDriverComm::~IDriverComm` runs — `NBDDriverComm`'s destructor (which closes `m_fd`) never runs. Always declare base class destructors `virtual`.

**Cost:** one pointer dereference + one indirect function call. ~5ns. Negligible unless called billions of times per second.

## Where It Breaks

- **Missing virtual destructor**: memory/resource leak when deleting derived via base pointer
- **Object slicing**: `IDriverComm copy = *derived_ptr;` copies only the `IDriverComm` part — vtable pointer is now wrong, derived data lost
- **Calling virtual in constructor/destructor**: the vtable is not yet/already set to the derived class — base version is called. Surprising behavior.

## In LDS

`interfaces/IDriverComm.hpp`

`IDriverComm` is a pure virtual interface. `NBDDriverComm` and `TCPDriverComm` both implement it. `InputMediator` holds a `shared_ptr<IDriverComm>` — it never knows which concrete type it has. When `InputMediator::Notify` calls `m_driver->SendReply(request)`, the vtable dispatch selects the correct implementation at runtime. Switching from NBD to TCP mode = swap which object is injected — zero code change in `InputMediator`.

## Validate

1. `InputMediator` calls `m_driver->SendReply(req)`. How many memory reads does the CPU perform before reaching the first instruction of `TCPDriverComm::SendReply`?
2. You delete a `NBDDriverComm` via an `IDriverComm*`. `IDriverComm` has no virtual destructor. `NBDDriverComm` has `m_fd` (a socket). What leaks?
3. You try to instantiate `IDriverComm comm;`. What happens and why?

## Connections

**Theory:** [[Core/Theory/C++/06 - Virtual Functions]]  
**Mental Models:** [[Inheritance — The Machine]], [[Templates — The Machine]], [[Strategy Pattern — The Machine]], [[Smart Pointers — The Machine]]  
**Tradeoffs:** [[LDS/Decisions/Why Templates not Virtual Functions]]  
**LDS Implementation:** [[LDS/Runtime Machines/InputMediator — The Machine]] — IDriverComm vtable dispatch  
**Glossary:** [[shared_ptr]], [[Templates]]
