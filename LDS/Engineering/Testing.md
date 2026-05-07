# Testing (`/test`)

## Purpose

This directory contains **test files, test utilities, and testing documentation** for the Local Cloud project.

## Directory Structure

```
test/
├─ unit/                        # Unit tests for individual components
├─ BEHAVIOR_GUIDE.md            # Test behavior documentation
├─ TEST_MSG_BROKER_GUIDE.md     # Message broker testing guide
├─ test_readwrite.sh            # Shell script for read/write testing
└─ test_signals.sh              # Shell script for signal testing
```

## Running Tests

```bash
# Run all tests
make test

# Run specific test binary
./bin/test_plugin_load
./bin/test_thread_pool
./bin/test_logger
./bin/test_msg_broker
```

## Test Coverage

### Phase 1: Dynamic Plugin Loading ✅
- [x] Plugin loading (dlopen)
- [x] Plugin unloading (dlclose)
- [x] Filesystem monitoring (inotify)
- [x] Multiple plugin simultaneous loading
- [x] Plugin auto-initialization

### Framework Components ✅
- [x] Dispatcher event notification
- [x] CallBack observer pattern
- [x] ThreadPool concurrent execution
- [x] Logger message output
- [x] Singleton pattern
- [x] Factory pattern
- [x] Command pattern
- [x] Message broker

## Test Execution Flow

```
make test
├─ test_plugin_load       → Single plugin loading/unloading
├─ test_pnp_main          → Multiple plugins, filesystem events
├─ test_thread_pool       → Concurrent task execution
├─ test_msg_broker        → Message passing between components
├─ test_logger            → Log output and filtering
└─ ... other framework tests
```

## Expected Test Output

### Successful Plugin Load
```
🚀 [SamplePlugin] Constructor - PLUGIN LOADED
💥 [SamplePlugin] Destructor - PLUGIN UNLOADED
✅ Test passed
```

### Filesystem Monitoring
```
🔔 [DirMonitor] Detected: CREATE: plugin1.so
📨 [PNP] Event received: CREATE: plugin1.so
✅ Loaded successfully
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Plugin load fails | Check `/tmp/pnp_plugins` exists, verify .so is executable |
| Thread pool tests hang | Check for deadlock, verify thread count |
| Message broker tests fail | Check thread safety, message ordering, serialization |

## Adding New Tests

1. Create test file in `test/unit/test_<component>.cpp`
2. Follow naming convention: `test_<component>.cpp`
3. Add to Makefile targets
4. Document expected behavior

## Test Template

```cpp
#include <iostream>
#include "framework_header.hpp"

int main() {
    MyComponent component;
    bool result = component.operation();
    assert(result == expected);
    std::cout << "✅ Test passed" << std::endl;
    return 0;
}
```

## Phase 2+ Tests Planned

| Phase | Component | Test |
|-------|-----------|------|
| 2 | ServiceRegistry | test_service_registry.cpp |
| 2 | ServiceDiscovery | test_service_discovery.cpp |
| 3 | RPC | test_rpc_invocation.cpp |
| 4 | Scheduler | test_scheduler.cpp |
| 5 | Storage | test_storage.cpp |
| 6 | Security | test_security.cpp |

## Related Notes
- [[Unit Tests]]
- [[Known Bugs]]
- [[Plugin Loading Internals]]

---

**Phase**: 1 | **Status**: ✅ Test suite complete and passing
