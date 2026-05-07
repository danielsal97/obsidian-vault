# main() Wiring — What C++ Is Actually Doing

Every line of the LDS startup code has hidden mechanics. This note exposes them all.

---

## Current vs Target

This file explains two versions of `main()`:

| | Code | Status |
|---|---|---|
| **NOW** | Actual `app/LDS.cpp` today | Phase 1-alpha — running, single-threaded |
| **TARGET** | Full Phase 1–3 wiring | Future goal — Command pattern, RAID, UDP |

---

## Current Wiring (actual `app/LDS.cpp`)

```cpp
// app/LDS.cpp — what is actually compiled and running today

LocalStorage  storage(size);       // in-memory block storage
NBDDriverComm driver(device, size); // opens /dev/nbd0, sets disk size
Reactor       reactor;             // creates epoll fd

reactor.Add(driver.GetFD());       // register NBD fd with epoll
reactor.SetHandler([&](int fd) {   // one handler for all events
    auto request = driver.ReceiveRequest();

    switch (request->m_type) {
    case DriverData::READ:
        storage.Read(request);
        driver.SendReply(request);
        break;
    case DriverData::WRITE:
        storage.Write(request);
        driver.SendReply(request);
        break;
    case DriverData::FLUSH:
    case DriverData::TRIM:
        request->m_status = DriverData::SUCCESS;
        driver.SendReply(request);
        break;
    case DriverData::DISCONNECT:
        reactor.Stop();
        break;
    }
});

reactor.Run();  // blocks forever in epoll_wait loop
```

### What this does

- One thread handles everything — no thread pool, no queue
- `LocalStorage` is a plain in-memory buffer (no network, no RAID)
- Reactor API: `Add(fd)` registers the fd, `SetHandler(lambda)` sets the callback
- The lambda receives the fd that fired; `driver.GetFD()` is the NBD socketpair end
- `reactor.Stop()` sets `running_ = false`, breaking the `epoll_wait` loop on DISCONNECT

### What it is missing (compared to target)

| Missing | Why it matters |
|---------|----------------|
| `ThreadPool` / WPQ | All I/O is blocking; one slow minion stalls everything |
| `CommandFactory` | Switch/case must be edited to add new request types |
| `InputMediator` | No separation between "receive request" and "dispatch command" |
| `MinionProxy` / RAID | No network; data lives only in RAM, lost on restart |
| `Scheduler` / `ResponseManager` | No retry logic, no timeout tracking |

---

## Target Wiring (Phase 1–3 complete)

---

## The Full Target Code

```cpp
// Phase 1: Infrastructure
Logger&        logger   = Singleton<Logger>::GetInstance();
NBDDriverComm  driver("/dev/nbd0", DISK_SIZE);
Reactor        reactor;

// Phase 2: Storage + Network
RAID01Manager  raid;
raid.AddMinion(0, "192.168.1.10", 9000);
raid.AddMinion(1, "192.168.1.11", 9000);

ResponseManager response_mgr(MASTER_UDP_PORT);
Scheduler       scheduler(response_mgr);
MinionProxy     proxy(raid, scheduler);

// Phase 1: Command routing
auto& factory = Singleton<CommandFactory>::GetInstance();
factory.Add("READ",  [&](DriverData d){ return make_shared<ReadCommand>(d, raid, proxy, scheduler); });
factory.Add("WRITE", [&](DriverData d){ return make_shared<WriteCommand>(d, raid, proxy, scheduler); });
factory.Add("FLUSH", [&](DriverData d){ return make_shared<FlushCommand>(d); });

ThreadPool      pool(std::thread::hardware_concurrency());
InputMediator   mediator(pool, factory, driver);

// Phase 3: Reliability
Watchdog        watchdog(proxy, raid);
AutoDiscovery   discovery(raid);

// Start
reactor.Add(driver.GetFD());
reactor.SetHandler([&](int fd){ mediator.HandleEvent(fd); });
reactor.Run();
```

---

## Line by Line (Target Code)

The section below explains each line of the **target** wiring. Lines that don't yet exist in `app/LDS.cpp` are marked *(future)*.

---

### `Logger& logger = Singleton<Logger>::GetInstance();`

**What you see:** A variable being assigned.

**What C++ does:**

`Singleton<Logger>` is a **template class** — `<Logger>` tells the compiler "generate this class specifically for the `Logger` type." The compiler produces a concrete class with `Logger`-specific storage.

`::GetInstance()` is a **static method** — it belongs to the class, not any instance. Inside it:

```cpp
static T& getInstance() {
    static T instance;  // ← created ONCE, on first call only
    return instance;
}
```

The `static T instance` line is the key. C++ guarantees that a static local variable:
- Is constructed **exactly once**, the first time that line is reached
- Is **thread-safe** (C++11 onwards — the compiler inserts locking automatically)
- Lives until the **program ends**

`Logger& logger` is a **reference** — not a copy of the Logger, just another name for the same object. Zero overhead. The `&` means "refer to, don't copy."

**Mental model:** `GetInstance()` returns the address of a single Logger that lives in static memory. `logger` is just a label stuck on that address.

---

### `NBDDriverComm driver("/dev/nbd0", DISK_SIZE);`

**What you see:** A variable declaration with arguments.

**What C++ does:** Calls `NBDDriverComm::NBDDriverComm(const char*, size_t)` — the **constructor** — immediately. The constructor runs real work:

```cpp
NBDDriverComm::NBDDriverComm(const char* device, size_t size) {
    fd_ = open(device, O_RDWR);       // opens /dev/nbd0
    ioctl(fd_, NBD_SET_SIZE, size);    // tells kernel: disk is this big
    socketpair(AF_UNIX, SOCK_STREAM, 0, fds_);  // creates the kernel bridge
    // ...
}
```

`driver` is a **stack object** — it lives on main()'s stack frame. When `main()` exits (or throws), `~NBDDriverComm()` is called automatically. The destructor calls `ioctl(NBD_DISCONNECT)` and closes the fd. **You never call delete. RAII handles it.**

---

### `Reactor reactor;`

**What you see:** A variable with no arguments.

**What C++ does:** Calls the **default constructor** `Reactor::Reactor()`. Under the hood:

```cpp
Reactor::Reactor() {
    epfd_ = epoll_create1(0);   // asks the kernel for an epoll instance
}
```

One syscall. `epfd_` is a file descriptor representing the epoll watch list. Again — stack object, destructor closes `epfd_` automatically.

---

### `RAID01Manager raid;`

Default-constructs the mapping table — just initializes an empty `std::map<int, Minion>`. No network, no I/O. Pure in-memory data structure.

---

### `raid.AddMinion(0, "192.168.1.10", 9000);`

**What you see:** A method call.

**What C++ does:** Inserts into the internal map:

```cpp
void RAID01Manager::AddMinion(int id, const std::string& ip, int port) {
    minions_[id] = Minion{id, ip, port, Minion::HEALTHY, time(nullptr)};
}
```

The string `"192.168.1.10"` is a **C-string literal** that gets implicitly converted to `std::string` by its constructor. No explicit conversion needed — C++ calls the right constructor automatically.

---

### `ResponseManager response_mgr(MASTER_UDP_PORT);`

Constructor opens a UDP socket and binds it to the given port. It also **spawns a background thread** that loops on `recvfrom()`:

```cpp
ResponseManager::ResponseManager(int port) {
    sock_ = socket(AF_INET, SOCK_DGRAM, 0);
    bind(sock_, ...port...);
    recv_thread_ = std::thread([this]{ receiveLoop(); });  // starts immediately
}
```

**Hidden:** A thread is running the moment this line executes. You didn't call `start()` — the constructor did it. The thread runs `receiveLoop()` which blocks on `recvfrom()` waiting for UDP packets from minions.

---

### `Scheduler scheduler(response_mgr);`

**What you see:** `scheduler` takes `response_mgr`.

**What C++ does:** Stores a **reference** to `response_mgr`. The `&` in the constructor parameter means "don't copy, just hold the address":

```cpp
Scheduler::Scheduler(ResponseManager& rm) : response_mgr_(rm) {}
//                                 ↑                        ↑
//                           reference param          stored as reference member
```

`scheduler` does not own `response_mgr`. It just knows where it lives. This means **construction order matters** — `response_mgr` must be constructed before `scheduler`, otherwise `scheduler` holds a reference to garbage. The order in `main()` is not arbitrary.

---

### `MinionProxy proxy(raid, scheduler);`

Same pattern — stores references to `raid` and `scheduler`. Proxy can now call:
- `raid.GetBlockLocation(n)` — to find which minion to send to
- `scheduler.Track(msg_id, deadline)` — to register a timeout

No ownership. No copies. Just pointers dressed as references.

---

### `auto& factory = Singleton<CommandFactory>::GetInstance();`

`auto&` means "deduce the type and make it a reference." The compiler sees `GetInstance()` returns `CommandFactory&` so `factory` is `CommandFactory&`. Same Singleton mechanic as `Logger`.

---

### `factory.Add("READ", [&](DriverData d){ return make_shared<ReadCommand>(d, raid, proxy, scheduler); });`

This is the most C++-dense line. Breaking it apart:

**`[&]` — Lambda capture by reference**

```cpp
[&](DriverData d){ ... }
```

This creates an anonymous function object (a **lambda**). The `[&]` says: "capture everything in the surrounding scope by reference." That means the lambda silently holds references to `raid`, `proxy`, and `scheduler` from `main()`.

The lambda itself is an object of a hidden compiler-generated type — something like:

```cpp
struct __lambda_42 {
    RAID01Manager& raid;      // ← captured by [&]
    MinionProxy&   proxy;     // ← captured by [&]
    Scheduler&     scheduler; // ← captured by [&]

    shared_ptr<ICommand> operator()(DriverData d) {
        return make_shared<ReadCommand>(d, raid, proxy, scheduler);
    }
};
```

**`make_shared<ReadCommand>(...)`**

Allocates a `ReadCommand` on the heap with a reference count of 1. Returns a `shared_ptr<ReadCommand>` which implicitly converts to `shared_ptr<ICommand>` (because `ReadCommand` inherits from `ICommand`).

**What `factory.Add` stores:**

```cpp
void Factory::Add(const string& key, function<shared_ptr<ICommand>(DriverData)> creator) {
    table_[key] = creator;   // stores the lambda as a std::function
}
```

The lambda is stored inside a `std::function` — a type-erased callable wrapper. Later, when `factory.Create("READ", data)` is called, it looks up `"READ"` in the table and invokes the stored lambda. The lambda runs, calls `make_shared<ReadCommand>(...)`, and returns the new command.

**The hidden chain:**

```
NBD event fires
  → InputMediator reads "READ" from DriverData
  → factory.Create("READ", data)
  → looks up table_["READ"]
  → calls stored lambda(data)
  → lambda calls make_shared<ReadCommand>(data, raid, proxy, scheduler)
  → returns shared_ptr<ICommand>
  → pushed to WPQ
```

---

### `ThreadPool pool(std::thread::hardware_concurrency());`

`std::thread::hardware_concurrency()` queries the OS for the number of logical CPU cores (e.g. 8 on a quad-core with hyperthreading). The ThreadPool constructor spawns exactly that many worker threads, all blocking on the WPQ condition variable.

**Hidden:** 8 threads are now alive and sleeping. They'll wake the moment something is pushed to the WPQ.

---

### `InputMediator mediator(pool, factory, driver);`

Stores references to all three. The mediator's job is one method:

```cpp
void InputMediator::HandleEvent(int fd) {
    auto data = driver_.ReceiveRequest();    // read from NBD fd
    auto cmd  = factory_.Create(data->type, *data);  // make command
    pool_.Enqueue(cmd);                      // push to WPQ
}
```

It holds no state of its own — just wires pool, factory, and driver together.

---

### `Watchdog watchdog(proxy, raid);`

Constructor stores references AND **spawns a background thread**:

```cpp
Watchdog::Watchdog(MinionProxy& p, RAID01Manager& r) : proxy_(p), raid_(r) {
    thread_ = std::thread([this]{ healthLoop(); });
}
```

`healthLoop()` runs forever: ping each minion every 5 seconds, mark FAILED after 15 seconds of silence. **Running from the moment this line executes.**

---

### `reactor.Add(driver.GetFD());` + `reactor.SetHandler([&](int fd){ mediator.HandleEvent(fd); });`

These two calls wire the event loop to the mediator. They are separate because the Reactor has a single handler for all registered fds — there is no per-fd callback map.

**`reactor.Add(fd)`** registers the fd with epoll:

```cpp
void Reactor::Add(int fd) {
    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, fd, &ev);
}
```

**`reactor.SetHandler(lambda)`** stores the single dispatch function:

```cpp
void Reactor::SetHandler(std::function<void(int)> handler) {
    io_handler = handler;
}
```

When epoll fires, Reactor calls `io_handler(fd)` — passing which fd triggered. The lambda `[&](int fd){ mediator.HandleEvent(fd); }` captures `mediator` by reference and forwards the fd. `HandleEvent` reads the request from the NBD fd, creates the command, and enqueues it.

---

### `reactor.Run();`

**What you see:** One function call.

**What C++ does:** An infinite loop:

```cpp
void Reactor::Run() {
    while (running) {
        int n = epoll_wait(epoll_fd, events, MAX_EVENTS, -1);
        //                                               ↑ timeout = forever
        // blocks here with 0% CPU until an fd fires

        for (int i = 0; i < n; i++) {
            int fd = events[i].data.fd;
            io_handler(fd);   // call the single registered handler
        }
    }
}
```

This line never returns (until `running_` is set to false by a signal). The entire program's execution lives inside this loop.

---

## The Hidden Destruction Order

When `reactor.Run()` finally returns (on SIGINT/SIGTERM), `main()` exits. **All stack objects are destroyed in reverse order of construction** — this is guaranteed by C++:

```
discovery   destroyed  → stops UDP broadcast listener
watchdog    destroyed  → stops health-check thread (joins it)
mediator    destroyed  → (nothing to clean up)
pool        destroyed  → signals workers to stop, joins all threads
factory     destroyed  → (Singleton — lives until program end)
proxy       destroyed  → closes UDP send socket
scheduler   destroyed  → stops timeout thread
response_mgr destroyed → stops recv thread, closes UDP socket
raid        destroyed  → frees minion map
reactor     destroyed  → closes epfd_
driver      destroyed  → ioctl(NBD_DISCONNECT), closes socketpair
logger      destroyed  → (Singleton — lives until program end)
```

**You wrote zero cleanup code.** Every destructor fires automatically in the right order because of RAII + stack unwinding.

---

## Why Construction Order Matters

```cpp
Scheduler scheduler(response_mgr);   // ✅ response_mgr exists
MinionProxy proxy(raid, scheduler);   // ✅ raid and scheduler exist

// If you swapped them:
MinionProxy proxy(raid, scheduler);   // ❌ scheduler doesn't exist yet — undefined behavior
Scheduler scheduler(response_mgr);
```

The compiler does not check this for you. Construction order in `main()` is your responsibility.

---

## Summary of Hidden Mechanics

| Line | Hidden C++ mechanic |
|------|---------------------|
| `Singleton<T>::GetInstance()` | Template instantiation + static local (constructed once, thread-safe) |
| `NBDDriverComm driver(...)` | Constructor runs OS syscalls; destructor cleans up automatically |
| `Logger& logger` | Reference — no copy, just an alias |
| `ResponseManager response_mgr(...)` | Constructor spawns a background thread |
| `Scheduler scheduler(response_mgr)` | Stores a reference — order of construction matters |
| `[&](DriverData d){...}` | Lambda closure — captures surrounding variables by reference |
| `make_shared<ReadCommand>(...)` | Heap allocation with reference counting |
| `factory.Add("READ", lambda)` | Stores lambda inside `std::function` (type erasure) |
| `hardware_concurrency()` | OS query for CPU core count |
| `reactor.Add(fd)` | Registers fd with epoll — separate from setting the handler |
| `reactor.SetHandler(lambda)` | Single handler called for all registered fds; receives which fd fired |
| `reactor.Run()` | Infinite `epoll_wait` loop — never returns until `Stop()` is called |
| `main()` exits | All stack objects destroyed in reverse order automatically |

## Related
- [[Glossary/RAII]] — why destructors clean up automatically
- [[Glossary/shared_ptr]] — make_shared and reference counting
- [[Glossary/Templates]] — how Singleton<T> and Factory<T> work
- [[Glossary/WPQ]] — what happens after pool.Enqueue()
- [[Glossary/epoll]] — what reactor.Run() is actually doing
- [[Request Lifecycle]] — the full journey of one NBD request through this wiring
