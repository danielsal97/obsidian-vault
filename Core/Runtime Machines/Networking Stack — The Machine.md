# Networking Stack — The Machine

## The Model

A UDP packet travels from NIC to userspace in three hops: NIC → kernel socket buffer → recvfrom(). The kernel is the middleman: it owns the buffer, wakes the sleeping process when data arrives, and hands the data to userspace on the syscall. epoll is the notification layer that tells you WHICH socket has data without scanning all sockets.

## How It Moves — UDP Receive

```
Remote host sends UDP datagram
      │
      ▼
NIC receives frame
  → DMA: kernel driver places packet into receive ring buffer (no CPU)
  → NIC raises hardware interrupt
      │
      ▼
Kernel interrupt handler (softirq context)
  → takes packet from ring buffer
  → IP layer: validate checksum, routing decision
  → UDP layer: find socket by (dst IP, dst port)
  → copy data into socket receive buffer (sk_buff)
  → mark socket as readable
  → if any task waiting on epoll for this socket fd → wake it
      │
      ▼
epoll_wait() returns in userspace (process wakes from sleep)
  → returns the fd that became readable
      │
      ▼
process calls recvfrom(fd, buf, len, ...)
  → kernel: copy data from socket buffer to userspace buf
  → return bytes received
```

## How It Moves — epoll Lifecycle

```
Setup (once):
  epoll_fd = epoll_create1(0)
  epoll_ctl(epoll_fd, EPOLL_CTL_ADD, socket_fd, &event)  // register interest

Wait loop:
  n = epoll_wait(epoll_fd, events, MAX_EVENTS, timeout_ms)
  → if no fd is ready: process sleeps, kernel parks it
  → when any registered fd becomes ready: kernel adds it to the ready list
  → epoll_wait returns: n = number of ready events
  → iterate events[0..n-1], each has .data.fd and .events flags
  → dispatch to handler for each ready fd
```

## Edge-triggered vs Level-triggered

Level-triggered (default EPOLLIN): `epoll_wait` returns whenever fd has data. Returns again next call if data still present.

Edge-triggered (EPOLLET): `epoll_wait` returns ONCE when fd transitions from not-ready to ready. You MUST drain the fd completely (read until EAGAIN) or the notification is lost. Higher performance but requires non-blocking sockets and careful drain loop.

LDS uses edge-triggered for the NBD fd to avoid spurious wakeups on partial reads.

## Where Time Is Spent

- NIC interrupt to kernel socket buffer: ~5-50μs (DMA + softirq)
- epoll_wait returning: negligible (futex wakeup ~1-5μs)
- recvfrom copy: ~1μs for typical MTU-sized packet
- Total receive latency (NIC → userspace): 50-200μs on LAN

## Links

→ [[../Domains/06 - Networking/Theory/04 - epoll]] — epoll API and kernel internals
→ [[../Domains/06 - Networking/Theory/03 - UDP Sockets]] — UDP socket API
→ [[../Domains/06 - Networking/Theory/02 - Sockets TCP]] — TCP for comparison
→ [[../Domains/07 - Design Patterns/Theory/01 - Reactor]] — using epoll as a Reactor event loop
→ [[../Domains/06 - Networking/Mental Models/04 - epoll — The Machine]] — epoll runtime story
→ [[../Domains/04 - Linux/Theory/02 - File Descriptors]] — what a socket fd is at the kernel level
