# NVIDIA Firmware Engineer — Interview Prep

**Role**: NIC Firmware Core team — C layer between HW and FW, C++ OOP verification environment, networking adapter core features.

---

## Level 0 — What NVIDIA Is Testing

```
 ┌─ C Firmware ──── register programming · MMIO · interrupt handling · DMA descriptors
 │
 ├─ C++ OOP ──────── classes · RAII · smart pointers · templates · design patterns
 │
 ├─ NIC Architecture ─ packet path: host → PCIe → DMA engine → RX ring → driver → socket
 │
 ├─ Linux ────────── kernel driver model · interrupt handlers · memory-mapped I/O · sysfs
 │
 └─ Systems Thinking ─ latency vs. throughput · DMA coherency · firmware/driver interface
```

Your LDS project covers everything in the right two columns directly. The NIC internals column is adjacent — your epoll/UDP/TCP work is the driver-side endpoint of exactly this path.

---

## Level 1 — Map Your Knowledge to the Role

| NVIDIA Requirement | Your LDS Evidence | Gap? |
|---|---|---|
| C for HW/FW interface | LDS: socketpair binary protocol, `nbd_request` struct packing | Minor: no MMIO yet |
| C++ OOP | LDS: RAII, `unique_ptr`, templates, Singleton, Factory, Observer, Reactor | None |
| Networking adapters | LDS: epoll Reactor, UDP/TCP socket layer, DMA path via [[Networking Stack — The Machine]] | Minor: NIC internals |
| Linux driver model | LDS: `ioctl(NBD_DO_IT)`, inotify, signalfd, epoll — all kernel interfaces | Minor: no kernel module |
| Embedded C / register access | Closest: `sigfillset`, socketpair flags, raw struct packing | Gap: MMIO/PCIe registers |
| Debugging firmware | LDS: GDB experience, race condition debugging, memory ordering bugs | Strong |

---

## Level 2 — The 3-Minute Pitch (NVIDIA framing)

### Opening — What you built
> "I built a userspace block device server in C++ targeting Linux. The kernel treats `/dev/nbd0` as a real disk — all I/O flows through a socket pair to our process, which decodes binary `nbd_request` structs, processes them, and sends binary `nbd_reply` packets back. The interface is similar in spirit to a NIC firmware's datapath: structured binary protocol over a kernel-managed channel, with strict alignment and byte-ordering requirements."

### Core Design — Why it maps to firmware work
> "The architecture is a Reactor using epoll — one thread multiplexes all I/O events without polling. This is the same event-driven model that NIC firmware uses internally: interrupt fires, interrupt handler posts work to a queue, worker processes descriptor rings. Our ThreadPool with a priority work queue mirrors the firmware's interrupt priority scheme: Admin > High > Medium lanes. Workers share no state except the queue — no locking on the hot path."

### Systems Depth — Where you went deep
> "We handle the full NIC-to-application packet path in reverse: my [[Networking Stack — The Machine]] note walks NIC DMA → softirq → socket buffer → epoll ready list → recv(). I can describe every step: DMA ring descriptors, RX/TX queue management, kernel softirq coalescing, and how epoll_wait() surfaces the event to userspace. Signal handling uses `signalfd` so signals arrive as readable fd events — no async-signal-safety restrictions, same discipline firmware uses to serialize interrupt contexts."

---

## Level 3 — Technical Deep Dives

### NIC Architecture (the path NVIDIA owns)

```
Host Memory                   NIC
────────────                  ────────────────────────────
TX ring (descriptors) ──PCIe──▶ DMA engine fetches buffers
                               ▼
                          TX packet processing
                          (checksums, VLAN, segmentation)
                               ▼
                          Physical wire

Wire ──────────────────────────▶ RX packet processing
                               ▼
                          DMA engine fills RX ring
                               ▼
RX ring (descriptors) ◀──PCIe── interrupt to host
                               ▼
softirq → NAPI poll → socket buffer → epoll → recv()
```

**Your entry point in this diagram**: everything from "interrupt to host" rightward — that's exactly what LDS's Reactor handles via epoll.

**NVIDIA's firmware owns**: DMA engine, TX/RX processing, descriptor management, PCIe BAR register programming.

### DMA Descriptors (what firmware programs)

A TX descriptor tells the DMA engine where to find the packet:

```c
struct tx_desc {
    uint64_t buf_addr;     // host physical address (DMA-mapped)
    uint16_t len;          // bytes to transmit
    uint16_t flags;        // OWNER bit: 0=SW, 1=HW
    uint32_t vlan_tag;
};
```

Key firmware discipline:
- Write descriptor fields **before** setting OWNER bit — memory barrier required
- After OWNER=1, host cannot touch the descriptor until NIC clears it
- Same discipline as your Singleton's `store(release)`: write data before the pointer that signals readiness

### MMIO / Register Programming

```c
// Map PCIe BAR into virtual address space
volatile uint32_t *bar = (volatile uint32_t *)mmap(
    NULL, BAR_SIZE, PROT_READ | PROT_WRITE,
    MAP_SHARED, dev_fd, 0);

// Write control register — volatile prevents compiler reorder
bar[REG_TX_CTRL] = TX_ENABLE | TX_START;

// Hardware memory barrier before kicking doorbell
__sync_synchronize();   // mfence equivalent
bar[REG_TX_DOORBELL] = tx_tail_ptr;
```

**Connect to your knowledge**: `volatile` here serves the same role as `memory_order_release` in your Singleton — prevents the compiler from reordering writes to shared state that hardware observes.

### Interrupt Handling (Linux kernel side)

```c
static irqreturn_t nic_irq_handler(int irq, void *dev_id)
{
    struct nic_dev *dev = dev_id;
    uint32_t status = readl(dev->bar + INT_STATUS);

    if (status & RX_INT) {
        napi_schedule(&dev->napi);   // defer to softirq
        writel(RX_INT, dev->bar + INT_CLEAR);
    }
    return IRQ_HANDLED;
}
```

**Connect to your knowledge**: `napi_schedule` is the kernel equivalent of your `Reactor` posting a work item to the `ThreadPool`. The interrupt handler does minimal work (read status, clear interrupt, schedule) — your epoll handler does the same: fd ready → enqueue Command → return.

---

## Level 4 — Expected Questions and Answers

### C / Firmware

| Question | Answer |
|---|---|
| What is a memory-mapped register? | A hardware register exposed at a physical address, mapped into virtual address space via mmap/ioremap. CPU reads/writes translate to PCIe transactions |
| Why `volatile` for MMIO? | Compiler must not cache the value or reorder accesses — hardware state changes independently of CPU |
| What is a memory barrier in firmware? | CPU instruction (mfence/DMB) preventing reorder across the barrier. Required before writing a doorbell after descriptor setup |
| What is a DMA descriptor ring? | Circular buffer of fixed-size descriptors in host memory. SW writes descriptors, sets OWNER=HW; NIC processes and sets OWNER=SW; tail/head pointers track position |
| What is cache coherency and why does it matter for DMA? | DMA writes to physical memory, bypassing CPU cache. CPU may see stale cache line. Either flush/invalidate caches or use non-cacheable DMA memory |
| What is a PCIe BAR? | Base Address Register — firmware programs these to tell the OS where to map the NIC's register space |
| What is IOMMU? | Maps device-visible DMA addresses to physical memory, preventing DMA attacks and bad firmware from accessing arbitrary host memory |

### C++ / OOP (your strongest area)

| Question | Answer |
|---|---|
| Why RAII in a firmware verification environment? | Same reason as LDS: destructor fires even on exception/early return — resource handles, test fixtures, register snapshots all cleaned up deterministically |
| When would you use `unique_ptr` vs raw pointer in test infrastructure? | `unique_ptr` for owned resources, raw pointer for non-owning views. Rule of zero: if a class uses smart pointers, no manual destructor needed |
| What is the Rule of Five? | If you define any of: destructor, copy ctor, copy assign, move ctor, move assign — define all five |
| What is double-checked locking? | Acquire-load to check → if null, lock, check again, construct, release-store. Used in LDS Singleton |
| How would you design a test harness for a NIC register interface? | Strategy pattern: `IRegisterAccess` interface — one impl hits real MMIO, one records writes for replay, one simulates expected register state. Factory selects at runtime |

### Linux / Kernel

| Question | Answer |
|---|---|
| What is the difference between `epoll`, `select`, and `poll`? | `select`/`poll`: O(n) scan of all fds each call. `epoll`: O(1) wakeup via kernel ready list, scales to 100k fds. LDS uses epoll |
| What does the kernel do when a NIC interrupt fires? | IRQ → interrupt handler → clears interrupt, schedules NAPI → softirq → NAPI poll → fills sk_buff → wakes epoll waiters |
| What is `inotify`? | Kernel subsystem for filesystem events. Register path → events arrive on readable fd. LDS uses it for plugin hot-loading |
| What is `signalfd`? | Converts signal delivery to readable fd — integrates with epoll, no async-signal-safety restrictions |
| What does `ioctl(NBD_DO_IT)` do? | Tells kernel to start forwarding block I/O over the socket — blocks until disconnect. LDS runs this in a dedicated thread because it never returns |

### Networking / NIC

| Question | Answer |
|---|---|
| Walk me through a UDP packet from NIC to your recv() call | NIC DMA → RX ring descriptor filled → interrupt → softirq NAPI poll → sk_buff allocated → IP/UDP demux → socket recv buffer → epoll ready list → epoll_wait returns → recvfrom() copies to userspace |
| What is TCP framing? | TCP is a byte stream — no message boundaries. Must length-prefix messages and loop recv until full message received. LDS uses `ReadAll` loop |
| What is the socket buffer? | Kernel ring buffer per socket. NIC DMA fills it; recv() drains it. epoll_wait fires when it becomes non-empty |
| What is EPOLLIN level-triggered vs edge-triggered? | Level-triggered: notifies while data remains. Edge-triggered: only on transition. LDS uses level-triggered — simpler, no missed wakeups |
| Why UDP for storage writes in LDS? | Application controls retry with exponential backoff — unacceptable for TCP retransmit to block the I/O path. See [[04 - Why UDP not TCP]] |

---

## Level 5 — Gaps to Fill Before the Interview

### Priority 1 — Read (2-3 hours each)

1. **DMA and Cache Coherency**
   - Linux DMA API: `dma_alloc_coherent`, `dma_map_single`, `dma_sync_*`
   - Why coherent vs. streaming DMA matters
   - IOMMU role in DMA safety

2. **PCIe Basics**
   - Configuration space, BARs, capabilities
   - Memory-mapped vs. I/O-mapped register access
   - MSI vs. MSI-X interrupts (NIC firmware critical)

3. **Linux Network Driver Model**
   - `net_device` structure, `ndo_start_xmit`
   - NAPI polling — why it replaces pure interrupt mode under load
   - `sk_buff` allocation and lifecycle

### Priority 2 — Connect to What You Know

| Firmware Concept | LDS Analogy |
|---|---|
| DMA OWNER bit flip | Singleton `store(release)` — write data before write pointer |
| Interrupt → NAPI schedule → poll | epoll_wait → Reactor → enqueue to ThreadPool |
| MSI-X vector per queue | One epoll fd per connection, one handler per event type |
| TX doorbell after descriptor write | `send()` after filling send buffer — order enforced |
| Firmware register sequence | `ioctl(NBD_SET_SOCK)` → `ioctl(NBD_DO_IT)` — setup before run |

### Priority 3 — One-liner answers to expect

- "What's the first thing you do when a register read returns unexpected garbage?" → Check if MMIO region is mapped, check PCIe link status, add read-back after write, check byte-order (PCIe is little-endian).
- "How do you debug a DMA corruption?" → Check descriptor alignment, verify DMA address isn't stale after realloc, check cache flush missing before DMA, verify IOMMU mappings.
- "What is a race between firmware and driver?" → Both sides touching the same descriptor or register without OWNER protocol. Fix: agree on ownership handoff with memory barrier.

---

## The LDS-to-NVIDIA Bridge (use this framing in the interview)

> "My LDS project is essentially the host-side mirror of what NIC firmware implements. I wrote the epoll-driven event loop that processes incoming data from a kernel socket — that's the driver side of the DMA → softirq → epoll → recv() path you've built the other half of. My Reactor pattern, priority work queue, and RAII resource management are the same disciplines firmware engineers use — just in userspace C++ rather than embedded C. I'm excited to go deeper on the hardware side: descriptor rings, MMIO register sequences, and the DMA coherency model."
