# Inotify_cpp (`/utils/Inotify_cpp`)

## Purpose

A set of C++ classes encapsulating the functionality of the C-language inotify library.

Inotify_cpp creates an **event-driven interface** to the Linux inotify API, allowing a developer to hook into filesystem events without the hassle of implementing a read-handle loop or directly manipulating file descriptors.

Instead, monitoring a filesystem is as easy as writing an event handler and attaching it to a watch.

## Usage

```cpp
#include <iostream>
#include <thread>
#include "InotifyManager.h"

class MyEventHandler : public InotifyEventHandler {
    bool handle(InotifyEvent &e) {
        if (e.getFlags() & IN_CREATE)
            std::cout << "Created: " << e.getName() << std::endl;
        else if (e.getFlags() & IN_DELETE)
            std::cout << "Deleted: " << e.getName() << std::endl;
        return false;  // return true to stop watching
    }
};

int main(int argc, char *argv[]) {
    InotifyManager m;
    MyEventHandler h;
    InotifyWatch *w = m.addWatch(argv[1], IN_CREATE | IN_DELETE);
    w->addEventHandler(h);
    thread t = m.startWatching();
    t.join();
    return 0;
}
```

## Current Features

Implements all functionality of the standard C inotify API, except:
- Cookie handling for move/rename events (not yet present)
- Watches cannot yet be removed or modified

## Planned Features

- Simple event checking without manipulating flags
- Abstraction of the `IN_MOVED_FROM`/`IN_MOVED_TO` events' cookie
- Inherent support for recursive watches
- Warning events when approaching watch limit

## Relationship to DirMonitor

[[DirMonitor]] wraps Inotify_cpp to provide the high-level filesystem event dispatch used by [[PNP]].

## Related Notes
- [[DirMonitor]]
- [[Utils Helpers]]
- [[Observer]]

---

**Location**: `utils/Inotify_cpp/` | **Type**: Third-party utility (C++ inotify wrapper)
