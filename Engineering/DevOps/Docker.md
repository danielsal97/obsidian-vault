# Docker

Containers package an application with everything it needs to run — OS libraries, dependencies, config. Same image runs identically on any machine.

---

## Core Concepts

**Image** — a read-only template (like a class). Built from a `Dockerfile`.  
**Container** — a running instance of an image (like an object). Isolated process with its own filesystem, network, PID namespace.  
**Layer** — each `Dockerfile` instruction creates a layer. Layers are cached and shared between images.  
**Registry** — image storage (Docker Hub, ECR, GCR). `docker pull` fetches from a registry.

---

## Dockerfile

```dockerfile
# Base image — choose the smallest that works
FROM ubuntu:22.04

# Install dependencies (one RUN = one layer; chain with && to keep layers small)
RUN apt-get update && apt-get install -y \
    g++ \
    make \
    libgtest-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy source files (COPY <host path> <container path>)
COPY . .

# Build
RUN make

# Command to run when the container starts
CMD ["./bin/LDS", "tcp", "9999", "134217728"]

# Expose port (documentation only — doesn't actually open the port)
EXPOSE 9999
```

---

## Essential Commands

```bash
# Build an image from Dockerfile in current directory:
docker build -t myapp:latest .
docker build -t myapp:v1.0 -f Dockerfile.prod .

# Run a container:
docker run myapp                         # run and exit
docker run -it myapp bash               # interactive shell
docker run -d myapp                     # detached (background)
docker run -p 9999:9999 myapp           # map host:container port
docker run -v $(pwd)/data:/app/data myapp  # mount host directory

# Container management:
docker ps                # list running containers
docker ps -a             # list all (including stopped)
docker stop <id>         # graceful stop (SIGTERM)
docker kill <id>         # force stop (SIGKILL)
docker rm <id>           # remove stopped container
docker logs <id>         # view stdout/stderr
docker exec -it <id> bash  # shell into running container

# Image management:
docker images            # list local images
docker rmi <image>       # remove image
docker pull ubuntu:22.04 # fetch from registry
docker push myapp:latest # push to registry (need docker login first)
```

---

## Volumes

Containers are ephemeral — their filesystem is destroyed when removed. Volumes persist data.

```bash
# Named volume (Docker manages it):
docker run -v mydata:/app/storage myapp

# Bind mount (host directory → container):
docker run -v /host/path:/container/path myapp
docker run -v $(pwd):/app myapp   # mount current dir — useful for development
```

---

## Networking

```bash
# Default: bridge network — containers get their own IPs
docker run -p 9999:9999 myapp     # host port 9999 → container port 9999

# Host network — container shares host's network stack (no port mapping needed):
docker run --network host myapp

# Connect two containers:
docker network create mynet
docker run --network mynet --name server myapp
docker run --network mynet --name client myclient
# 'client' can reach 'server' by hostname 'server'
```

---

## Docker Compose

Define multi-container applications in `docker-compose.yml`.

```yaml
version: '3.8'
services:
  lds-master:
    build: .
    ports:
      - "9999:9999"
    volumes:
      - ./data:/app/data

  lds-minion:
    image: lds-minion:latest
    environment:
      - MASTER_HOST=lds-master
      - MASTER_PORT=9999
    depends_on:
      - lds-master
```

```bash
docker-compose up          # start all services
docker-compose up -d       # detached
docker-compose down        # stop and remove containers
docker-compose logs -f     # follow logs from all services
docker-compose build       # rebuild images
```

---

## Layer Caching

Docker caches each layer. If a layer's instruction or inputs haven't changed, it reuses the cache — rebuilds are fast.

**Rule:** put infrequently changing instructions early, frequently changing ones late.

```dockerfile
# GOOD: dependencies change rarely → cached almost always
COPY requirements.txt .
RUN apt-get install ...
# Source code changes frequently → always re-runs
COPY src/ .
RUN make

# BAD: COPY . . invalidates cache for every source change,
# forcing apt-get install to re-run every time
COPY . .
RUN apt-get install ...
```

---

## LDS Docker Setup

LDS has a `Dockerfile` that builds the project and runs it in TCP mode. Useful for:
- Testing on a clean Linux environment from Mac
- Running LDS without installing dependencies on the host
- Simulating the master + multiple minion nodes with docker-compose

```bash
docker build -t lds .
docker run -p 9999:9999 lds
# Then connect from host:
python3 test/integration/test_tcp_client.py --host 127.0.0.1 --port 9999
```

---

## Understanding Check

> [!question]- A container writes a file to `/app/output/result.txt`. After `docker rm`, the file is gone. Why and how do you fix it?
> Containers have an ephemeral writable layer on top of the read-only image. When the container is removed, that layer is destroyed. Fix: mount a volume (`-v $(pwd)/output:/app/output`). Writes go to the host filesystem via the bind mount and survive the container's removal.

> [!question]- You change one line of source code. Docker rebuilds from scratch instead of using the cache. Why?
> `COPY . .` (or similar) appears before the `RUN make` step. Any change to any file in `.` invalidates that layer's cache, and all subsequent layers are rebuilt. Fix: copy only files needed for the expensive step first (e.g., `COPY Makefile .` then `COPY src/ src/`) so unrelated changes don't invalidate the dependency-install layer.

> [!question]- Two containers need to communicate. Container A can't reach container B by IP. What's the problem and fix?
> By default, containers on the default bridge network can reach each other by IP but not by name. Solution: create a named network (`docker network create mynet`), attach both containers to it, then refer to them by their `--name`. Docker's embedded DNS resolves container names to IPs within a named network.

> [!question]- What's the difference between `docker stop` and `docker kill`?
> `docker stop` sends SIGTERM, waits up to 10 seconds for a graceful shutdown, then sends SIGKILL. `docker kill` sends SIGKILL immediately (or a specified signal). For LDS, `docker stop` is correct — it gives the server time to close connections and flush state cleanly.

> [!question]- Why does `-p 9999:9999` work for the LDS TCP server but `EXPOSE 9999` in the Dockerfile alone isn't enough?
> `EXPOSE` is documentation — it tells other developers which port the container intends to use, but it doesn't actually publish the port to the host. `-p host_port:container_port` at `docker run` time is what creates the actual mapping from the host network into the container.
