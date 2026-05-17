# Networking — Hub

Sockets, protocols, and the I/O multiplexing that makes non-blocking servers possible.

## Place in Runtime

```
NIC DMA → softirq → socket buffer → epoll ready list → Reactor → ThreadPool
```

→ [[Networking Stack — The Machine]] — full packet path NIC→application (start here)
→ [[00 - VAULT MAP]] — vault root
→ [[Core/00 START HERE|Core Start Here]]

## The Machine

→ [[04 - epoll — The Machine]] — kernel ready list, epoll_wait() return, level vs edge
→ [[02 - TCP Sockets — The Machine]] — connect/accept, send buffer, ACK, retransmit, TIME_WAIT
→ [[03 - UDP Sockets — The Machine]] — no connection state, message boundaries, recvfrom semantics
→ [[01 - Networking Overview — The Machine]] — NIC DMA → kernel socket buffer → syscall return
→ [[01 - Reactor Pattern — The Machine]] — epoll loop + handler dispatch table
→ [[05 - IPC Overview — The Machine]] — pipes, socketpair, unix domain sockets

## Theory

→ [[01 - Overview]] — physical → Ethernet → IP → TCP/UDP → application
→ [[02 - Sockets TCP]] — socket(), connect(), RecvAll loop, wire protocol design
→ [[03 - UDP Sockets]] — sendto/recvfrom, message boundaries, MTU, broadcast
→ [[04 - epoll]] — select vs poll vs epoll, level vs edge-triggered, EPOLLET
→ [[05 - IPC Overview]] — pipes, socketpair, unix domain sockets, shared memory

## Interview Q&A

→ [[01 - Networking Q&A]] — epoll vs select, TCP sockets, TCP framing, byte ordering, UDP vs TCP

## Glossary

→ [[12 - TCP]] · [[14 - UDP]] · [[16 - epoll]] · [[19 - socketpair]]
