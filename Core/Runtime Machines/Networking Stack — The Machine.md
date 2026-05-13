# Networking Stack — The Machine

## The Model

A packet travels in two directions. Inbound: electrical signal → NIC → DMA → kernel buffer → socket → userspace. Outbound: userspace → kernel buffer → TCP segmentation → NIC → wire. The kernel is the routing layer in both directions. Your process never touches hardware — it only sees data after the kernel has already processed several protocol layers.

---

## How It Moves — Inbound TCP Packet

```
[1] Electrical signal arrives on NIC
      │
      ▼
NIC hardware:
  → receives Ethernet frame from wire
  → verifies Ethernet FCS (frame check sequence)
  → DMA: writes frame bytes directly into kernel rx ring buffer
    (no CPU involved — DMA controller does the copy)
  → raises hardware interrupt: "frame available"
      │
      ▼
CPU pauses current execution → enters kernel interrupt handler
      │
      ▼
Kernel network interrupt (softirq, not hard interrupt):
  → pulls frame from rx ring buffer
  → Ethernet layer: strip header, identify protocol (IPv4)
  → IP layer: validate checksum, TTL check, routing decision
  → TCP layer:
      → validate TCP checksum
      → find socket: look up (src IP, src port, dst IP, dst port) in socket hash table
      → verify TCP sequence number is in-window
      → append payload to socket receive buffer (sk_buff)
      → update TCP receive window
      → schedule ACK (deferred, may be piggybacked)
      │
      ▼
Socket becomes readable:
  → if any task is sleeping in epoll_wait() watching this socket fd:
      → kernel adds socket fd to epoll ready list
      → wakes the task: marks TASK_RUNNING
      │
      ▼
epoll_wait() returns in Reactor thread (userspace)
  → returns: fd = socket_fd, events = EPOLLIN
      │
      ▼
Reactor: does NOT read the data itself
  → looks up handler for this fd
  → calls handler.onReadable()
  → handler calls recv(fd, buf, len, MSG_DONTWAIT)
  → kernel: copy data from socket buffer → userspace buf
  → return bytes received
      │
      ▼
Reactor posts work item to ThreadPool WPQ
  → worker thread wakes
  → executes: parse request, run application logic
```

---

## How It Moves — Outbound TCP Reply

```
Worker thread calls send(fd, response_buf, len, 0)
      │
      ▼
Kernel:
  → copy response bytes from userspace buffer → socket send buffer
  → TCP layer:
      → segment into MSS-sized chunks (typically 1460 bytes)
      → set sequence numbers, set TCP flags (ACK, PSH)
      → start retransmission timer for each unACKed segment
      → check send window: can we send? (receiver window + congestion window)
      → if window allows: pass to IP layer
  → IP layer: add IP header, TTL, checksum
  → Ethernet layer: ARP lookup for next-hop MAC address
  → NIC driver: add frame to tx ring buffer
      │
      ▼
NIC hardware:
  → DMA reads frame from tx ring buffer into NIC hardware queue
  → NIC transmits frame on wire
  → NIC raises interrupt: "tx complete" (ring slot now free)
      │
      ▼
Later: remote host sends ACK
  → arrives as new inbound frame
  → TCP layer: marks segments up to ACK number as delivered
  → cancels retransmit timers for ACKed segments
  → increases congestion window (slow start / congestion avoidance)
```

---

## What TCP Does Behind the Scenes

**Retransmission**: if ACK doesn't arrive before retransmit timer fires, kernel resends the segment. Timer uses exponential backoff. Under loss, throughput drops dramatically — this is why UDP is preferred for LDS block I/O.

**Congestion control**: kernel tracks a congestion window (cwnd). After packet loss (timeout or duplicate ACKs), cwnd is halved. This is transparent to your application but causes unpredictable latency spikes.

**Nagle's algorithm**: by default, TCP buffers small writes and batches them. On low-latency servers, disable with `TCP_NODELAY` to prevent 40ms delays.

---

## Hidden Costs

| Operation | Cost |
|---|---|
| Userspace → kernel (syscall) | ~100ns |
| Kernel receive buffer copy to userspace | ~1μs for 4KB |
| epoll_wait wakeup (futex) | ~1-5μs |
| Context switch (Reactor → worker thread) | ~2-10μs |
| TCP ACK round-trip | ~100μs LAN, ~10ms WAN |
| TCP retransmit timer | 200ms-1s (exponential backoff) |
| DMA transfer NIC → RAM | ~5-50μs |

---

## Related Machines

→ [[../Domains/06 - Networking/Mental Models/04 - epoll — The Machine]]
→ [[../Domains/07 - Design Patterns/Mental Models/01 - Reactor Pattern — The Machine]]
→ [[../Domains/05 - Concurrency/Mental Models/01 - Multithreading Patterns — The Machine]]
→ [[Concurrency Runtime — The Machine]]
→ [[Memory System — The Machine]]
→ [[../Domains/04 - Linux/Mental Models/10 - Context Switch — The Machine]]
→ [[../Domains/06 - Networking/Theory/02 - Sockets TCP]]
→ [[../Domains/06 - Networking/Theory/04 - epoll]]
