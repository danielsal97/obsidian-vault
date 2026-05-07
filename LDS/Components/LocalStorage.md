# LocalStorage

**Phase:** 1 (complete) | **Status:** ✅ Implemented

**Files:**
- `services/local_storage/include/LocalStorage.hpp`
- `services/local_storage/src/LocalStorage.cpp`

---

## Responsibility

`LocalStorage` is the current **in-memory block storage backend**. It stores all data in a `std::vector<char>` sized at startup. It has no persistence — data is lost on process exit. This is Phase 1's storage — it will be replaced by the distributed RAID01 backend in Phase 2+.

---

## Interface

```cpp
class LocalStorage {
public:
    explicit LocalStorage(size_t size);   // allocates size bytes, zero-initialized

    void Read(std::shared_ptr<DriverData> data);
    void Write(std::shared_ptr<DriverData> data);

private:
    std::vector<char> m_storage;
};
```

---

## Implementation

```cpp
LocalStorage::LocalStorage(size_t size)
    : m_storage(size, 0) {}   // zero-initialized, allocated once

void LocalStorage::Read(std::shared_ptr<DriverData> data) {
    // Copy from m_storage into data->m_buffer
    auto begin = m_storage.begin() + data->m_offset;
    auto end   = begin + data->m_buffer.size();
    std::copy(begin, end, data->m_buffer.begin());
    data->m_status = DriverData::SUCCESS;
}

void LocalStorage::Write(std::shared_ptr<DriverData> data) {
    // Copy from data->m_buffer into m_storage
    auto dest = m_storage.begin() + data->m_offset;
    std::copy(data->m_buffer.begin(), data->m_buffer.end(), dest);
    data->m_status = DriverData::SUCCESS;
}
```

---

## Known Bugs

### Bug 1: Bounds Check Wrong
```cpp
// Current (wrong):
if (data->m_offset > m_storage.size()) { throw ...; }

// Missing: doesn't check if offset + length exceeds storage
// Write at offset=size-100, length=200 → writes 100 bytes out of bounds
// Correct:
if (data->m_offset + data->m_buffer.size() > m_storage.size()) { throw ...; }
```

### Bug 2: Not Thread-Safe
```cpp
// m_storage has no mutex
// Phase 1: single-threaded handler → no problem
// Phase 2+: ThreadPool executes concurrent WriteCommands → data race
// Fix: std::shared_mutex (shared_lock for Read, unique_lock for Write)
```

Full details: [[Known Bugs]]

---

## Transition to Phase 2

In Phase 2, `LocalStorage` is replaced by the RAID01 distributed backend. The Reactor and NBDDriverComm don't change — they still call `Read(data)` and `Write(data)` on whatever storage backend is plugged in.

```
Phase 1: LocalStorage (in-RAM, single node)
Phase 2: RAID01Manager + MinionProxy (distributed, multi-node)
```

The `IDriverComm` / `DriverData` interface stays constant throughout all phases.

---

## Related Notes
- [[NBDDriverComm]]
- [[RAID01 Manager]]
- [[Known Bugs]]
