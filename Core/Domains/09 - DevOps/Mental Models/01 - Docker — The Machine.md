# Docker — The Machine

## The Model
A shipping container system for software. A container is a sealed box containing the application and everything it needs to run (OS libraries, config, binaries) — it runs identically on any machine that has Docker. An image is the blueprint for the box (read-only layers). A container is a running instance (blueprint + writable layer on top). The Dockerfile is the factory instruction sheet.

## How It Moves

```
Dockerfile (instruction sheet):
  FROM ubuntu:22.04            ← base layer (OS)
  RUN apt-get install g++      ← compile layer (adds g++ to the image)
  COPY src/ /app/src/          ← source layer
  RUN make -C /app             ← build layer (compiles LDS)
  CMD ["/app/bin/lds_server"]  ← what to run when container starts

docker build → Image:
  [layer: ubuntu:22.04]        ← shared with other images using same base
  [layer: g++ installed]       ← cached if Dockerfile unchanged above here
  [layer: source files]        ← rebuilds only if source changed
  [layer: compiled binary]     ← rebuilds only if build layer changed

docker run → Container:
  [all image layers — read-only]
  [writable layer — your process's writes go here]
```

**Layer caching:** each `RUN`/`COPY` instruction is a cached layer. If you change line N in the Dockerfile, layers 1 to N-1 are reused from cache — only N and after are rebuilt. This is why you copy `CMakeLists.txt` and install dependencies BEFORE copying source code — dependencies change rarely, source changes constantly.

## The Blueprint

**Optimized LDS Dockerfile:**
```dockerfile
FROM ubuntu:22.04

# Install dependencies first — cached unless this changes:
RUN apt-get update && apt-get install -y \
    g++ cmake make libgtest-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy build files separately — cached unless CMakeLists changes:
COPY CMakeLists.txt /app/
COPY Makefile /app/

# Copy source — invalidates cache on any source change:
COPY src/ /app/src/
COPY include/ /app/include/

WORKDIR /app
RUN make

CMD ["/app/bin/lds_server", "--port", "7800"]
EXPOSE 7800
```

**Key commands:**
```bash
docker build -t lds-server .          # build image
docker run -p 7800:7800 lds-server    # run container, expose port
docker run -v /data:/app/data lds-server  # mount host directory
docker-compose up                     # start multi-container setup
docker exec -it container_id bash     # open shell inside running container
```

**docker-compose for LDS:**
```yaml
services:
  lds-manager:
    build: .
    ports: ["7800:7800"]
    volumes: ["./storage:/app/storage"]
  
  lds-minion-1:
    build: ./minion
    depends_on: [lds-manager]
  
  lds-minion-2:
    build: ./minion
    depends_on: [lds-manager]
```

## Where It Breaks

- **Large image**: installing dev tools in the final image → 1GB+ image. Use multi-stage build: compile in a build image, copy only the binary to a slim runtime image.
- **Wrong layer order**: `COPY src/ .` before `RUN apt-get install` → source change invalidates the expensive apt layer.
- **Volume not mounted**: container writes to `/app/storage` inside the writable layer — data is lost when container dies. Mount a volume for persistence.

## In LDS

No Dockerfile exists yet in the LDS codebase. The integration point would be `Makefile` and the main entry point binary. A basic LDS Dockerfile would:
1. Start from `ubuntu:22.04`
2. Install `g++`, `make`, `libnbd-dev`
3. Copy and build LDS
4. Run `lds_server` with the TCP port exposed

For Phase 2, `docker-compose` would spin up one manager container and N minion containers, all on a shared Docker network — replacing the current manual multi-process setup for testing RAID01 across multiple storage nodes.

## Validate

1. You change one line in `LocalStorage.cpp`. Which Docker layers are rebuilt on `docker build`? Which are served from cache?
2. The LDS server writes storage data to `/app/storage/` inside the container. The container is restarted. Is the data still there? What do you need to add to preserve it?
3. Three minion containers must reach the manager container at `lds-manager:7800`. What Docker feature makes `lds-manager` a valid hostname, and what replaces the need for hardcoded IP addresses?

## Connections

**Theory:** [[01 - Docker]]  
**Mental Models:** [[Processes — The Machine]], [[File Descriptors — The Machine]], [[Networking Overview — The Machine]], [[Make and CMake — The Machine]]  
**LDS Implementation:** [[LDS/DevOps/Build System]] — no Dockerfile yet; integration point is the Makefile and main entry binary; docker-compose would orchestrate manager + minion containers for RAID01 testing
