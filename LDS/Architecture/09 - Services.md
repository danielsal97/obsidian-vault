# Services (`/services`)

## Purpose

This directory is reserved for **microservice implementations** that will be built on top of the Local Cloud infrastructure. Services are plugins that:
- Register themselves with the service registry
- Discover and communicate with other services
- Implement standardized service interfaces
- Support health checking and monitoring

## Current Status

🔄 **Phase 2 (Service Registry & Discovery) - Design Phase**

## Service Lifecycle (Phase 2)

```
1. Plugin loaded via LDS (Phase 1) ✅
2. Service implements IService interface
3. Service registers with ServiceRegistry
4. Other services discover it by name
5. Communication via MessageBroker (Phase 3)
6. Health checks monitored continuously
7. Auto-scaling via ResourceScheduler (Phase 4)
```

## Service Communication Flow (Phase 3)

```
Service A                 Service B
    │                        │
    ├─ Discover Service B ───┤
    │                        │
    ├─ Send RPC Request ─────┤
    │                        │
    ├─ Wait for Response ◄───┤
```

## Protocol Definitions

### Service Interface
```cpp
class IService {
public:
    virtual ~IService() = default;
    virtual std::string getName() = 0;
    virtual std::string getVersion() = 0;
    virtual ServiceStatus healthCheck() = 0;
    virtual void shutdown() = 0;
};
```

### RPC Message Format (Phase 3)
```json
{
    "id": "msg-123",
    "from": "api-service",
    "to": "database-service",
    "method": "query",
    "params": { "sql": "SELECT * FROM users" },
    "timestamp": 1234567890
}
```

## Communication Layers

```
Layer 4: Application Logic (Services: Database, API, Cache)
Layer 3: RPC Framework (Phase 3) - MessageBroker, Request/Response, Pub/Sub
Layer 2: Network Transport - TCP/IP, Serialization, Encryption (Phase 6)
Layer 1: Plugin System (Phase 1) ✅ - Dynamic Loading, RAII
```

## Service Registration Pattern

```cpp
class DatabaseService : public IService {
public:
    void onServiceLoad() override {
        ServiceRegistry::getInstance()->registerService("database", this);
        startListening();
    }
    void onServiceUnload() override {
        ServiceRegistry::getInstance()->unregisterService("database");
    }
};

__attribute__((constructor)) void init() { new DatabaseService(); }
```

## Features Timeline

| Feature | Phase | Status |
|---------|-------|--------|
| Plugin loading | 1 | ✅ Done |
| Service registration | 2 | 🔄 Planned |
| Service discovery | 2 | 🔄 Planned |
| Health checking | 2 | 🔄 Planned |
| RPC communication | 3 | 📋 Planned |
| Load balancing | 4 | 📋 Planned |
| Service authentication | 6 | 📋 Planned |

## Related Notes
- [[Plugins]]
- [[App Layer]]
- [[System Overview]]
- [[Three-Tier Architecture]]

---

**Phase**: 2 (Service Registry & Discovery) 🔄 | **Depends On**: Phase 1 ✅
