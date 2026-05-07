# Interview Guide — Present This Project Professionally

## The 3-Minute Pitch

### Opening (30 sec) — What it is
> "I built a userspace NBD server — Network Block Device. The Linux kernel treats `/dev/nbd0` as a real disk, but all I/O goes to our process via a Unix socket pair. We receive structured `nbd_request` packets, process them in-memory, and send `nbd_reply` packets back. The interesting part is that from the user's perspective it's a completely transparent block device — you can format it, mount it, run `cp` on it."

### Core flow (60 sec) — How it works
> "The kernel writes requests to one end of a `socketpair`. Our `NBDDriverComm` reads from the other end with `ReceiveRequest()`, which decodes the binary NBD protocol into a `DriverData` object containing the action type, byte offset, length, and data buffer. A Reactor using `epoll` dispatches these requests to `LocalStorage`, which reads or writes from an in-memory vector. We reply to the kernel via `SendReplay()`. The Reactor uses `epoll` so a single thread handles all events without polling — it wakes only when the kernel sends data."

### What's interesting (60 sec) — Design decisions
> "We have a dedicated listener thread blocked in `ioctl(NBD_DO_IT)` — that's a kernel call that never returns until disconnect. It can't be on the main thread or the program would hang. The Reactor watches the server FD with `epoll` and drives the main request loop. Signal handling uses `signalfd` — signals become readable file descriptor events that `epoll` can monitor, no async interrupts."
>
> "The plugin system hot-loads `.so` files: drop one into a watched directory, `inotify` fires `IN_CLOSE_WRITE` (after full write, not just file creation), `DirMonitor` notifies `SoLoader` via the Observer pattern, `SoLoader` calls `dlopen`, and the plugin's constructor attribute fires — which self-registers into the global Factory singleton. No restart needed."

### Patterns (30 sec)
> "The project exercises Singleton with double-checked locking and memory ordering guarantees, Factory for runtime plugin registration, Observer/Dispatcher for event propagation with RAII auto-registration, Command for prioritized task queuing, and Reactor for I/O multiplexing."

---

## Key Questions You Must Answer Cold

### System Level

| Question | Answer |
|---|---|
| What is a userspace block device? | `/dev/nbd0` looks like a real disk to the kernel, but all I/O is forwarded to our process over a socket |
| Why `socketpair` not `pipe`? | NBD kernel driver requires a socket FD for `NBD_SET_SOCK`. Socketpair is bidirectional, AF_UNIX, avoids TCP stack |
| Why listener thread? | `ioctl(NBD_DO_IT)` blocks forever in the kernel. Cannot be on main thread |
| What does `ioctl(NBD_DO_IT)` do? | Tells kernel to start forwarding I/O over the socket; blocks until disconnect |
| Why `sigfillset` in listener thread? | Any signal interrupts `ioctl` with EINTR, aborting the kernel relay loop. Must block ALL signals |
| What is `m_handle`? | Opaque bytes from kernel request; copied unchanged to reply; kernel matches async responses by this ID |
| Why `ReadAll`/`WriteAll` loop? | Sockets deliver partial data; must loop until all bytes transferred |
| What is `signalfd`? | Linux: converts signals to readable FD events; integrates with `epoll`. No async callbacks, no signal safety restrictions |

### Design Patterns

| Question | Answer |
|---|---|
| What is double-checked locking? | `load(acquire)` → if null → lock → check again → create → `store(release)` |
| Why `acquire` on first load? | Pairs with `release` store; guarantees object construction writes visible before pointer is readable |
| Why second check inside lock? | Between null-check and lock, another thread may have created the instance |
| Why `unique_ptr` in Singleton? | Owns the instance, destroys it at exit. Raw pointer would need explicit delete |
| Why Factory has private ctor? | Forces use of `Singleton<Factory>::GetInstance()` — exactly one global instance |
| What is `ICallBack` vs `CallBack`? | `ICallBack` = interface + RAII registration/unregistration. `CallBack` = concrete, binds subscriber + method pointer |
| What happens when ICallBack destroyed? | Destructor calls `m_disp->UnRegister(this)` — auto-cleanup |
| How does CallBack bind a method? | Stores `void (Sub::*)(const Msg&)`. Calls: `(m_sub.*m_actFunc)(msg)` |
| EPOLLIN level vs edge triggered? | Level-triggered: notifies while data available. Edge-triggered: only on state transition. LT is simpler, correct here |

### Plugin System

| Question | Answer |
|---|---|
| What is `inotify`? | Linux kernel subsystem. Register for filesystem events on paths. Events arrive via readable FD |
| Why `IN_CLOSE_WRITE` not `IN_CREATE`? | `IN_CREATE` fires before writing — file is empty. `IN_CLOSE_WRITE` fires after last write and close — safe to `dlopen` |
| What is `__attribute__((constructor))`? | Runs automatically on `dlopen`, before any code explicitly calls the library |
| How does plugin self-register? | Constructor attribute calls `Singleton<Factory>::GetInstance()->Add("key", creator)` |
| What is `RTLD_LAZY`? | Defer symbol resolution until first call (faster load) |
| What is `RTLD_DEEPBIND`? | `.so` resolves its own symbols against its own exports first — prevents name collision with host process |
| What does Loader destructor do? | Calls `dlclose(handle)` — decrements ref count; unmaps library when 0 |

### Threading

| Question | Answer |
|---|---|
| What happens on empty WPQ Pop()? | Blocks on `condition_variable` until `Push()` calls `notify_one()` |
| Why `Resume()` before StopCommands? | Suspended threads can't reach Pop(). Must wake them first so they can receive the stop signal |
| Why StopCommands Low priority? | Finish all pending work first, then stop. Graceful ordered shutdown |
| Why SuspendCommands High priority? | Must preempt queue immediately. Responsive suspension |
| What is spurious wakeup? | `cv.wait` wakes without `notify`. Predicate form re-checks and sleeps again if false |
| How many StopCommands? | Exactly one per worker thread — each picks one up and exits |

---

## Bugs That Show Senior Understanding

Mention 2-3 of these proactively to signal senior level:

1. **Bounds check missing length** — `offset > size` should be `offset + length > size`
2. **No error reply to kernel** — if storage throws, kernel I/O hangs forever
3. **Dispatcher not thread-safe** — concurrent `NotifyAll` + `Register` = use-after-free on vector reallocation
4. **Static mutex/cv in ThreadPool** — two ThreadPool instances share the same condition_variable

---

## How to Present the Architecture

Draw this while speaking:

```
/dev/nbd0 (kernel)
    │ socket
    ▼
NBDDriverComm
    │ DriverData
    ▼
Reactor (epoll)
    │
    ▼
LocalStorage (vector<char>)

Plugin system (independent):
DirMonitor → Dispatcher → SoLoader → dlopen → Factory
```

---

## Related Notes
- [[Known Bugs]]
- [[Threading Deep Dive]]
- [[Singleton Memory Model]]
- [[System Overview]]
- [[NBD Layer]]

---

## Deep-Dive Interview Prep Sheets

Full question-and-answer coverage for each topic area:

- [[Engineering/Interview - C++ Language]] — Stack/heap, RAII, smart pointers, move semantics, virtual functions, templates, const, nullptr
- [[Engineering/Interview - Concurrency]] — Mutex types, lock_guard vs unique_lock, race conditions (Bugs #8 and #10), condition variables, spurious wakeup, deadlock, atomic, memory ordering, producer-consumer
- [[Engineering/Interview - Linux & Networking]] — fork/exec/wait, signals (sigaction, signalfd, sig_atomic_t), epoll vs select vs poll, TCP socket API, RecvAll framing, byte ordering, UDP vs TCP, inotify, mmap, file descriptors
- [[Engineering/Interview - Data Structures]] — Every structure built in ds/, Big-O table, why heap PQ for Scheduler, hash table internals, binary trie for DHCP, UID design, circular buffer wrap-around, amortised analysis, FSA vs malloc
