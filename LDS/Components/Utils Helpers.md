# Utilities & Helpers (`/utils`)

## Purpose

This directory contains **lightweight utility functions and helper classes** that support the main framework. These are general-purpose tools used across the codebase.

## Relationship to `/utilities`

| Directory | Purpose | Scope |
|-----------|---------|-------|
| `/utils` | Lightweight helper functions | Small, reusable utilities |
| `/utilities` | Core framework components | Large, central frameworks |

## Typical Contents

- **String utilities** — parsing, formatting, manipulation
- **File utilities** — path operations, directory handling
- **Conversion functions** — type conversions, serialization
- **Math utilities** — common mathematical operations
- **Memory utilities** — allocation wrappers, smart pointers
- **Time utilities** — timing, scheduling helpers

## Common Patterns

```cpp
// String utilities
namespace StringUtils {
    std::string trim(const std::string& str);
    std::vector<std::string> split(const std::string& str, char delimiter);
}

// File utilities
namespace FileUtils {
    bool fileExists(const std::string& path);
    std::vector<std::string> listDirectory(const std::string& path);
    std::string getBasename(const std::string& path);
}
```

## When to Use

### Use `/utils` for:
- ✅ Simple, focused functionality
- ✅ Reusable across multiple components
- ✅ Not a complete framework
- ✅ Stateless helper functions

### Use `/utilities` for:
- ✅ Complex framework components
- ✅ Components with state/configuration
- ✅ Central services (Logger, Factory)
- ✅ Design pattern implementations

## Adding New Utilities

1. Create new header in `/utils/`
2. Keep implementation simple and focused
3. Make functions reusable
4. Document with clear examples

```cpp
// utils/my_utility.hpp
#pragma once

namespace MyUtility {
    std::string doSomething(const std::string& input);
    int calculateValue(int a, int b);
}
```

## Related Notes
- [[Utilities Framework]]
- [[Inotify]]

---

**Status**: 🔄 Active development | **Complexity**: Low to Medium
