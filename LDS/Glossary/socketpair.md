---
name: socketpair — AF_UNIX
type: linux-api
---

# socketpair — AF_UNIX

**[man page →](https://man7.org/linux/man-pages/man2/socketpair.2.html)**

Creates two connected Unix-domain sockets in a single call. Data written to one end can be read from the other. No network involved — pure kernel memory.

```c
int fds[2];
socketpair(AF_UNIX, SOCK_STREAM, 0, fds);
// fds[0] and fds[1] are now connected
// write to fds[0] → read from fds[1], and vice versa
```

## Role in NBD

The NBD kernel driver uses a socketpair as the bridge between the kernel and our userspace process:

```
Kernel side (NBD driver)     Userspace side (LDS process)
        m_clientFd    ←————→    m_serverFd
             │                       │
   writes nbd_request          reads nbd_request
   blocks waiting              processes request
   for nbd_reply         ←     writes nbd_reply
   unblocks user's             (SendReply)
   read()/write()
```

The kernel writes `nbd_request` structs to `m_clientFd`. Our process reads from `m_serverFd`, fulfills the request (reading/writing data from minions), then writes an `nbd_reply` back to `m_serverFd`. The kernel receives the reply and unblocks the user's system call.

## Why Not a Real Network Socket?

The socketpair is local — kernel to userspace on the same machine. No TCP/IP overhead, no port binding, no network stack traversal. It behaves exactly like a socket API but goes through kernel memory.

## Related
- [[NBD Layer]] — full NBD protocol
- [[NBD Protocol Deep Dive]] — struct layouts and handle matching
- [[Reactor]] — epoll watches the m_serverFd end
