# Inheritance — The Machine

## The Model
A physical extension of a base object. A `NBDDriverComm` object contains a complete `IDriverComm` sub-object as its first bytes, then appends its own data. A base pointer can point to a derived object because the base part is physically at the beginning — the pointer points to exactly the right place.

## How It Moves

```
IDriverComm object layout:    [vptr(8)] = 8 bytes total

NBDDriverComm object layout:  [vptr(8)][m_fd(4)][m_buf(8)][...] 
                               ↑
                               IDriverComm subobject is right here (first 8 bytes)

IDriverComm* p = new NBDDriverComm();
  p points to the start of the NBDDriverComm object
  p->SendReply() → vptr → NBD vtable → NBDDriverComm::SendReply ✓

// Object slicing:
IDriverComm copy = *p;   // copies ONLY the first 8 bytes (IDriverComm part)
                          // copy has a correct vptr... but it's a base object
                          // NBD data (m_fd, m_buf) is gone
```

**WHY base at offset 0:** makes it free to cast a derived pointer to base pointer — no offset adjustment needed. The derived pointer IS already a valid base pointer.

## The Blueprint

```cpp
class IDriverComm {         // pure interface — no data, pure virtual methods
    virtual ~IDriverComm() = default;
    virtual void SendReply(const Request&) = 0;
};

class NBDDriverComm : public IDriverComm {
    int m_fd;               // appended after base subobject
public:
    void SendReply(const Request& req) override { write(m_fd, ...); }
};
```

**public vs private inheritance:**
- `public`: "is-a" — `NBDDriverComm` IS-A `IDriverComm`. Base is accessible everywhere.
- `private`: "implemented-in-terms-of" — inherits implementation, hides the base type from outside. Rare — prefer composition.

**Composition over inheritance:** if `B` does not need to be used as an `A`, don't inherit — contain:
```cpp
class TCPDriverComm : public IDriverComm {
    Socket m_socket;    // composition — TCPDriverComm HAS-A Socket, not IS-A Socket
};
```

## Where It Breaks

- **Slicing**: passing derived by value to base parameter — base copy constructor called, derived part cut off
- **Forgetting `virtual` destructor**: base destructor called on delete via base pointer — derived resources not cleaned up
- **Diamond inheritance**: B and C both inherit A; D inherits B and C — D has two copies of A's data. Solved with `virtual` inheritance (rarely needed).

## In LDS

`interfaces/IDriverComm.hpp` → `services/communication_protocols/nbd/include/NBDDriverComm.hpp` + `tcp/include/TCPDriverComm.hpp`

Both `NBDDriverComm` and `TCPDriverComm` inherit from `IDriverComm`. This is the Strategy pattern expressed through inheritance. `InputMediator` only knows the base interface — it can hold either concrete type behind the same pointer. When you construct LDS in TCP mode, you inject a `TCPDriverComm`; in NBD mode, a `NBDDriverComm`. The inheritance hierarchy is what makes this substitution possible.

## Validate

1. `IDriverComm* p = new TCPDriverComm()`. You call `delete p`. `IDriverComm` has no virtual destructor. `TCPDriverComm` owns a socket. What happens?
2. A function takes `IDriverComm driver` by value (not pointer or reference). You pass a `TCPDriverComm`. What is `driver` inside the function?
3. `NBDDriverComm` has `m_fd` (4 bytes). `IDriverComm` has only `vptr` (8 bytes). What is `sizeof(NBDDriverComm)`? (assume no padding)
