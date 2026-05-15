# DriverData — The Central Data Carrier

`DriverData` is the shared struct that flows through every layer of LDS. It is created by the driver (`NBDDriverComm` or `TCPDriverComm`), handed to `InputMediator`, dispatched into a command, executed against storage, and finally used to send the reply. Every component that touches a request reads from or writes to a `DriverData`.

---

## The Struct

```cpp
// shared/include/DriverData.hpp

#pragma once
#include <cstdint>
#include <vector>
#include <memory>

enum class ActionType : uint8_t {
    READ       = 0x00,   // read `m_len` bytes from `m_offset`
    WRITE      = 0x01,   // write `m_buffer` to `m_offset`
    FLUSH      = 0x02,   // flush all pending writes to storage
    DISCONNECT = 0x03,   // driver is closing — begin shutdown
    GET_SIZE   = 0x04    // TCP-only: query bytes stored at `m_offset`
};

enum class RequestStatus : uint8_t {
    PENDING  = 0x00,   // initial state — not yet executed
    SUCCESS  = 0x01,   // operation completed without error
    ERROR    = 0x02    // operation failed — reply EIO to kernel/client
};

struct DriverData {
    ActionType            m_type;    // what operation the driver requested
    uint64_t              m_handle;  // NBD handle — echoed back in SendReply so kernel
                                     // matches the reply to the original request
    uint64_t              m_offset;  // byte offset into the virtual block device
    uint32_t              m_len;     // number of bytes to read or write
    std::vector<char>     m_buffer;  // payload: driver fills this for WRITE;
                                     // storage fills this for READ
    RequestStatus         m_status;  // set by storage layer before SendReply is called

    DriverData(ActionType type, uint64_t handle, uint64_t offset, uint32_t len)
        : m_type(type), m_handle(handle), m_offset(offset),
          m_len(len), m_status(RequestStatus::PENDING)
    {
        if (type == ActionType::READ) {
            m_buffer.resize(len);   // pre-allocate so storage can write directly
        }
    }
};
```

---

## Ownership Contract

`DriverData` is always heap-allocated and passed as `shared_ptr<DriverData>`.

```
Driver (NBDDriverComm / TCPDriverComm)
  │  creates: make_shared<DriverData>(type, handle, offset, len)
  │  for WRITE: fills m_buffer with data read from the socket
  ▼
InputMediator::Notify(fd)
  │  calls driver.ReceiveRequest() → gets shared_ptr<DriverData>
  │  calls CreateCommand(data) → command captures the shared_ptr
  ▼
ICommand::Execute()   ← runs on a ThreadPool worker thread
  │  for READ:  calls m_storage->Read(data)  → storage fills data->m_buffer
  │  for WRITE: calls m_storage->Write(data) → storage writes data->m_buffer
  │  sets data->m_status = SUCCESS or ERROR
  ▼
m_driver->SendReply(data)
  │  echoes data->m_handle back to the kernel
  │  sends data->m_buffer if ActionType == READ
  └─ shared_ptr ref count drops to zero → DriverData destroyed
```

The `shared_ptr` ensures the data outlives any thread boundary. The driver, the command, and the storage layer all hold a reference simultaneously while the operation is in flight.

---

## Field Reference

| Field | Type | Set by | Read by |
|-------|------|--------|---------|
| `m_type` | `ActionType` | Driver (ReceiveRequest) | InputMediator (dispatch), Command (Execute) |
| `m_handle` | `uint64_t` | Driver (ReceiveRequest) | Driver (SendReply) — echoed back to kernel |
| `m_offset` | `uint64_t` | Driver (ReceiveRequest) | Storage layer (Read/Write), RAID01 (GetBlockLocation) |
| `m_len` | `uint32_t` | Driver (ReceiveRequest) | Storage layer (read size), Command (buffer allocation) |
| `m_buffer` | `vector<char>` | Driver (WRITE payload); Storage (READ result) | Driver (SendReply sends it for READ) |
| `m_status` | `RequestStatus` | Storage layer / Command (after Execute) | Driver (SendReply — sends EIO on ERROR) |

---

## RAID01 Phase 2 Note

In Phase 2, `RAID01Manager::Write()` fans the request out to two minions. The `shared_ptr<DriverData>` is passed to `WriteCommand::Execute()`, which:
1. Calls `GetBlockLocation(data->m_offset)` to find primary + replica
2. Sends UDP to both minions via `MinionProxy::Send(block, data->m_buffer, msg_id)`
3. Waits for both ACKs via `ResponseManager`
4. Sets `data->m_status = SUCCESS` before returning

The `m_buffer` is read-only during RAID01 fan-out — both `sendto()` calls read the same vector. No copy needed.

---

## In LDS

`shared/include/DriverData.hpp` — included by:
- `NBDDriverComm` — creates DriverData from NBD wire format
- `TCPDriverComm` — creates DriverData from TCP wire format
- `InputMediator` — receives and dispatches
- `ReadCommand`, `WriteCommand`, `FlushCommand` — execute against storage
- `LocalStorage`, `RAID01Manager` — fill m_buffer / set m_status
- `IDriverComm::SendReply()` — reads m_handle, m_buffer, m_status

---

## Validate

1. A WRITE arrives: `m_buffer` is filled by the driver. `WriteCommand::Execute()` passes `data->m_buffer` to `LocalStorage::Write()`. Who owns the buffer memory? When is it freed?
2. A READ arrives: `m_buffer` is pre-allocated to `m_len` bytes in the constructor. `LocalStorage::Read()` writes into it. Then `SendReply()` sends it. Is the buffer safe to read from the Reactor thread after Execute() runs on a worker thread?
3. `m_status` starts as `PENDING`. If Execute() throws before setting it to `SUCCESS`, `SendReply()` sends `ERROR`. Trace what the kernel sees.
