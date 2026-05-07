---
name: Raspberry Pi
type: hardware
---

# Raspberry Pi

**[Official site →](https://www.raspberrypi.com)** | **[Wikipedia →](https://en.wikipedia.org/wiki/Raspberry_Pi)**

A credit-card-sized single-board computer (~$35–$80) that runs standard Linux. Originally designed for education; widely adopted in IoT, embedded systems, and DIY projects.

## Specs Relevant to LDS

| Property | Value |
|----------|-------|
| CPU | ARM Cortex (64-bit on RPi 3/4/5) |
| RAM | 1–8 GB |
| Storage | microSD or USB drive |
| Network | 100/1000 Mbps Ethernet |
| OS | Raspberry Pi OS (Debian-based) |
| Power | ~5W idle |

## Role in LDS

Each Raspberry Pi acts as a **minion storage node**:
- Runs the `MinionServer` binary
- Stores block data on its local microSD or USB drive
- Listens on a UDP port for GET/PUT/DELETE commands from the master
- Broadcasts `"Hello, I'm Minion-N"` on startup for [[AutoDiscovery]]

The master node can be any Linux machine (laptop, server, another RPi).

## Why RPi?

- Cheap enough to deploy many nodes (redundancy without cost)
- Low power — always-on without significant electricity cost
- Standard Linux — same C++ toolchain as the master
- GPIO/USB allows external storage expansion

## Related
- [[AutoDiscovery]] — how new RPi nodes join automatically
- [[Watchdog]] — how the master monitors RPi health
- [[State Diagram - Minion]] — minion lifecycle
