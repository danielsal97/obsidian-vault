# Decision: Why IN_CLOSE_WRITE (not IN_CREATE) for Plugin Detection

## Decision

Use `IN_CLOSE_WRITE` inotify event, not `IN_CREATE`, to trigger plugin loading.

---

## The Problem with IN_CREATE

```
Timeline of "cp plugin.so /tmp/pnp_plugins/":

t=0ms   open() creates the file         → IN_CREATE fires ← too early!
t=0ms   write() starts copying bytes
t=5ms   write() continues...
t=10ms  write() finishes
t=10ms  close() is called               → IN_CLOSE_WRITE fires ← correct
```

If `dlopen()` is called at `IN_CREATE` (t=0ms):
- The file exists but is **empty or partially written**
- `dlopen` either fails or loads corrupt data
- The plugin system breaks silently

---

## Why IN_CLOSE_WRITE is Safe

`IN_CLOSE_WRITE` fires **after the last `write()` AND the `close()` system call**.

At this point:
- All bytes are on disk (or at least in the page cache)
- The file descriptor is closed
- The file is complete and consistent
- `dlopen()` will succeed and load the correct binary

---

## In the Code

```cpp
// plugins/src/dir_monitor.cpp — inotify watch setup:
inotify_add_watch(fd, path, IN_CLOSE_WRITE | IN_DELETE);
//                          ↑ only trigger after close, not create

// DirMonitorHandler filters for .so:
if (event->mask & IN_CLOSE_WRITE && endswith(event->name, ".so")) {
    dispatcher.NotifyAll(path);
}
```

---

## Analogous Pattern in Other Systems

This same issue appears everywhere files are written and then consumed:

| System | Wrong event | Correct event |
|---|---|---|
| inotify plugin loading | IN_CREATE | IN_CLOSE_WRITE |
| S3 object processing | ObjectCreated:Put (partial) | ObjectCreated:CompleteMultipartUpload |
| Log rotation | File rename | fsync + rename |
| Database WAL | Write start | Write commit |

The pattern: always wait for the **completion signal**, not the **start signal**.

---

## Related Notes
- [[DirMonitor]]
- [[PNP]]
- [[Observer]]
