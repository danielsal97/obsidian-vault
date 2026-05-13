# Docker Setup

## Files Created

| File | Purpose |
|---|---|
| `Dockerfile` | Builds the project inside Ubuntu 22.04 |
| `docker-compose.yml` | Two services: `dev` (development) and `nbd` (full NBD tests) |
| `docker-nbd-setup.sh` | Loads NBD kernel module into Docker Desktop's VM (macOS only) |

---

## Quick Start

```bash
# Build the image (first time or after code changes)
docker build -t lds .

# Interactive shell with your code mounted
docker run -it -v $(pwd):/app lds bash

# Inside container:
make all          # compile
make run_tests    # unit tests (no NBD needed)
```

---

## Linux Features and Docker Support

| Feature | Docker support | Notes |
|---|---|---|
| `epoll` | ✅ Works | Containers share host kernel |
| `inotify` | ✅ Works | No special flags |
| `dlopen` / plugins | ✅ Works | Fine in containers |
| `pthreads` | ✅ Works | Fine |
| NBD `/dev/nbd0` | ⚠️ Needs setup | Requires kernel module + `--privileged` |

---

## Development Workflow

### Without volumes (image includes compiled code):
```bash
docker build -t lds .
docker run -it lds make run_tests
```

### With volumes (edit on Mac, compile in container):
```bash
docker run -it -v $(pwd):/app lds bash
# Edit on Mac → make all inside container → instant rebuild
```

### Using docker-compose:
```bash
docker compose up dev              # start dev container
docker compose exec dev bash       # open shell in running container
docker compose down                # stop everything
```

---

## NBD Testing (Full System)

Only needed for `make test_nbd` — all unit tests run without this.

```bash
# Step 1: Load nbd module into Docker Desktop's Linux VM (macOS)
# Run once after every Docker Desktop restart
./docker-nbd-setup.sh

# Step 2: Start privileged container
docker compose up nbd

# Step 3: Shell in and run NBD tests
docker compose exec nbd bash
  → sudo make test_nbd
```

On a real Linux machine (not macOS):
```bash
sudo modprobe nbd max_part=8
docker run --privileged --device=/dev/nbd0 -v $(pwd):/app lds bash
  → sudo make test_nbd
```

---

## Dockerfile Explained

```dockerfile
FROM ubuntu:22.04          # base Linux environment

ENV DEBIAN_FRONTEND=noninteractive  # no interactive apt prompts

RUN apt-get update && apt-get install -y \
    build-essential \      # gcc, make, etc.
    g++ \                  # C++ compiler
    make \                 # build system
    nbd-client \           # for test_nbd
    sudo \
    && rm -rf /var/lib/apt/lists/*   # keep image small

WORKDIR /app               # cd /app for all following commands

COPY . .                   # copy project into container

RUN make all               # compile at build time

CMD ["bash"]               # default: open shell
```

---

## docker-compose.yml Explained

```yaml
services:
  dev:
    build: .               # use Dockerfile in current dir
    volumes:
      - .:/app             # mount project folder (live edits)
    command: bash

  nbd:
    build: .
    privileged: true       # access kernel features
    devices:
      - /dev/nbd0:/dev/nbd0  # NBD device from host
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    volumes:
      - .:/app
    command: bash
```

---

## Image Size Optimization

Current image: ~500MB (Ubuntu + build tools)

If size matters (e.g., deploying minion to Raspberry Pi):
```dockerfile
# Multi-stage build: compile in one stage, run in minimal stage
FROM ubuntu:22.04 AS builder
RUN apt-get install -y build-essential g++ make
COPY . .
RUN make all

FROM ubuntu:22.04 AS runtime
COPY --from=builder /app/bin/LDS /usr/local/bin/LDS
# Result: ~200MB instead of ~500MB
```

---

## Related Notes
- [[Phase 6 - Optimization & Polish]] (CI/CD section)
- [[System Overview]]
