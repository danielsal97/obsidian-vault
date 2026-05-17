# Strategy Pattern — The Machine

## The Model
A chassis with a swappable engine slot. The chassis (context) works the same way regardless of which engine is plugged in. You can swap the engine at construction time or even at runtime — the chassis doesn't need to change. Instead of if/else chains that grow with every new mode, you add a new engine class.

## How It Moves

```
WITHOUT strategy:
  void InputMediator::SendReply(Request req) {
    if (mode == "nbd")  { /* NBD-specific code */ }
    if (mode == "tcp")  { /* TCP-specific code */ }
    if (mode == "udp")  { /* UDP-specific code */ }   ← add new mode = edit this file
  }

WITH strategy:
  void InputMediator::SendReply(Request req) {
    m_driver->SendReply(req);   ← same code, any driver
  }
  // Adding UDP mode = add UDPDriverComm class, change factory = zero changes here
```

**Dependency injection:** the strategy is NOT created inside the context — it's passed in (constructor injection or setter injection). This makes the context testable: inject a mock strategy in tests, inject the real one in production.

## The Blueprint

```cpp
// Interface (strategy):
class IDriverComm {
public:
    virtual void SendReply(const Request& req) = 0;
    virtual Request RecvRequest() = 0;
    virtual ~IDriverComm() = default;
};

// Concrete strategies:
class NBDDriverComm : public IDriverComm { ... };
class TCPDriverComm : public IDriverComm { ... };

// Context — holds strategy, uses interface only:
class InputMediator {
    std::shared_ptr<IDriverComm> m_driver;
public:
    InputMediator(std::shared_ptr<IDriverComm> driver)
        : m_driver(std::move(driver)) {}
    
    void Notify(const Request& req) {
        // uses m_driver without knowing its type:
        m_driver->SendReply(processRequest(req));
    }
};

// Wiring (in main or factory):
auto driver = std::make_shared<TCPDriverComm>(7800);
auto mediator = std::make_shared<InputMediator>(driver);
```

## Where It Breaks

- **Strategy creates its own dependencies**: if `InputMediator` calls `new NBDDriverComm()` inside, it's coupled to the concrete type — Strategy pattern benefits are lost. Always inject.
- **Strategy state shared between calls**: if the strategy stores per-request state and is shared between threads, race conditions occur. Stateless strategies are safest.
- **Missing virtual destructor**: if `InputMediator` holds `unique_ptr<IDriverComm>` and the strategy is replaced, the old one is deleted via base pointer → resource leak.

## In LDS

`interfaces/IDriverComm.hpp` → `services/mediator/include/InputMediator.hpp`

`IDriverComm` is the strategy interface. `NBDDriverComm` and `TCPDriverComm` are the two concrete strategies. `InputMediator` is the context — it only calls `m_driver->SendReply` and `m_driver->RecvRequest`. In tests, a mock `IDriverComm` is injected — `InputMediator` is tested without any real socket or NBD device. In production, the factory creates either `NBDDriverComm` or `TCPDriverComm` based on configuration and injects it.

## Validate

1. `InputMediator` is tested with a mock `IDriverComm`. The test verifies `SendReply` is called with the correct reply. Does the test need to create a socket or open `/dev/nbd0`? Why?
2. You add `UDPDriverComm`. Which files change, and which files do NOT change?
3. Two threads share the same `IDriverComm` instance (via `shared_ptr`). `NBDDriverComm::SendReply` writes to a socket fd. Is this thread-safe? What makes it safe or unsafe?

## Connections

**Theory:** [[06 - Strategy]]  
**Mental Models:** [[Factory Pattern — The Machine]], [[Virtual Functions — The Machine]], [[Smart Pointers — The Machine]], [[Observer Pattern — The Machine]]  
**LDS Implementation:** [[LDS/Decisions/Why Templates not Virtual Functions]]  
**Runtime Machines:** [[LDS/Runtime Machines/InputMediator — The Machine]]  
**Glossary:** [[shared_ptr]], [[Templates]]
