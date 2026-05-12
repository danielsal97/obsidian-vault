---
name: IoT — Internet of Things
type: concept
---

# IoT — Internet of Things

**[Wikipedia →](https://en.wikipedia.org/wiki/Internet_of_things)**

Networked physical devices — sensors, actuators, small computers — that communicate over IP networks. Distinguished from traditional computing by being embedded, low-power, numerous, and often resource-constrained.

## LDS Context

LDS is an IoT-class distributed storage system:

| IoT characteristic | LDS implementation |
|---|---|
| Many small devices | N Raspberry Pi minion nodes |
| Low power | RPi: ~5W idle per node |
| IP networking | UDP over LAN |
| Embedded Linux | Raspberry Pi OS |
| Dynamic topology | Nodes join/leave; AutoDiscovery handles it |

## Connections

**Mental Models:** [[UDP Sockets — The Machine]], [[Processes — The Machine]]  
**LDS Implementation:** [[System Overview]], [[Watchdog]]  
**Related Glossary:** [[Raspberry Pi]], [[NAS]], [[UDP]]
