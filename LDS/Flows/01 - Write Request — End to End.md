# Write Request — End to End

A single `write()` call traced top to bottom through every layer of LDS.

---

## Step 1 — User Space to Kernel

```
user process:  write(fd, buf, 512)
                    │
                    ▼
             Linux VFS → Block Layer
                    │
                    ▼
             NBD kernel driver
             encodes: nbd_request { WRITE, handle=0xABCD, offset=4096, len=512 }
             writes to socketpair fd
             ★ user's write() is now BLOCKED waiting for our reply ★
```

The kernel acts as a bridge. The user writes to what looks like a disk. The NBD driver packages it into a struct and hands it to our process through a socketpair. The user's call is blocked until we reply.

→ [[06 - NBD Layer]] · [[03 - NBD Protocol Deep Dive]]

---

## Step 2 — Reactor Wakes Up

```
             socketpair fd has data
                    │
                    ▼
             Reactor (epoll loop)
             epoll_wait() fires on the NBD fd
             calls: io_handler(fd)
```

The Reactor is the heartbeat of the master. It sits idle (zero CPU) until an fd becomes readable, then dispatches to the registered handler and returns immediately. It never does the work itself.

→ [[03 - Reactor]] · [[03 - Reactor — The Machine]]

---

## Step 3 — InputMediator Converts Event to Command

```
             io_handler(fd)
                    │
                    ▼
             InputMediator::HandleEvent(fd)
             reads DriverData { WRITE, handle, offset, buffer }
                    │
                    ▼
             Factory::Create("WRITE", driverData)
             → returns shared_ptr<WriteCommand>
                    │
                    ▼
             ThreadPool.Enqueue(cmd)
             ★ main thread returns to epoll immediately ★
```

InputMediator bridges the event world (raw fds) and the command world (typed objects). It reads the raw struct, creates the right command, pushes it to the priority queue. The main thread never blocks.

→ [[InputMediator]] · [[Commands]] · [[Factory]]

---

## Step 4 — ThreadPool Executes the Command

```
             ThreadPool worker thread (sleeping on WPQ)
             WPQ.Pop() → WriteCommand
                    │
                    ▼
             WriteCommand::Execute()
```

The ThreadPool holds N worker threads, all blocking on the WPQ (Waitable Priority Queue). Priority: `WRITE (High) > READ (Med) > FLUSH (Low)`.

→ [[06 - ThreadPool]] · [[04 - ThreadPool and WPQ — The Machine]]

---

## Step 5 — RAID01Manager Finds the Minions

```
             WriteCommand::Execute()
                    │
                    ▼
             RAID01Manager::GetBlockLocation(block_num)
             primary = block_num % num_minions
             replica = (block_num + 1) % num_minions
             → returns { minionA_id, minionB_id }
```

Pure mapping logic — no networking, no I/O. Returns two minion IDs for any block number. Failed minions are skipped.

→ [[02 - RAID01 Manager]] · [[07 - RAID01 Explained]]

---

## Step 6 — MinionProxy Sends UDP Packets

```
             WriteCommand::Execute() continues
                    │
                    ▼
             MinionProxy::SendPutBlock(minionA, offset, data) → msg_id_A
             MinionProxy::SendPutBlock(minionB, offset, data) → msg_id_B

             Wire format:
             [ MSG_ID: 4B ][ OP: 1B ][ OFFSET: 8B ][ LEN: 4B ][ DATA: var ]

             Fire and forget — returns immediately
```

Serializes the request into wire format and fires UDP. Returns a MSG_ID for tracking.

→ [[03 - MinionProxy]] · [[10 - Wire Protocol Spec]]

---

## Step 7 — ResponseManager + Scheduler Handle the Async Response

```
             ResponseManager (background thread, blocking on recvfrom)
                    │
                    ▼
             UDP packet arrives from Minion A
             parse: [ MSG_ID=msg_id_A ][ STATUS=OK ]
             lookup callback for msg_id_A
             call callback → WriteCommand notified

             Scheduler (parallel)
             tracks msg_id_A with deadline = now + 1s
             if deadline exceeded → retry with exponential backoff
             max retries exceeded → propagate error
```

→ [[04 - ResponseManager]] · [[05 - Scheduler]]

---

## Step 8 — Reply Goes Back to Kernel

```
             Both ACKs received
                    │
                    ▼
             WriteCommand calls: driver.SendReply(driverData)
             encodes: nbd_reply { magic, error=0, handle=0xABCD }
             writes to socketpair

             Kernel receives reply, matches handle 0xABCD
             ★ user's write() unblocks, returns 512 ★
```

If `error != 0`, the user sees `EIO`.

→ [[08 - Request Lifecycle]] · [[02 - NBDDriverComm]]

---

## Full data flow

```
                     USER: write(fd, data)
                              │
                         [KERNEL: NBD]
                              │ socketpair
                         [REACTOR: epoll]
                              │ event fires
                     [INPUT MEDIATOR]
                        │
                  Factory::Create("WRITE")
                        │
               [THREAD POOL / WPQ]
                  worker picks up
                        │
               [WRITE COMMAND::Execute()]
                        │
               [RAID01 MANAGER]
               GetBlockLocation(N)
               → (primary, replica)
                    │         │
             [MINION PROXY]  [MINION PROXY]
             SendPutBlock(A)  SendPutBlock(B)
                    │               │
             [UDP → Minion A] [UDP → Minion B]
                    │               │
             [RESPONSE MANAGER receives ACKs]
                    │
             [SCHEDULER clears deadlines]
                    │
             [WRITE COMMAND calls SendReply]
                              │ socketpair
                     [KERNEL: unblocks write()]
                              │
                       USER: write() returns
```
