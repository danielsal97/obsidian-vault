# LDS Architecture - Detailed Analysis

## Component Dependency Graph

```
Application Layer
└─ LDS.cpp (main)
   ├─ RunNBDMode / RunTCPMode
   └─ RunServer (template)
      ├─ LocalStorage
      ├─ NBDDriverComm or TCPDriverComm
      ├─ InputMediator
      ├─ Reactor
      └─ ThreadPool

Reactor (Event Loop)
├─ epoll_wait()
├─ SetHandler(callback)
├─ SetupSignals()
└─ Run() → Handler → InputMediator::Notify()

InputMediator (Orchestration)
├─ IDriverComm* (driver reference)
├─ IStorage* (storage reference)
├─ ThreadPool* (pool reference)
├─ m_handlers map
└─ Notify(fd) → CreateCommand → AddCommand

ThreadPool (Concurrency)
├─ WPQ<ICommand> (priority queue)
├─ std::vector<std::thread> workers
├─ AddCommand(cmd) → Push to queue
├─ Worker threads → Execute()
└─ Stop() → Send StopCommand to all

LocalStorage (Data)
├─ std::vector<char> m_storage
├─ std::mutex m_lock
├─ Read(DriverData*)
├─ Write(DriverData*)
└─ GetDataSize()

NBDDriverComm (Protocol)
├─ m_serverFd (socket to kernel)
├─ ReceiveRequest()
├─ SendReply(DriverData*)
└─ Disconnect()

TCPDriverComm (Protocol)
├─ m_listen_fd (listen socket)
├─ m_client_fd (client socket)
├─ ReceiveRequest()
├─ SendReply(DriverData*)
└─ Disconnect()

Utilities
├─ Logger (singleton) → Thread-safe logging
├─ Singleton<T> → Double-checked locking
├─ Factory → Object creation registry
├─ ICommand → Priority-based tasks
└─ WPQ → Ordered task queue
```

---

## Request Processing Flow

### Happy Path: READ Request

```
1. KERNEL sends READ request on /dev/nbd0
   │
   ├─ NBD kernel driver writes to socket
   │
2. Reactor detects epoll event
   │
   ├─ epoll_wait() returns
   ├─ Event handler called synchronously
   │
3. InputMediator::Notify(fd)
   │
   ├─ m_driver->ReceiveRequest() [BLOCKING]
   │   ├─ ReadAll(socket, header, 28 bytes)
   │   └─ Parse NBD_CMD_READ
   │
   ├─ Create FunctionCommand lambda
   │   ├─ Captures: request (shared_ptr)
   │   ├─ Handler body: 
   │   │   ├─ m_storage->Read(request)
   │   │   └─ m_driver->SendReply(request)
   │   └─ Priority: Med
   │
   ├─ ThreadPool::AddCommand(cmd)
   │   └─ WPQ::Push(cmd)
   │
4. REACTOR CONTINUES (back to epoll_wait)
   │
5. WORKER THREAD (async)
   │
   ├─ Pop command from queue
   ├─ FunctionCommand::Execute()
   │
6. LocalStorage::Read(request)
   │
   ├─ Lock m_lock (mutex)
   ├─ Copy m_storage[offset..offset+len] to request->m_buffer
   ├─ Set request->m_status = SUCCESS
   └─ Unlock m_lock
   │
7. SendReply(request)
   │
   ├─ Build nbd_reply header
   ├─ WriteAll(socket, reply, 16 bytes)
   ├─ WriteAll(socket, payload, len bytes)
   └─ Return
   │
8. KERNEL reads reply and completes syscall
   │
9. APPLICATION reads from /dev/nbd0 and gets data
```

### Error Path: Invalid Command Type

```
1. Reactor wakes on socket event
2. ReceiveRequest() returns request with m_type = 999 (invalid)
3. ThreadPool worker created and starts
4. FunctionCommand::Execute()
   │
   ├─ m_handlers.at(999) [THROWS std::out_of_range]
   │
   ⚠️ EXCEPTION NOT CAUGHT
      └─ Propagates up worker thread
         ├─ Worker dies with uncaught exception
         ├─ ThreadPool doesn't know
         └─ Client never receives reply 🔴
```

---

## Threading Execution Timeline

### Single Request Scenario

```
TIME   MAIN THREAD (Reactor)        WORKER THREAD (ThreadPool)
────────────────────────────────────────────────────────────────
T0     epoll_wait() [blocked]       [waiting on queue]
T1     ↓ EVENT
       Handler()
       └─ ReceiveRequest() [BLOCKED on socket read]
T2     ↓ Socket data arrives
       Header parsed
       FunctionCommand created
       AddCommand() queued
       Resume epoll_wait() [blocked again]
                                     ↓ Command available
                                     Pop from queue
                                     Execute()
T3                                  Lock LocalStorage
                                    ├─ Read data
                                    └─ Unlock
T4                                  SendReply() [BLOCKED on socket write]
T5                                  ↓ Data sent
                                    Return from Execute()
                                    [waiting on queue]
```

### Two Concurrent Requests (NBD)

```
Client A sends READ at T0
Client B sends READ at T1
```

**Problem:** Sequential processing
```
T0: Reactor receives A's request
    ├─ ReceiveRequest() for A [BLOCKED]
    └─ Cannot accept B's request yet

T1: B's request arrives
    └─ Waits in kernel socket buffer
       (Reactor is blocked on A's socket)

T2: A's request fully received
    ├─ AddCommand(A)
    └─ Resume epoll_wait()
       └─ NOW sees B's request

T3: ReceiveRequest() for B [BLOCKED]

T4-T5: Processors A in thread pool
T6-T7: Process B in thread pool
```

**Result:** Both clients processed, but serially at socket receive level.

---

## Thread Safety Matrix

### Shared State Access

```
STATE                    MAIN THREAD    WORKER THREADS    PROTECTION
─────────────────────────────────────────────────────────────────────
Reactor::m_io_handler    Write (once)   Read (never)      ✅ Safe
ThreadPool queue         Read (push)    Read (pop)        ✅ WPQ mutex
LocalStorage            Read indirect   Read/Write        ✅ std::mutex
LocalStorage m_storage  via handler    R/W              ✅ std::mutex
Logger singleton        Read           Read             ✅ mutex in Logger
request (shared_ptr)    Create         Read/Modify      ✅ shared_ptr
m_handlers map          Setup          Read             ✅ Setup before use
```

### Safe Patterns ✅

1. **Reactor Handler → ThreadPool**
   - Handler creates command, queues it
   - Returns immediately
   - Worker thread executes asynchronously
   - ✅ Good separation of concerns

2. **LocalStorage Mutex**
   - All Read/Write operations protected
   - Lock guard ensures unlock
   - ✅ RAII pattern

3. **shared_ptr Captures**
   ```cpp
   auto cmd = std::make_shared<FunctionCommand>(
       [this, request]() {  // request captured by value (shared_ptr copy)
           m_handlers.at(request->m_type)(request);
       }
   );
   ```
   - shared_ptr increments ref count
   - Handler keeps request alive
   - ✅ Memory safe

### Unsafe Patterns ⚠️

1. **Blocking Handler**
   ```cpp
   Reactor::Run() {
       m_io_handler(fd);  // Synchronous
   }
   
   InputMediator::Notify() {
       m_driver->ReceiveRequest();  // BLOCKS
   }
   ```
   - Reactor thread frozen during socket read
   - ⚠️ No parallelism at I/O level

2. **Exception in Worker**
   ```cpp
   m_handlers.at(request->m_type)(request);  // Can throw
   ```
   - No try-catch around handler
   - Exception kills worker thread
   - ⚠️ Client never gets reply

---

## Design Pattern Implementation Details

### Reactor Pattern

**Key Features:**
```cpp
class Reactor {
    int m_epoll_fd;              // epoll instance
    int m_signal_fd;             // signalfd for SIGINT/SIGTERM
    std::function<void(int)> m_io_handler;
    
    void Run() {
        while (true) {
            int n = epoll_wait(m_epoll_fd, events, MAX_EVENTS, -1);
            for (int i = 0; i < n; ++i) {
                if (events[i].data.fd == m_signal_fd) {
                    return;  // Graceful shutdown
                }
                m_io_handler(events[i].data.fd);  // Call handler
            }
        }
    }
};
```

**Characteristics:**
- ✅ Non-blocking multiplexing via epoll
- ✅ Signal handling via signalfd
- ⚠️ Synchronous handler execution
- ⚠️ Handler blocking freezes reactor

### Command Pattern + Priority Queue

**Execution Order:**
```
Admin priority > High > Med > Low

Example queue:
  [High: Flush]
  [Med: Read request A]
  [Med: Read request B]
  [Low: Trim]
  
Workers will execute:
1. Flush (High)
2. Read A (Med)
3. Read B (Med)
4. Trim (Low)
```

**Implementation:**
```cpp
class ICommand {
    enum CMDPriority { Low, Med, High, Admin };
    bool operator<(const ICommand& rhs) const {
        return this->m_priority > rhs.m_priority;  // Inverted for max-heap
    }
};

class WPQ {  // Priority queue with mutex
    std::priority_queue<T, Vector, Comparator> m_queue;
    std::mutex m_lock;
};
```

### Mediator Pattern

**Role:** Decouple driver from storage
```
Without Mediator:
  Driver → Storage (coupled)
  
With Mediator:
  Driver ─→ Mediator ←─ Storage
           (loose coupling)
```

**Handler Map:**
```cpp
struct InputMediator {
    std::map<int, std::function<void(std::shared_ptr<DriverData>)>> m_handlers;
    
    void SetupHandlers() {
        m_handlers[DriverData::READ] = 
            [this](auto request) { 
                m_storage->Read(request);
                m_driver->SendReply(request); 
            };
        // ... other command types
    }
};
```

---

## Signal Handling Flow

### Normal Operation
```
Main thread → Reactor → epoll_wait() [BLOCKED]
                            ↓
                    [SIGINT arrives]
                            ↓
                    signalfd wakes epoll
                            ↓
                    Handler sees m_signal_fd
                            ↓
                    Return from Run() (graceful shutdown)
                            ↓
                    ~Reactor() closes signalfd, epoll_fd
                            ↓
                    ~ThreadPool() stops workers
```

### Problem: During Socket Read
```
Main thread → Reactor → Handler → ReceiveRequest() [BLOCKED on socket.read()]
                              ↓
                        [SIGINT arrives]
                              ↓
                        signalfd doesn't help (epoll not blocking now)
                              ↓
                        Signal handler (SIG_DFL or custom) runs
                              ↓
                        If SIG_DFL: Process terminates
                        If custom: Still in socket read loop
                              ↓
                        ⚠️ Unclean shutdown
```

**Real Issue:** Signals can't interrupt socket reads easily without signal handlers.

---

## Memory Layout

### Process Memory
```
┌─────────────────────┐
│ Stack               │  <- Local variables, thread stacks
├─────────────────────┤
│ Heap                │  <- new/malloc allocations
│                     │     - ThreadPool threads
│ Reactor             │     - Logger singleton
│ ThreadPool          │     - Locked for LocalStorage
│ LocalStorage        │
│  m_storage vector   │  <- Actual data buffer (size_bytes)
│  m_lock mutex       │
│                     │
├─────────────────────┤
│ BSS                 │  <- Singleton static members
│ Reactor m_epoll_fd  │
│ Singleton s_instance│
├─────────────────────┤
│ Text/Code           │  <- Executable instructions
│ Libraries           │  <- libc, libpthread
└─────────────────────┘
```

### LocalStorage Memory
```
LocalStorage object:
  ├─ m_storage (vector<char>)
  │  └─ heap allocation: [size_bytes]
  │     ├─ [0..offset1] = Client A data
  │     ├─ [offset1..offset2] = Client B data
  │     └─ [offset2..end] = Free space
  │
  ├─ m_lock (std::mutex)
  │  └─ Platform-specific lock structure
  │
  └─ m_offset_sizes (map)
     └─ offset → size tracking for GET_SIZE
```

---

## Failure Modes

### 1. Client Stalls After Sending Header

```
Reactor: ReceiveRequest() [BLOCKED waiting for payload]
         ReadAll(socket, payload, len) [BLOCKED for 10 seconds]
         
Result: 
  - Reactor frozen
  - No new requests accepted
  - Signals ignored
  - ThreadPool idles with no new work
```

### 2. Storage Runs Out of Memory

```
LocalStorage::Write() called with large buffer
  ├─ m_storage.resize(new_size) [THROWS std::bad_alloc]
  │
  ├─ Exception propagates to handler
  └─ Worker thread dies
  
Result:
  - Client never gets reply
  - Data may be partially written
  - No rollback
```

### 3. Invalid Command Type

```
ReceiveRequest() returns request with m_type = 999

FunctionCommand::Execute()
  └─ m_handlers.at(999) [THROWS std::out_of_range]
     ├─ No try-catch
     └─ Worker dies
     
Result:
  - Client timeout waiting for reply
  - Memory leak (request shared_ptr stays alive)
```

### 4. Signal During Handler

```
SIGINT arrives while ReceiveRequest() [BLOCKED on socket]
  
Signal handlers run in Reactor thread, but socket read blocks signal delivery
  
Result:
  - Process may terminate abruptly
  - Unclean shutdown
  - Files left open
```

---

## Configuration & Tunables

### Current Hardcoded Values

```cpp
// Reactor
static constexpr int MAX_EVENTS = 10;  // Max events per epoll_wait

// ThreadPool
size_t ThreadsNum = SetDefNumThreads();  // Gets from CPU count

// Storage
size_t storage_size = argv[3];  // From command line

// Timeout
None  ⚠️  No timeout on socket operations
```

### Recommended Configurable Parameters

```
reactor {
  epoll_timeout_ms: 5000
  max_events: 16
}

threadpool {
  num_threads: 4
  queue_max_size: 1000
}

storage {
  max_size_bytes: 10GB
  enable_raid: false
}

network {
  socket_timeout_sec: 30
  recv_buffer_size: 65536
  send_buffer_size: 65536
}

logging {
  level: INFO
  output_file: /var/log/lds.log
  max_file_size: 100MB
}
```

---

## Integration Points

### With Kernel (NBD)
```
Kernel's block I/O layer
        ↓
/dev/nbd0 device
        ↓ ioctl + socket
NBDDriverComm
        ↓
Reactor [epoll on socket]
        ↓
UserSpace Storage
```

### With Client (TCP)
```
Network Client
        ↓
TCP Port (e.g., 9999)
        ↓
TCPDriverComm [listen socket]
        ↓
Reactor [epoll on socket]
        ↓
UserSpace Storage
```

### With Plugins (PNP)
```
Plugin .so file
        ↓
soLoader (dynamic load)
        ↓
Factory::Register()
        ↓
Runtime instantiation
```

---

## Performance Characteristics

### Request Latency Path

```
T0: Socket has data
    └─ epoll_wait() returns (latency: ~1ms)

T1: Handler executes synchronously
    └─ ReceiveRequest() (latency: depends on socket, ~0.1-10ms)

T2: Command queued
    └─ AddCommand() (latency: ~0.01ms)

T3: Worker gets CPU
    └─ Pop from queue (latency: ~0.01ms)

T4: Execute handler
    └─ Read/Write + SendReply (latency: depends on storage + socket, ~1-100ms)

Total: ~2-110ms for typical operation
```

### Bottlenecks

1. **Socket I/O:** ReadAll() blocks entire reactor
   - Impact: No parallelism at protocol level
   - Fix: Non-blocking sockets + incremental parsing

2. **LocalStorage Mutex:** All threads serialize on m_lock
   - Impact: Only one read/write at a time
   - Fix: Fine-grained locking or lock-free structure

3. **ThreadPool Queue Contention:** All workers compete for lock
   - Impact: Minimal, WPQ well-designed
   - Fix: Per-thread queues if needed

### Throughput Estimates

```
Single Worker: ~1000 requests/sec (assuming 1ms handler time)
4 Workers:     ~4000 requests/sec (parallel execution)
Bottleneck:    Socket I/O (sequential at accept/ReceiveRequest level)
```

---

## Testing Strategy

### Unit Tests (Current)

- ✅ test_reactor.cpp - Validates epoll loop
- ✅ test_input_mediator.cpp - Mediator with mock driver
- ✅ test_tcp_driver.cpp - Protocol validation

### Integration Tests (Recommended)

```
[ ] Multi-client concurrent access
[ ] Rapid SIGINT/SIGTERM
[ ] Large buffer reads/writes
[ ] Malformed protocol messages
[ ] Memory exhaustion
[ ] Worker thread crash recovery
```

### Stress Tests (Recommended)

```
[ ] 100 concurrent clients
[ ] 1GB files
[ ] 10k requests/sec throughput
[ ] Handler timeout simulation
```

---

## Conclusion

**Strengths:**
- Clean architecture with good separation of concerns
- Proper thread safety for shared data
- Extensible design patterns
- Well-documented code

**Critical Issues:**
- Blocking I/O fundamentally incompatible with event-driven architecture
- No exception handling in critical paths
- Single-threaded at protocol level

**Before Production:**
1. Redesign I/O for async/non-blocking
2. Add exception handling
3. Add input validation
4. Add timeouts
5. Add resource limits

**Recommendation:** Safe for educational/prototype use; needs architectural changes for high-concurrency production use.
