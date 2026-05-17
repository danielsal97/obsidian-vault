1# Job Search Plan

**Goal:** First C++ systems/backend job  
**Start date:** 2026-05-08  
**Target:** First offer within 8–12 weeks  
**Last updated:** 2026-05-08

---

## The Strategy

Apply now. Don't wait for the project to be done. The hiring pipeline takes weeks — start filling it today while continuing to build and prep in parallel.

```
Week 1:   Polish repo + CV → Start sending applications
Week 2–4: Interview prep daily + apply daily + continue Phase 2
Week 5+:  Interviews start → prep intensifies → keep applying
```

---

## Week 1 — Make the Repo Presentable (Do This First)

These are quick wins that dramatically improve how your GitHub looks to an interviewer. Each item is < 1 day.

### GitHub Polish Checklist

- [x] **README** — ✅ Done (2026-05-08)
  - Architecture diagram, dual NBD/TCP mode, build/run commands, wire protocol, component table, design pattern rationale, roadmap

- [x] **Fix the diverged branches** — ✅ Done (2026-05-08) — rebased local onto origin/main

- [ ] **2–3 gtest unit tests** — signals professional, not student
  - `test_local_storage.cpp` — write/read round-trip
  - `test_input_mediator.cpp` — dispatch to correct handler
  - `test_tcp_driver.cpp` — already exists but not gtest, convert it

- [x] **GitHub Actions CI** — green checkmark on every commit
  ```yaml
  # .github/workflows/build.yml
  on: [push, pull_request]
  jobs:
    build:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - run: sudo apt-get install -y g++ make libgtest-dev
        - run: make
        - run: make run_tests
  ```

- [x] **Pin the repo** on GitHub profile — make it your featured project

---

## CV Checklist

- [x] LDS project description — 3 bullet points max:
  - "Distributed NAS system in C++20: epoll Reactor, plugin system via dlopen, TCP block device interface"
  - "Implemented RAID01 block distribution across storage nodes with async UDP + retry/backoff"
  - "Phase 2A: TCP server drop-in for NBD kernel driver, enabling remote Mac↔Linux block I/O"

- [x] Technologies section: C++20, Linux, pthreads, epoll, TCP/UDP sockets, inotify, NBD, Google Test, Make, Docker, Git

- [x] Keep it to 1 page

- [x] GitHub link visible at the top

---

## Where to Apply

### Tier 1 — Best fit for your profile
- Embedded / IoT companies (your LDS is literally IoT NAS)
- Storage companies (NetApp, Pure Storage, Vast Data, Weka)
- Infrastructure / systems software (Nvidia, Intel, Cloudflare, Akamai)
- Israeli defense tech (Rafael, Elbit, IAI) — C++ systems background is gold

### Tier 2 — Good fit
- Any backend C++ role
- Kernel / driver teams
- High-frequency trading (HFT) — they love low-level C++

### How many to send
- **Week 1:** 5–10 applications (quality > quantity, personalize each)
- **Week 2+:** 3–5 per day until you have 3+ active interview processes

---

## Daily Schedule (Weeks 2–4)

```
Morning (1–2 hrs): Interview prep — one topic per day
Afternoon (2–3 hrs): Continue Phase 2 (MinionProxy + RAID01Manager)
Evening (30 min): Send 2–3 applications, follow up on existing ones
```

---

## Interview Prep Order

Work through the Obsidian notes in this order — one topic per day:

| Day | Topic | Note |
|---|---|---|
| 1 | C++ fundamentals | [[Engineering/Interview - C++ Language]] |
| 2 | Concurrency | [[Engineering/Interview - Concurrency]] |
| 3 | Linux & Networking | [[Engineering/Interview - Linux & Networking]] |
| 4 | Data Structures | [[Engineering/Interview - Data Structures]] |
| 5 | LDS system design | [[Start Here]], [[System Overview]], [[Request Lifecycle]] |
| 6 | Design patterns | [[Design Patterns/Reactor]], [[Design Patterns/Observer]], [[Factory]] |
| 7 | Known bugs + decisions | [[Engineering/Known Bugs]], [[Decisions/]] |
| 8–∞ | Repeat + practice explaining LDS out loud | [[Engineering/Interview Guide]] |

**Most important:** Practice your 3-minute pitch about LDS. Record yourself. Should cover: what it is, what you built, one interesting technical challenge you solved.

---

## What to Build vs Skip

### Build (adds interview stories)
- [ ] **MinionProxy + UDP** — "I implemented fire-and-forget UDP with MSG_ID tracking and exponential backoff retry"
- [ ] **README + CI** — polish, not features (Week 1)
- [ ] **AddressSanitizer clean run** — "my code runs clean under ASan"

### Skip (diminishing returns before job search)
- RAID01Manager — describe the algorithm in interviews, don't need to implement
- ResponseManager — too deep, not worth the time now
- Watchdog / AutoDiscovery / Minion Server — architecture story is enough
- Phase 5–6 — irrelevant until you have a job offer

### If you have extra time
- Python or C++ CLI tool to demo LDS over TCP — very concrete, impressive to show live in an interview

---

## The Pitch (Memorize This)

> "I built a distributed NAS system in C++20 on Linux. The core is an epoll Reactor loop that handles both NBD kernel requests and TCP client connections. Data is distributed across storage nodes using RAID01 — every block goes to two nodes for redundancy. I implemented the full stack: the event loop, a plugin system using dlopen for runtime extensibility, a TCP server as a drop-in replacement for the NBD kernel interface so remote clients can read and write blocks over the network, and async UDP with message IDs and exponential backoff for minion communication."

Hit these words: **epoll, RAID01, TCP, UDP, async, plugin system, C++20.**

---

## Application Tracker

| Company | Role | Date sent | Status | Notes |
|---|---|---|---|---|
| | | | | |

---

## Milestones

- [x] README done — 2026-05-08
- [x] Diverged branches fixed — 2026-05-08
- [ ] gtest + GitHub Actions CI
- [ ] Pin repo on GitHub profile
- [ ] CV updated with LDS
- [ ] First 10 applications sent
- [ ] First technical screen scheduled
- [ ] First onsite / final round
- [ ] Offer

---

## Related Notes

- [[Engineering/Interview Guide]] — 3-min pitch, cold Q&A
- [[Start Here]] — full LDS system for talking about in interviews
- [[Engineering/Known Bugs]] — bugs to mention (show you can debug)
- [[Manager/Phase 2 Execution Plan]] — what to build next
