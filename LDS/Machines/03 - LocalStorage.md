# LDS LocalStorage — The Machine

## The Model
A warehouse with one large shelf (`m_storage`) and a single locked door. Every worker who wants to read from or write to the shelf must grab the door key first (`m_lock`). The warehouse also keeps a ledger (`m_offset_sizes`) that records what was written to each shelf address — so if someone asks "how big was the thing at offset 512?", the answer is instant. Importantly: the shelf is pre-allocated at construction — it never grows or shrinks.

## How It Moves

```
Construction:
  LocalStorage(size_):
    m_storage = vector<char>(size_)   ← one allocation, size_ bytes, zero-filled
    m_lock = mutex{}
    m_offset_sizes = map<size_t, size_t>{}   ← empty ledger

Write(data_):
  lock_guard lock(m_lock)   ← acquire key (released at end of scope)
  
  if data_->m_offset + data_->m_buffer.size() > m_storage.size():
    throw out_of_range(...)   ← bounds check BEFORE writing
  
  copy(data_->m_buffer → m_storage[m_offset]...)   ← memcpy semantics
  m_offset_sizes[data_->m_offset] = data_->m_buffer.size()   ← update ledger
  
  lock released (scope exit)

Read(data_):
  lock_guard lock(m_lock)
  
  if data_->m_offset + data_->m_buffer.size() > m_storage.size():
    throw out_of_range(...)
  
  copy(m_storage[m_offset]... → data_->m_buffer)   ← data goes OUT into buffer

GetDataSize(offset_):
  lock_guard lock(m_lock)   ← m_lock is mutable — const method can still lock
  return m_offset_sizes[offset_]   ← ledger lookup (0 if never written)
```

**The `shared_ptr<DriverData>` contract:**
`data_->m_buffer` is the carrier. For `Read`, the buffer is pre-sized by the caller — LocalStorage fills it. For `Write`, the buffer holds the incoming bytes — LocalStorage copies them in. The shared_ptr keeps DriverData alive across the async thread handoff: main thread creates it, ThreadPool worker executes it, nobody destroys it prematurely.

**Why `mutable std::mutex`:**
`GetDataSize()` is `const` (doesn't modify storage logically) but needs a lock (modifies locking state). `mutable` lets a `const` method acquire a mutex — standard C++ idiom for thread-safe const methods.

## The Blueprint

```cpp
// local_storage/include/LocalStorage.hpp:
class LocalStorage : public IStorage {
    std::vector<char> m_storage;          // the shelf
    mutable std::mutex m_lock;            // the key
    std::map<size_t, size_t> m_offset_sizes;  // the ledger

public:
    explicit LocalStorage(size_t size_);
    void Read(std::shared_ptr<DriverData> data_) override;   // throws out_of_range
    void Write(std::shared_ptr<DriverData> data_) override;  // throws out_of_range
    size_t GetDataSize(size_t offset_) const;
};

// local_storage/src/LocalStorage.cpp — Write():
void LocalStorage::Write(std::shared_ptr<DriverData> data_) {
    std::lock_guard<std::mutex> lock(m_lock);
    if (data_->m_offset + data_->m_buffer.size() > m_storage.size())
        throw std::out_of_range("Write exceeds storage bounds");
    std::copy(data_->m_buffer.begin(), data_->m_buffer.end(),
              m_storage.begin() + data_->m_offset);
    m_offset_sizes[data_->m_offset] = data_->m_buffer.size();
}
```

**IStorage interface:**
```cpp
class IStorage {
public:
    virtual void Read(std::shared_ptr<DriverData> data_) = 0;
    virtual void Write(std::shared_ptr<DriverData> data_) = 0;
    virtual ~IStorage() = default;
};
```

`InputMediator` holds `IStorage*` — it calls `m_storage->Read(request)` and `m_storage->Write(request)` without knowing whether the concrete type is `LocalStorage` or `RAID01Manager`. This is the `IStorage` interface's entire purpose: Phase 1 → Phase 2 swap with zero changes to the Mediator.

## Where It Breaks

- **Concurrent write + write to same offset**: Two workers call `Write()` with overlapping offsets. They serialize on `m_lock` — one waits. No corruption, but no parallelism for overlapping regions.
- **Concurrent read + write**: `Read()` and `Write()` both need the full lock. An exclusive lock on the mutex means reads are serialized with writes — even read-read contention exists. A `shared_mutex` (reader-writer lock) would allow concurrent reads.
- **Out of bounds throws — who catches?**: `out_of_range` escapes `Execute()` in the worker thread. If `ThreadFunc()` doesn't catch it, `std::terminate` is called and the entire process dies. The handler lambda in `InputMediator::SetupHandlers()` should catch storage exceptions.
- **`m_offset_sizes` never shrinks**: Every unique offset that's ever been written is in the map forever — even if the storage is "overwritten" (the old size stays until re-written). Not a correctness problem for current use.

## In LDS

`services/local_storage/include/LocalStorage.hpp` + `src/LocalStorage.cpp`

Phase 1's concrete storage. Created in `main()` alongside the driver:
```cpp
LocalStorage storage(storageSize);
InputMediator mediator(&driver, &storage);
```

`InputMediator` holds `IStorage* m_storage` — so `storage` is passed as `IStorage*`, enabling Phase 2 drop-in of `RAID01Manager` with no change to `InputMediator`. LocalStorage is non-copyable (copy constructor `= delete`) — passing raw pointer (not by value) is the correct interface.

## Validate

1. Two ThreadPool workers receive a READ and a WRITE to the same offset simultaneously. One has `lock_guard lock(m_lock)`. Describe exactly what happens to the other. Who decides which one goes first?
2. `GetDataSize(512)` is called before any `Write(offset=512)` has occurred. What does `m_offset_sizes.find(512)` return, and what does `GetDataSize` return?
3. Replace `std::mutex` with `std::shared_mutex` and use `shared_lock` for `Read()` and `unique_lock` for `Write()`. What concurrency improvement does this give? What breaks with `GetDataSize()`?
