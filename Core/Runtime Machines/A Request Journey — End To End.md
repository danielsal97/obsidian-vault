# A Request Journey — End To End

One read request. From the moment a client calls read() to the moment bytes land in its buffer.

Every layer of the system — Hardware, OS, Networking, Concurrency, C++, Design Patterns, LDS — is touched exactly once, in the order runtime touches it.

This is not a list of concepts. This is a walk through a live machine.

→ [[01 - LDS System — The Machine]] — LDS-specific pipeline diagram
→ [[00 - Traversal Paths]] — shorter focused walks per subsystem
→ [[Linux Runtime — The Machine]] — all subsystems simultaneously

---

## The Setup

**Client**: a program (or Mac-side BlockClient) that wants to read 512 bytes at block offset 0 from LDS.
**Server**: LDS master process, running on Linux, already listening on TCP port.
**State**: TCP connection between client and server is already established. The Reactor is idle in `epoll_wait()`.

---

## Step 1 — Client: Application crosses the user/kernel boundary

```
BlockClient::Read(offset=0, len=512)
  build request frame: [4-byte length][1-byte type=READ][8-byte offset][4-byte len]
  write(tcp_fd, frame, 17)          ← syscall: user mode → kernel mode
```

**What happens at the syscall**: CPU executes `syscall` instruction. Hardware switches from ring 3 (user) to ring 0 (kernel) in ~100ns. Registers saved on kernel stack. Kernel `sys_write()` handler runs. The calling thread is blocked — it will not return from `write()` until the kernel copies the 17 bytes to the socket send buffer.

**Why this boundary exists**: without the kernel/user separation, any application could corrupt another process's memory or bypass network security. The syscall is the enforced interface — the only door into the kernel.

Latency: ~100ns (syscall overhead)

→ [[Linux Runtime — The Machine]] § user/kernel boundary
→ [[02 - File Descriptors — The Machine]]

---

## Step 2 — Client Kernel: TCP builds and sends a segment

```
kernel (client side, after sys_write returns bytes to send buffer):
  TCP:
    segment into MSS-sized chunk (17 bytes << 1460 byte MSS — one segment)
    attach TCP header: src_port=50001, dst_port=9000, seq=N, ACK=M, flags=PSH|ACK
    compute TCP checksum (covers header + payload)
  IP:
    attach IP header: TTL=64, proto=TCP, src=192.168.1.10, dst=192.168.1.20
    compute IP checksum
  Ethernet:
    ARP lookup for dst IP → get destination MAC address
    attach Ethernet header: src_mac, dst_mac, ethertype=IPv4
  NIC driver:
    write frame pointer + length into TX ring descriptor
    write TX doorbell register: "new descriptor ready"
```

**Why TCP here**: LDS block data has zero tolerance for silent corruption. A lost byte corrupts a filesystem. TCP's retransmit, ordering, and checksum guarantee reliable delivery. (Contrast: LDS uses UDP for minion writes because the application controls retry — TCP's blind retransmit would create unpredictable I/O latency.)

Latency: ~1–2μs (TCP/IP stack processing)

→ [[02 - TCP Sockets — The Machine]]

---

## Step 3 — Client NIC: DMA transmit (CPU not involved)

```
NIC hardware (independent of CPU):
  DMA engine reads TX ring descriptor: finds frame address + length
  DMA: copies Ethernet frame from kernel TX ring buffer → NIC hardware queue
  NIC serializes bits onto the wire at line rate (e.g. 1Gbps)
  NIC raises TX-complete interrupt: "ring slot is now free, reuse it"
```

**Why DMA exists**: without it, the CPU must copy every byte from kernel memory to NIC hardware registers. At 1Gbps that's 125MB/s of copying — wasting a full CPU core on data movement. DMA offloads all data movement to the NIC's on-board engine. The CPU writes one descriptor pointer, then is completely free while the NIC transmits.

Latency: ~5–50μs (DMA copy + serialization + wire propagation)

→ [[Networking Stack — The Machine]] § DMA

---

## Step 4 — Server NIC: Frame arrives, DMA into kernel

```
Server NIC hardware:
  Ethernet frame received from wire
  NIC verifies Ethernet FCS (frame check sequence) — drop frame if corrupted
  DMA engine: writes frame bytes → pre-allocated kernel RX ring buffer page
  NIC raises hardware interrupt: "frame available in RX ring slot N"
```

The LDS server's CPU was either idle in `epoll_wait()` or running other work. The interrupt fires on whichever CPU core the NIC is affinitized to, pausing that core's current execution.

Latency: ~5–20μs (DMA fill + interrupt delivery)

---

## Step 5 — Server Kernel: Interrupt → softirq → TCP → epoll

```
[Hard interrupt context — ~microseconds, IRQs disabled, cannot sleep]
  IRQ handler: read NIC interrupt status register
               clear interrupt (write NIC register: "I saw this")
               schedule NET_RX_SOFTIRQ: flag this CPU for deferred processing
               return from interrupt — original thread resumes on this CPU

[Softirq context — runs shortly after, IRQs re-enabled, can be preempted]
  ksoftirqd / NAPI poll loop:
    pull frame from RX ring buffer
    Ethernet layer: strip 14-byte header, identify ethertype=IPv4
    IP layer: verify IP checksum, TTL check, routing (local destination)
    TCP layer:
      verify TCP checksum
      socket lookup: hash table on (src_ip=10, src_port=50001, dst_ip=20, dst_port=9000)
      → finds LDS's accepted socket
      verify seq number is in-window
      append 17-byte payload to socket receive buffer (sk_buff chain)
      update TCP receive window (announce more space to peer)
      schedule deferred ACK (will be sent piggyback or standalone)

    socket is now readable:
      → epoll subsystem: socket fd already registered in LDS's epoll instance
      → add socket fd to epoll ready list (O(1): fd is already in the rbtree)
      → wake any task sleeping in epoll_wait() on this epoll instance
```

**Why softirq**: TCP processing must happen but can't run in hard interrupt context (IRQs disabled for too long, no sleeping, no allocation). Softirq gives TCP a deferred context: IRQs re-enabled, preemptible by higher-priority work, batched with NAPI to handle many frames per softirq invocation.

Latency: ~10–50μs (protocol stack processing)

→ [[Networking Stack — The Machine]] § softirq
→ [[04 - epoll — The Machine]]

---

## Step 6 — Server: Context switch to Reactor thread

```
[Scheduler: Reactor thread was sleeping in FUTEX_WAIT inside epoll_wait()]
  softirq's wakeup marks Reactor thread as TASK_RUNNING
  CFS run queue: Reactor thread added with its current vruntime
  Scheduler picks Reactor thread (it has low vruntime — was sleeping, deserves CPU)

[Context switch]:
  save current thread's registers (RSP, RIP, general-purpose registers, FPU state)
  load Reactor thread's saved registers
  CR3 register: UNCHANGED — same process = same page tables = TLB NOT flushed
  Reactor thread resumes execution exactly at the epoll_wait() return point

epoll_wait() returns:
  n=1, events[0] = {fd=tcp_client_fd, events=EPOLLIN}
```

**Why CR3 unchanged**: context switching between threads of the same process does NOT flush the TLB (no CR3 change). All the Reactor's hot code and data structures are still in TLB and L1 cache. The switch costs ~2–10μs for register save/restore — not the extra 100–500μs of a cold TLB.

Latency: ~2–10μs (context switch)

→ [[10 - Context Switch — The Machine]]
→ [[11 - Scheduler — The Machine]]

---

## Step 7 — Server: Reactor dispatches to handler

```
Reactor::Run():
  for each event in epoll_wait() results:
    handler = m_handlers.Find(event.fd)    ← O(1) hash map lookup
    handler->OnReadable(event.fd)
    // does NOT read the data itself — that's the handler's job
```

```
TCPDriverComm::OnReadable(fd):
  ReadAll(fd, header_buf, 17)      ← recv() in a loop until all 17 bytes received
  // kernel: copies 17 bytes from socket receive buffer → header_buf
  parse: type=READ, offset=0, len=512, handle=0xABCD1234
```

**Why the Reactor doesn't read data directly**: the Reactor's ONLY job is dispatching. Each handler knows the protocol for its fd — the NBD handler parses NBD binary frames, the TCP handler parses the wire protocol, the inotify handler reads filesystem events. Reactor doesn't know any of this.

**Why ReadAll loops**: TCP is a byte stream. `recv()` may return fewer bytes than requested if the socket buffer partially filled. ReadAll loops until all `n` bytes are received. This is a fundamental TCP property — there are no message boundaries in the stream.

Latency: recv() copy ~100ns for 17 bytes

→ [[03 - Reactor — The Machine]]
→ [[01 - Reactor Pattern — The Machine]]
→ [[02 - TCP Sockets — The Machine]] § RecvAll

---

## Step 8 — Server: InputMediator creates a Command and enqueues it

```
InputMediator::OnReadableEvent(DriverData{READ, offset=0, len=512, handle=0xABCD1234}):
  
  cmd = Factory::GetInstance()->Create("ReadCommand", data)
  // Factory: looks up creator function in registry by key "ReadCommand"
  // returns unique_ptr<ICommand> — heap allocation of ReadCommand object
  
  m_threadpool.Push(std::move(cmd), Priority::HIGH)
  // std::move: O(1) transfer of unique_ptr — no copy of ReadCommand
  // WPQ.Push: lock mutex (futex fast path ~5ns), push to High lane, unlock, notify_one()
  
  return   ← Reactor thread returns to epoll_wait() in < 1μs
```

**Why Command pattern**: the Reactor thread must NEVER block. Creating a Command and pushing it to a queue is O(1) non-blocking. The actual storage I/O — which may take milliseconds if a minion is slow — runs on a worker thread. The Reactor is free in < 1μs.

**Why std::move here**: `cmd` is a `unique_ptr<ICommand>`. Moving it transfers ownership to the WPQ in O(1) — no copy of the ReadCommand object, no second heap allocation. RAII ensures the Command is destroyed exactly once, by whichever object last holds the pointer.

Latency: < 1μs (Factory lookup + move + futex push)

→ [[10 - InputMediator — The Machine]]
→ [[05 - Command Pattern — The Machine]]
→ [[04 - Factory Pattern — The Machine]]

---

## Step 9 — Server: Worker thread wakes via futex

```
[Worker thread was sleeping in condition_variable::wait()]
  WPQ::Push() calls cv.notify_one()
  → FUTEX_WAKE(futex_addr, 1): kernel marks one waiting worker as TASK_RUNNING
  → scheduler picks this worker on an available CPU core
  → context switch: save sleeping thread → load worker thread
  
Worker::Run():
  cmd = WPQ.Pop()    ← lock mutex, pop from HIGH lane (READ), unlock
  cmd->Execute()
```

**Why futex here and not a kernel semaphore**: the WPQ mutex is acquired/released thousands of times per second. A pure kernel semaphore would syscall on every lock/unlock: ~100–200ns each. Futex: uncontested lock = single atomic CAS in userspace, ~5ns. Kernel only called when a thread actually needs to sleep (FUTEX_WAIT) or wake (FUTEX_WAKE). At 10,000 enqueues/sec: futex = 50μs/sec overhead, kernel semaphore = 2,000μs/sec.

Latency: ~5–20μs (futex wake + context switch to worker)

→ [[04 - ThreadPool and WPQ — The Machine]]
→ [[01 - Multithreading Patterns — The Machine]]

---

## Step 10 — Server: ReadCommand executes (business logic)

```
ReadCommand::Execute():

  // Phase 1 — in-memory local storage:
  LocalStorage::Read(offset=0, len=512, out_buf)
  → memcpy from m_storage.data() + 0 → out_buf, 512 bytes
  // Pure userspace DRAM access. If hot in cache: ~50ns. Cold: ~500ns.
  
  // Phase 2+ — distributed RAID:
  RAID01Manager::GetBlockLocation(block_num=0)
  → returns {minionA=192.168.1.100, minionB=192.168.1.101}
  MinionProxy::Read(minionA, 0, 512)
  → sendto(udp_fd, read_request, ...)   // UDP: no connection, no ACK
  ResponseManager::Wait(handle, timeout=100ms)
  → blocks worker thread until UDP reply arrives with 512 bytes
```

**Phase 2 note**: the worker thread blocking on `ResponseManager::Wait()` is fine — the Reactor thread and all other workers continue running. Blocking one worker for 100ms UDP timeout has zero effect on other requests.

Latency: Phase 1: ~50–500ns (memcpy). Phase 2: ~100μs–1ms (UDP round trip to minion)

→ [[06 - LocalStorage — The Machine]]
→ [[09 - RAID01Manager — The Machine]]

---

## Step 11 — Server: Reply sent back to client

```
ReadCommand::Execute() continued:
  IDriverComm::SendReply(handle=0xABCD1234, buf=out_buf, len=512)

TCPDriverComm::SendReply():
  frame = [4-byte length][1-byte type=REPLY][8-byte handle][512 bytes data]
  WriteAll(tcp_client_fd, frame, 525)
  → write(fd, frame, 525) syscall
  → kernel: copy 525 bytes from userspace → socket send buffer
  → TCP: segment (one segment, 525 bytes << MSS=1460)
        set seq=M, ACK=N+17 (acknowledge client's request)
        check send window (open — client is ready)
  → NIC driver: TX ring descriptor, doorbell write
  → NIC DMA: transmits frame to client
```

Latency: ~1–50μs (syscall + TCP stack + NIC DMA)

→ [[08 - TCPDriverComm — The Machine]]

---

## Step 12 — Client: Receives reply, returns to application

```
Client kernel TCP (softirq):
  reply frame arrives → NIC DMA → RX ring → interrupt → softirq
  TCP: validate checksum, seq number in-window
  append 525 bytes to client socket receive buffer
  client's read() or recv() was blocking — wake the blocked thread

Client BlockClient::Read():
  ReadAll(tcp_fd, reply_buf, 525)    ← returns with 525 bytes
  parse frame: verify handle=0xABCD1234 matches pending request
  copy 512 data bytes → caller's buffer
  return   ← application's read() call completes
```

The application's blocking call — which started in Step 1 — returns. 512 bytes of data are in the application's buffer. The full round-trip is complete.

---

## The Full Latency Budget

| Step | What | Typical |
|---|---|---|
| 1 | syscall (user → kernel) | ~100ns |
| 2 | TCP/IP stack, client side | ~2μs |
| 3 | Client NIC DMA + wire | ~10–50μs |
| 4 | Server NIC DMA + interrupt | ~5–20μs |
| 5 | softirq: Ethernet→IP→TCP→epoll | ~10–50μs |
| 6 | Context switch to Reactor | ~2–10μs |
| 7 | Reactor dispatch + ReadAll | < 1μs |
| 8 | InputMediator + WPQ enqueue | < 1μs |
| 9 | futex wake + context switch to worker | ~5–20μs |
| 10a | LocalStorage memcpy (Phase 1) | ~50–500ns |
| 10b | UDP minion round trip (Phase 2) | ~100μs–1ms |
| 11 | Reply TCP + NIC DMA transmit | ~10–50μs |
| 12 | Client receive + parse | ~10–50μs |
| **Total Phase 1** | **LAN, local memory** | **~100–300μs** |
| **Total Phase 2** | **LAN, distributed** | **~500μs–5ms** |

---

## Every Concept This Journey Touches

| Concept | Where in Journey | Note |
|---|---|---|
| syscall / user-kernel boundary | Steps 1, 11, 12 | [[Linux Runtime — The Machine]] |
| TCP reliable stream | Steps 2, 5, 7, 11 | [[02 - TCP Sockets — The Machine]] |
| DMA (NIC → kernel ring) | Steps 3, 4 | [[Networking Stack — The Machine]] |
| Hardware interrupt | Step 4 | [[Networking Stack — The Machine]] |
| softirq / NAPI | Step 5 | [[Networking Stack — The Machine]] |
| epoll ready list | Step 5 | [[04 - epoll — The Machine]] |
| Context switch | Steps 6, 9 | [[10 - Context Switch — The Machine]] |
| CFS scheduler | Steps 6, 9 | [[11 - Scheduler — The Machine]] |
| TLB (not flushed on thread switch) | Step 6 | [[07 - TLB — The Machine]] |
| Reactor pattern | Step 7 | [[01 - Reactor Pattern — The Machine]] |
| RAII / unique_ptr | Step 8 | [[01 - RAII — The Machine]] |
| Move semantics | Step 8 | [[21 - Move Semantics — The Machine (deep)]] |
| Factory pattern | Step 8 | [[04 - Factory Pattern — The Machine]] |
| Command pattern | Steps 8–10 | [[05 - Command Pattern — The Machine]] |
| futex | Step 9 | [[01 - Multithreading Patterns — The Machine]] |
| ThreadPool + WPQ | Steps 8–10 | [[04 - ThreadPool and WPQ — The Machine]] |
| LocalStorage / RAID | Step 10 | [[06 - LocalStorage — The Machine]], [[09 - RAID01Manager — The Machine]] |
| RecvAll / WriteAll loops | Steps 7, 12 | [[02 - TCP Sockets — The Machine]] |
| LDS full pipeline | All steps | [[02 - Request Lifecycle — The Machine]] |
