# Decision: TCP for the Client Link

**Decision:** The Mac client ↔ Linux master connection uses TCP, not UDP.  
**Context:** Phase 2A (client-server link). This is separate from the master ↔ minion protocol, which uses UDP (see [[Why UDP not TCP]]).

---

## The Choice

| | TCP | UDP |
|---|---|---|
| Delivery | Guaranteed, ordered | Best-effort, unordered |
| Framing | Stream (you handle framing) | Packets (natural framing) |
| Reliability | Built-in retransmit | You implement it yourself |
| Connection | Stateful (connect/disconnect) | Stateless |
| Complexity for this use case | Low — length-prefix framing is simple | High — need MSG_ID, retry, reorder |

---

## Why TCP Wins Here

**1. The client is interactive and expects errors.**
A CLI user running `./ldsclient write 0 data.bin` expects to know if it failed. TCP's reliable delivery means a `send()` that succeeds means the data was received. With UDP you implement retry and acknowledgement yourself — which is what `ResponseManager` + `Scheduler` are for on the minion side.

**2. There is one client, one connection.**
UDP shines when you're fanning out to many stateless endpoints (like the master pinging 5 minions in parallel). Here there's one Mac, one Linux master, one conversation. The overhead of TCP connection setup is irrelevant.

**3. TCP handles fragmentation for you.**
The `RecvAll()` pattern (loop until N bytes received) is the entirety of the reliability work on our end. With UDP on a local network you'd still need to write `RecvAll` because UDP has a max packet size — and then add MSG_IDs and retry on top.

**4. It's what real storage protocols use.**
iSCSI (enterprise storage over IP), NFS over TCP, SMB — all use TCP for the client-facing link. Interviewers recognize this. "I used TCP for the client connection and UDP for the server-to-minion fan-out because the reliability requirements differ" is a precise, correct, and impressive answer.

**5. It's what the original Phase 2 plan already used for a different purpose.**
The Wire Protocol Spec for master ↔ minion uses UDP for stateless fire-and-forget fan-out. The client link is stateful and interactive — a different problem deserves a different tool.

---

## The Tradeoff

UDP would be valid if:
- You wanted to support many concurrent clients without per-connection state
- You were latency-sensitive at microsecond scale (TCP's Nagle algorithm can add delay)
- You needed multicast (send to multiple clients at once)

None of those apply here. The tradeoff is simple: TCP costs a three-way handshake on connect (once per session). That's it.

---

## Related Notes

- [[Why UDP not TCP]] — why the master ↔ minion path uses UDP (different reasoning)
- [[Architecture/03 - Client-Server Architecture]]
- [[Phase 2A - Mac Client TCP Bridge]]
