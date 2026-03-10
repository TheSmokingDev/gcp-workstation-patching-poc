# Contributing a Workstation Image

This repo lets individuals and teams submit custom Docker images that get automatically built and hardened when you open a PR.

## How it works

1. You create a folder under `users/` (personal) or `teams/` (shared) and add a `Dockerfile`
2. You open a PR
3. CI builds your image, applies a mandatory hardening layer on top, and pushes it to Artifact Registry
4. A bot comments the final image tag on your PR so you can pull and test it

---

## Personal images (`users/`)

Images are organised by **environment first**, then your S-number, then image name. Place your Dockerfile in the environment you want to deploy to.

```
users/
├── dev/
│   └── s12345/              ← your S-number
│       ├── r-geospatial/    ← image name (you choose)
│       │   └── Dockerfile
│       └── python-ml/
│           └── Dockerfile
├── preprod/
│   └── s12345/
│       └── r-geospatial/
│           └── Dockerfile
└── prod/
    └── s12345/
        └── r-geospatial/
            └── Dockerfile
```

Branch name convention: `user/s12345/{env}/my-description`

---

## Team images (`teams/`)

Same structure as users — environment first, then team name, then image name.

```
teams/
├── dev/
│   └── data-science/        ← team name
│       ├── base/
│       │   └── Dockerfile
│       └── gpu-workbench/
│           └── Dockerfile
├── preprod/
│   └── data-science/
│       └── base/
│           └── Dockerfile
└── prod/
    └── data-science/
        └── base/
            └── Dockerfile
```

Branch name convention: `team/data-science/{env}/my-description`

Team folders are shared — coordinate with your team before making changes to an existing image.

---

## Steps

### 1. Create your Dockerfile

Image names must be lowercase and may only contain letters, digits, and hyphens (`-`).

Your `Dockerfile` must start `FROM` a base image. The recommended starting point is a published platform image from this repo:

```dockerfile
FROM us-central1-docker.pkg.dev/my-project/workstation-images/codeoss:codeoss-locked--rstudio-locked

# your additions below
RUN apt-get update && \
    apt-get install -y --no-install-recommends my-tool && \
    rm -rf /var/lib/apt/lists/*
```

Available platform tags:

| Tag | Code OSS downloads | RStudio downloads |
|---|---|---|
| `codeoss-locked--rstudio-locked` | blocked | blocked |
| `codeoss-locked--rstudio-open` | blocked | allowed |
| `codeoss-open--rstudio-locked` | allowed | blocked |
| `codeoss-open--rstudio-open` | allowed | allowed |

You can use any base image, but images not derived from the project base will still have the hardening layer applied on top.

### 2. Open a pull request

- Only change files inside your own folder (`users/<your-snumber>/` or `teams/<your-team>/`)
- PRs that touch files outside your folder will be rejected
- Multiple Dockerfiles in one PR are supported — each gets its own parallel build

### 3. Wait for CI

The pipeline that runs depends on which environment folder your Dockerfile is in:

| Folder | Workflow | Registry |
|---|---|---|
| `users/dev/**` or `teams/dev/**` | `deploy-dev.yml` | `DEV_REGISTRY` |
| `users/preprod/**` or `teams/preprod/**` | `deploy-preprod.yml` | `PREPROD_REGISTRY` |
| `users/prod/**` or `teams/prod/**` | `deploy-prod.yml` | `PROD_REGISTRY` (requires reviewer approval) |

Each pipeline:
1. Detects changed Dockerfiles in your PR
2. Builds each one for `linux/amd64`
3. Applies the mandatory hardening layer via the shared `build-harden-push` action
4. Pushes the hardened image to the environment's Artifact Registry
5. Comments the image tag on your PR

Example bot comment:

```
### ✅ Hardened image built for `teams/dev/data-science/base`
docker pull us-central1-docker.pkg.dev/my-dev-project/workstation-images/codeoss/teams/dev/data-science/base:pr-42-hardened
```

### 4. Pull and verify

```bash
docker pull us-central1-docker.pkg.dev/my-dev-project/workstation-images/codeoss/users/dev/s12345/r-geospatial:pr-42-hardened
docker run --rm -it <image> bash
```

---

## Prerequisites for compatibility with the base image

The platform Dockerfile lives in [`platform/Dockerfile`](platform/Dockerfile). It is built by CI and published to Artifact Registry — you do not need to modify it.

The base image is Ubuntu Noble (`linux/amd64`) and runs two services at startup:

| Service | Port | Startup script |
|---|---|---|
| Code OSS (VS Code) | 80 | managed by the base image |
| RStudio Server | 8787 | `/etc/workstation-startup.d/210_start-rstudio.sh` |

Your `Dockerfile` must meet the following requirements to stay compatible:

**Package management**
- Use `apt-get` (Debian/Ubuntu). Do not use `yum`, `dnf`, `apk`, or other package managers.
- Always pair `apt-get update` with your `apt-get install` in the same `RUN` step.
- Always append `&& rm -rf /var/lib/apt/lists/*` to keep the image lean.
- Always use `--no-install-recommends`.

```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends my-tool && \
    rm -rf /var/lib/apt/lists/*
```

**User context**
- The container runs as `user` (non-root). Your additions should work under this user.
- Do not add `USER root` without switching back, and do not add `USER 0`.
- Do not add your user to sudoers — `sudo` is removed by the hardening layer.

**Startup scripts**
- Startup scripts live in `/etc/workstation-startup.d/` and run in filename order at boot.
- Do not delete or overwrite existing scripts (`100_*`, `210_*`).
- If you need to run something at startup, add a new script with a unique prefix, e.g. `220_my-tool.sh`.

**Ports**
- Ports 80 and 8787 are reserved. Do not bind any service to these ports.

**Architecture**
- Images are built for `linux/amd64` only. Do not use base images or binaries that are `arm64`-only.

**Layer hygiene**
- Do not `COPY` or `ADD` large binary blobs — install from apt or a verified release URL.
- Do not embed credentials, tokens, or `.env` files in any layer.

---

## Rules

- **One folder per person / team.** User folders must be named `s` + digits (e.g. `s12345`). Team folders use a lowercase hyphenated name (e.g. `data-science`).
- **Only modify your own folder.** PRs touching files outside your folder will be rejected.
- **No privilege escalation.** Do not install `sudo`, add capabilities, or modify `/etc/sudoers`. The hardening layer removes these regardless, but PRs containing them will be flagged for review.
- **No secrets in the Dockerfile.** Do not embed passwords, tokens, or credentials. Use Secret Manager at runtime.
- **Images must build for `linux/amd64`.**

---

## What the hardening layer applies

Applied automatically on top of every image — you do not need to do this yourself:

| Step | Detail |
|---|---|
| OS security patches | `apt-get upgrade` for all available CVE fixes |
| Package removal | `sudo`, `gdebi-core`, `dirmngr`, `software-properties-common` removed |
| sudo disabled | Binary removed and sudoers drop-in added as belt-and-suspenders |
| SUID/SGID strip | Setuid bits removed from non-essential binaries |
| Restrictive umask | `umask 027` — new files default to `640` |
| Core dumps disabled | Hard/soft core limit set to 0, `suid_dumpable=0` |
| iptables egress | Outbound restricted to DNS + HTTP/S only (requires `NET_ADMIN` cap at runtime) |

---

## Need help?

Open an issue or ask in the team channel.
