# Utilities & Framework Components (`/utilities`)

## Purpose

This directory contains **core framework components and utility classes** that form the foundation of the Local Cloud system. These are reusable, battle-tested components used throughout the project.

## Directory Structure

```
utilities/
├─ logger/                          # Logging system
├─ threading/                       # Threading utilities
└─ thread_safe_data_structures/     # Concurrent data structures
```

## Core Components

### 1. Logger (Observability)

Centralized logging for the entire system.

```cpp
#include "logger.hpp"

Logger& logger = Logger::getInstance();
logger.log(LogLevel::INFO, "System started");
logger.log(LogLevel::ERROR, "Connection failed");
```

**Log Levels**: `DEBUG` → `INFO` → `WARN` → `ERROR`

Thread-safe — multiple threads can log simultaneously.

**Test**: `./bin/test_logger`

---

### 2. ThreadPool (Concurrent Execution)

Execute tasks concurrently using worker threads.

```cpp
#include "thread_pool.hpp"

ThreadPool pool(4);  // 4 worker threads

auto future = pool.enqueue([](){ return doWork(); });
auto result = future.get();
```

**Architecture**:
```
ThreadPool (N threads)
    ├─ Worker 1..N
         ↑
    Thread-Safe Queue (WPQ)
```

**Test**: `./bin/test_thread_pool`

---

### 3. Work Queue (WPQ)

Thread-safe FIFO queue. Blocking pop with timeout. Used by ThreadPool.

```cpp
WorkQueue<Task> queue;
queue.push(task);
Task t = queue.pop();  // Blocks until item available
```

**Test**: `./bin/test_wpq`

---

## Framework Integration

```
Dispatcher (Observer Pattern)
    ↓ notifies
ThreadPool (threading)  →  Logger (Singleton)
    ├─ Worker threads
    └─ Work queue (WPQ)
```

## Usage Across Project

| Component | Used By | Purpose |
|-----------|---------|---------|
| Logger | All components | Debugging & observability |
| ThreadPool | Future phases | Async task execution |
| Work Queue | ThreadPool | Task distribution |

## ThreadPool Sizing

```cpp
// Optimal: match hardware
int optimal_threads = std::thread::hardware_concurrency();
ThreadPool pool(optimal_threads);
```

## Logger Level Control

```cpp
// Development: verbose
Logger::getInstance().setLevel(LogLevel::DEBUG);

// Production: less verbose
Logger::getInstance().setLevel(LogLevel::INFO);
```

## Performance

| Component | Overhead | Notes |
|-----------|---------|-------|
| Logger | Minimal (sync write) | Use at all levels |
| ThreadPool | Low (created once) | Optimal for tasks >1ms |
| Work Queue | O(1) push/pop | Grows with queue depth |

## Related Notes
- [[Logger]]
- [[Scheduler]]
- [[Utils Helpers]]

---

**Phase**: 1 | **Status**: ✅ Core utilities ready | **Used By**: All components, all future phases
