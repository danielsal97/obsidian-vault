# Plugin System (`/plugins`)

## Purpose

This directory contains **plugin implementations** - the modules that are dynamically loaded at runtime by the Local Cloud system. Plugins are self-contained units of functionality that can be added, removed, or updated without restarting the main application.

## Directory Structure

```
plugins/
├─ include/
│  └─ plugin_interface.hpp    # Base plugin definitions
└─ src/
   └─ sample_plugin.cpp       # Example plugin implementation
```

## What is a Plugin?

A plugin is a **shared library (.so file)** that:
1. Implements the plugin interface
2. Provides self-initialization via static constructors
3. Registers itself with the PluginFactory
4. Can be loaded/unloaded dynamically without restart
5. Operates independently from other plugins

## Plugin Lifecycle

```
1. Plugin file created in monitored directory
2. DirMonitor detects filesystem event
3. PNP receives notification
4. Loader calls dlopen() on plugin file
5. Plugin constructor runs (static initializer)
6. Plugin registers with Factory
7. Plugin is ready for use
```

## Minimal Plugin Implementation

```cpp
class MyPlugin {
public:
    MyPlugin() {
        std::cout << "🚀 [MyPlugin] Loaded" << std::endl;
        PluginFactory::getInstance().registerType("MyPlugin", 
            []() { return new MyPlugin(); });
    }
    ~MyPlugin() {
        std::cout << "💥 [MyPlugin] Unloaded" << std::endl;
    }
};

// Auto-initialization
__attribute__((constructor)) void init() { new MyPlugin(); }
```

## Loading Plugins

### Via PNP (Directory Monitoring)
```cpp
PNP plugin_manager;
plugin_manager.monitorDirectory("/tmp/pnp_plugins");
// PNP will load any .so files added to the directory
```

### Via Loader (Direct)
```cpp
Loader plugin_loader("./bin/sample_plugin.so");
// Plugin is loaded and initialized; destructor automatically unloads
```

## Building

```bash
make plugins
# Or manually:
g++ -fPIC -shared -o bin/sample_plugin.so plugins/src/sample_plugin.cpp
```

## Debugging

```bash
# Check plugin symbols
nm -D bin/sample_plugin.so | grep -E "init|SamplePlugin"

# Test loading
./bin/test_plugin_load
./bin/test_pnp_main
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Plugin not found | Check file path, verify .so extension |
| Symbol not found | Verify all dependencies compiled, check `nm -D` |
| Segfault on load | Check constructor code, verify thread safety |
| Plugin not initialized | Verify static constructor runs, check Factory |

## Future (Phase 2+)

Plugins will become services with dependency declarations, service discovery, RPC communication, and resource quotas.

## Related Notes
- [[PNP]]
- [[DirMonitor]]
- [[Factory]]
- [[App Layer]]

---

**Phase**: 1 (Dynamic Plugin Loading) ✅ | **Status**: Working, extensible for Phase 2+
