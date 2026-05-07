# Application Layer (`/app`)

## Purpose

This directory contains **application-level code** that demonstrates and exercises the Local Cloud Dynamic Plugin Loading (LDS) system. These are executable programs that use the core LDS framework components.

## Contents

| File | Purpose |
|------|---------|
| `LDS.cpp` | Main application demonstrating plugin loading and lifecycle management |

## What's Here

### LDS.cpp
- Main entry point for the Local Cloud plugin system
- Demonstrates how to use the LDS framework to load plugins
- Shows integration with:
  - **Loader**: Dynamic linking (dlopen/dlclose)
  - **DirMonitor**: Filesystem event detection
  - **PNP**: Plugin orchestration
  - **Dispatcher/CallBack**: Event notification system

## How It Works

```
LDS Application
├─ Initialize DirMonitor
├─ Monitor plugin directory for changes
├─ Load plugins dynamically (via Loader)
├─ Initialize plugins through PNP
└─ Handle plugin lifecycle events
```

## Architecture Integration

```
┌─────────────────────────────────────┐
│     Application Layer (app/)        │
│  - LDS main application             │
│  - Example plugin loading           │
└─────────────────────────────────────┘
               ▲
               │ uses
               │
┌─────────────────────────────────────┐
│   Service Framework Layer            │
│  - Dispatcher, CallBack              │
│  - Message Broker, ThreadPool        │
└─────────────────────────────────────┘
               ▲
               │ uses
               │
┌─────────────────────────────────────┐
│   Core Infrastructure (LDS Phase 1)  │
│  - Loader, DirMonitor, PNP           │
│  - Plugin System                     │
└─────────────────────────────────────┘
```

## Building & Running

```bash
# Build the application
make

# Run the application
./bin/LDS

# In another terminal, add plugins to the monitored directory
cp ./bin/sample_plugin.so /tmp/pnp_plugins/
```

## Related Notes
- [[Plugins]]
- [[DirMonitor]]
- [[PNP]]
- [[Three-Tier Architecture]]

---

**Phase**: 1 (Dynamic Plugin Loading) | **Status**: ✅ Complete & Tested
