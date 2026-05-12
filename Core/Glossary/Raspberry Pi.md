---
name: Raspberry Pi
type: hardware
---

# Raspberry Pi

**[Official site →](https://www.raspberrypi.com)** | **[Wikipedia →](https://en.wikipedia.org/wiki/Raspberry_Pi)**

A credit-card-sized single-board computer (~$35–$80) that runs standard Linux. Widely adopted in IoT, embedded systems, and DIY projects.

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
- Broadcasts `"Hello, I'm Minion-N"` on startup for AutoDiscovery

## Connections

**Mental Models:** [[UDP Sockets — The Machine]], [[Processes — The Machine]]  
**LDS Implementation:** [[Watchdog]], [[State Diagram - Minion]]  
**Related Glossary:** [[IoT]], [[NAS]], [[UDP]]
