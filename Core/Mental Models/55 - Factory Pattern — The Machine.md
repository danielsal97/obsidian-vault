# Factory Pattern — The Machine

## The Model
A machine that produces objects without the caller knowing which specific type is being made. You give the factory a specification ("TCP mode"); it builds the right type and hands you back an interface pointer. The caller only knows the interface — it never sees the concrete type's header. Adding a new type requires only changing the factory, not the caller.

## How It Moves

```
Without factory:
  // Caller must know TCPDriverComm exists and how to construct it:
  #include "TCPDriverComm.hpp"
  auto driver = std::make_shared<TCPDriverComm>(port);
  // Adding NBD mode: add another #include, another if/else, recompile caller

With factory:
  // Caller only knows IDriverComm:
  auto driver = DriverFactory::Create("tcp", port);
  // Returns shared_ptr<IDriverComm> — caller never sees TCPDriverComm.hpp
  // Adding NBD mode: add to factory only — caller recompiles nothing
```

**LDS plugin factory (dlopen):**
```
plugins/libpluginA.so
      │
      v
dlopen("libpluginA.so")
dlsym("createPlugin")        ← find the factory function by name
IPlugin* = createPlugin()    ← call it — returns interface pointer
                              never imported the plugin's header
```

**The critical property:** the factory lives at the boundary between "what is needed" (interface) and "what exists" (implementation). Caller imports only the interface header.

## The Blueprint

```cpp
// Factory function (simple):
std::shared_ptr<IDriverComm> DriverFactory::Create(
    const std::string& mode, int param)
{
    if (mode == "tcp")  return std::make_shared<TCPDriverComm>(param);
    if (mode == "nbd")  return std::make_shared<NBDDriverComm>(param);
    throw std::invalid_argument("Unknown driver: " + mode);
}

// Plugin factory (dlopen — runtime loading):
void* handle = dlopen("./libplugin.so", RTLD_LAZY);
using CreateFn = IPlugin*(*)();
auto create = (CreateFn)dlsym(handle, "createPlugin");
IPlugin* plugin = create();
```

## Where It Breaks

- **Factory knows too much**: if the factory imports every concrete type's header, adding a new type still requires recompiling the factory. Use abstract factory or registration pattern for large plugin systems.
- **No cleanup for dlopen**: `dlopen` handle must be `dlclose`d. The plugin's objects must be destroyed BEFORE `dlclose` — otherwise the code they point to is unmapped → crash.
- **Missing `extern "C"` on plugin function**: C++ name mangling makes `dlsym("createPlugin")` fail — the symbol is actually `_ZN12createPlugin`. Mark plugin entry points `extern "C"`.

## In LDS

`design_patterns/factory/include/factory.hpp`
`plugins/src/sample_plugin.cpp` + `include/dir_monitor.hpp`

LDS's plugin system uses `dlopen`/`dlsym` as a factory. The plugin monitor watches a directory for new `.so` files. When one appears, it calls `dlopen` + `dlsym("createPlugin")` to instantiate the plugin. The LDS core never imports a plugin header — it only knows `IPlugin`. This is the Factory pattern enabling runtime extensibility without recompilation.

## Validate

1. LDS loads a plugin with `dlopen`. The plugin's `IPlugin*` is stored. Before calling `dlclose`, you delete the `IPlugin*`. Why must you delete the object BEFORE `dlclose`?
2. The factory returns `shared_ptr<IDriverComm>`. The caller stores it. The factory goes out of scope. Is the `IDriverComm` object destroyed? Why?
3. You add `UDPDriverComm` to LDS. With the factory pattern, which files do you need to modify? Without the factory?

## Connections

**Theory:** [[Core/Theory/Design Patterns/04 - Factory]]  
**Mental Models:** [[Strategy Pattern — The Machine]], [[Templates — The Machine]], [[Virtual Functions — The Machine]]  
**LDS Implementation:** [[LDS/Linux Integration/Plugin Loading Internals]] — dlopen plugin factory; [[LDS/Application/Plugins]]  
**Runtime Machines:** [[LDS/Runtime Machines/Plugin System — The Machine]]  
**Glossary:** [[Templates]], [[shared_ptr]]
