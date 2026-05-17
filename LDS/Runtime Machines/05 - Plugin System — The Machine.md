# LDS Plugin System — The Machine

## The Model
A factory floor that automatically gains new workers when you drop a toolbox in the loading bay. The loading bay is a directory (`plugins/`). A security camera (`DirMonitor`) watches it using inotify — when a new `.so` file drops, it fires an alarm. The alarm goes to a broadcast board (`Dispatcher`). Every subscriber on the board gets the file path. One subscriber — the toolbox loader (`SoLoader`) — picks up the path, opens the toolbox with `dlopen()`, and the new worker is instantly available in the running process. Nobody restarts the factory. Nobody recompiles. The `PNP` class is just the wiring that connects camera → board → loader into one unit.

## How It Moves

```
Construction — PNP(dirPath = "plugins/"):
  m_dirMonitor(dirPath)   ← starts inotify watcher + background thread
  m_soLoader(m_dirMonitor.GetDispatcher())   ← subscribes to the Dispatcher

Inside DirMonitor(dirPath):
  m_manager = InotifyManager(...)         ← creates inotify fd
  m_watch = InotifyWatch(m_manager, dirPath, IN_CLOSE_WRITE | IN_MOVED_IN)
  m_handler = InotifyEventHandler(...)
  m_listener = thread([this]{ /* reads inotify events forever */ })
    ← background thread blocks on read(inotify_fd)
    ← when .so file written/moved in: m_disp.NotifyAll(filename)

Dispatcher<const std::string&>::NotifyAll(path):
  for each ICallBack<const string&>* sub in m_subs:
    sub->Notify(path)
  ← synchronous: iterates all subscribers in the listener thread

Inside SoLoader — constructed with Dispatcher*:
  m_pluginCB = new CallBack<const string&, SoLoader>(disp, *this, &SoLoader::OnLoad)
    ← CallBack registers itself with the Dispatcher on construction
    ← when Notify() is called on the CallBack, it calls this->OnLoad(path)

SoLoader::OnLoad(libPath):
  handle = dlopen(libPath.c_str(), RTLD_LAZY)
  if !handle: throw runtime_error(dlerror())
  m_libs.push_back(handle)   ← RAII: keep handle alive, dlclose in ~SoLoader

Plugin .so file — sample_plugin.cpp:
  extern "C" { void createPlugin() { /* register self with some registry */ } }
  ← extern "C" prevents name mangling — dlsym("createPlugin") finds it by exact name
```

**inotify event flow:**
The kernel's inotify subsystem monitors filesystem events. `IN_CLOSE_WRITE` fires when a file is closed after writing — not on every write (which would fire multiple times during a `cp` operation). `IN_MOVED_IN` fires when a file is atomically moved into the directory (`mv plugin.so plugins/`). Both trigger the same `NotifyAll` broadcast.

**`CallBack` vs raw function pointer:**
`CallBack<const string&, SoLoader>` is a template wrapper that binds a member function (`&SoLoader::OnLoad`) to a specific instance (`*this`). It implements `ICallBack<const string&>` so it can be registered with `Dispatcher`. The `CallBack` is heap-allocated (`new`) and stored as `m_pluginCB` — SoLoader owns it and `delete`s it in the destructor.

**`RTLD_LAZY | RTLD_DEEPBIND`:**
`RTLD_LAZY` — symbol resolution deferred until first call (faster load, fails at call time not load time).
`RTLD_DEEPBIND` (in `Loader.hpp`) — the plugin's own symbol table is searched before the global scope. Prevents plugins from accidentally hijacking symbols in the main binary.

## The Blueprint

```cpp
// plugins/include/pnp.hpp — the wiring:
class PNP {
    DirMonitor m_dirMonitor;   // watches "plugins/" directory
    SoLoader m_soLoader;       // subscribes to DirMonitor's Dispatcher
    Logger* m_logger;
public:
    explicit PNP(const std::string& dirPath = "plugins/");
};

// plugins/include/dir_monitor.hpp — the camera:
class DirMonitor {
    std::string m_dirName;
    std::thread m_listener;            // background inotify thread
    Dispatcher<const std::string&> m_disp;  // the broadcast board
public:
    Dispatcher<const std::string&>* GetDispatcher();
};

// plugins/include/soLoader.hpp — the loader:
class SoLoader {
    std::vector<void*> m_libs;    // all loaded .so handles
    PlugInCB* m_pluginCB;         // CallBack registered with Dispatcher
public:
    explicit SoLoader(Dispatcher<const std::string&>* disp);
    void Load(const std::string& libPath);   // manual load (no directory watch)
};

// plugins/include/loader.hpp — RAII .so handle:
class Loader {
    void* m_handle;   // dlopen result
public:
    explicit Loader(const std::string& path_)
        : m_handle(dlopen(path_.c_str(), RTLD_LAZY | RTLD_DEEPBIND)) {}
    ~Loader() { if (m_handle) dlclose(m_handle); }
};
```

## Where It Breaks

- **`dlopen` after `dlclose`**: if `~SoLoader` is called while the plugin's code is still executing, `dlclose` removes the code from the address space → segfault. Plugins must be cleanly shut down before `SoLoader` destructs.
- **`NotifyAll` in the listener thread**: `OnLoad` runs on the `DirMonitor` background thread, not the main thread. If `OnLoad` accesses shared state (registries, etc.) without locks, this is a data race.
- **Dispatcher destructor calls `NotifyEnd()`**: `~Dispatcher` calls `sub->NotifyEnd()` on all subscribers. If `SoLoader` is already destroyed (its `m_pluginCB` deleted), but the `Dispatcher` still holds the dangling pointer → UB. Destruction order: `SoLoader` first (removes CallBack from Dispatcher), then `DirMonitor`. `PNP`'s member declaration order (`m_dirMonitor` before `m_soLoader`) means `m_soLoader` is destroyed first — which is correct.
- **No `.so` unload path**: once a plugin is loaded, there's no mechanism to unload it (no `IN_DELETE` watching, no `dlclose` on demand). Plugins are permanent for the process lifetime.

## In LDS

`plugins/` directory: `dir_monitor.hpp`, `soLoader.hpp`, `loader.hpp`, `pnp.hpp`, `src/soLoader.cpp`, `src/pnp.cpp`, `src/sample_plugin.cpp`

Observer pattern from `design_patterns/observer/include/Dispatcher.hpp` is used directly here — the plugin system is a live use of the Observer + Command patterns.

Usage in main:
```cpp
PNP pnp("plugins/");   // starts watching, ready to load
// Drop any .so into plugins/ at runtime → auto-loaded
```

`sample_plugin.cpp` demonstrates the required plugin interface:
```cpp
extern "C" { void createPlugin() { /* self-register */ } }
```

## Validate

1. A file `storage_plugin.so` is copied to `plugins/` with `cp`. When exactly does `IN_CLOSE_WRITE` fire? Would it fire during the copy, or after? What would happen if LDS used `IN_CREATE` instead?
2. `SoLoader::OnLoad` runs on the `DirMonitor` background thread. The Reactor's main thread simultaneously calls `mediator.Notify()`. Is there a data race? What shared state could both threads access?
3. `~PNP` destroys `m_soLoader` before `m_dirMonitor` (reverse declaration order). The Dispatcher inside `m_dirMonitor` calls `NotifyEnd()` on the SoLoader's CallBack during `~Dispatcher`. By then, is `m_soLoader.m_pluginCB` still valid? Trace the destruction sequence.

---

## Core Vault Cross-Links

→ [[02 - Observer Pattern — The Machine]] — the Observer pattern DirMonitor uses
→ [[04 - Factory Pattern — The Machine]] — how plugins self-register into the Factory
→ [[Program Startup — The Machine]] — dlopen runs the same ELF loading sequence
