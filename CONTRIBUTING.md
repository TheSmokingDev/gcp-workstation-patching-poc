# Contributing a Workstation Image

This repo lets individuals and teams submit custom workstation images that get automatically built and hardened when you open a PR.

---

## Personal images (`users/`)

You do not write a Dockerfile. Create a `config.json` under your S-number folder inside the platform image folder you want to build on. CI generates the Dockerfile from it.

```
users/
└── {base-image}/          ← platform to build on: codeoss or rstudio
    └── {snumber}/         ← your S-number (e.g. s12345)
        └── config.json
```

**Example:**
```
users/
└── r-geospatial/
    └── s12345/
        └── config.json
```

The folder name after `users/` determines your base image — it must be `codeoss` or `rstudio`.

**`config.json` schema:**

```json
{
  "apt": ["libgdal-dev", "libproj-dev"]
}
```

| Field | Required | Description |
|---|---|---|
| `apt` | no | apt packages to install on top of the base image |

**Base image options:**

| Folder name | What's included |
|---|---|
| `codeoss` | Code OSS only |
| `rstudio` | Code OSS + R + RStudio Server |

---

## Team images (`teams/`)

Teams can submit either a `config.json` (simple package installs) or a full `Dockerfile` (custom logic). Any team member can open a PR to add or update an image.

```
teams/
└── {team-name}/           ← your team name (e.g. data-science)
    └── {image-name}/      ← image name (you choose)
        └── config.json    ← or Dockerfile
```

**Option A — config.json (recommended for package-only images)**

Same approach as personal images, but `base` is required since it cannot be derived from the path:

```json
{
  "base": "rstudio",
  "apt":  ["libgdal-dev", "libproj-dev"]
}
```

| Field | Required | Description |
|---|---|---|
| `base` | **yes** | Platform image to build on: `codeoss` or `rstudio` |
| `apt` | no | apt packages to install |

**Option B — Dockerfile (for custom logic)**

```
teams/
└── data-science/
    └── gpu-workbench/
        └── Dockerfile
```

Team Dockerfiles must follow the [compatibility prerequisites](#prerequisites-for-team-dockerfiles) below.

---

## Steps

### 1. Create your file(s)

- **Users:** create `users/{image-name}/{snumber}/config.json`
- **Teams:** create `teams/{team-name}/{image-name}/config.json` or `teams/{team-name}/{image-name}/Dockerfile`

Folder and image names must be lowercase and may only contain letters, digits, and hyphens (`-`).

### 2. Open a pull request

- Branch convention (users): `user/{snumber}/{image-name}`
- Branch convention (teams): `team/{team-name}/{image-name}`
- Only change files inside your own folder
- Multiple images in one PR are supported — each builds in parallel

### 3. Wait for CI

On PR open, the relevant pipeline runs automatically:

| What changed | Workflow |
|---|---|
| `users/**/config.json` | `deploy-users.yml` |
| `teams/**/Dockerfile` | `deploy-teams.yml` |

Each pipeline:
1. Detects all changed files in the PR
2. Builds each image for `linux/amd64`
3. Applies the mandatory hardening layer
4. Pushes the hardened image to Artifact Registry
5. Comments the pull image command on your PR

Example bot comment:
```
### ✅ Image built for `users/r-geospatial/s12345`
docker pull us-central1-docker.pkg.dev/my-project/workstation-images/codeoss/users/r-geospatial/s12345:pr-42-hardened
```

### 4. Pull and verify

```bash
docker pull <image-from-bot-comment>
docker run --rm -it <image> bash
```

---

## Prerequisites for team Dockerfiles

The base images are Ubuntu Noble (`linux/amd64`). Your Dockerfile must start `FROM` one of the published platform images:

```dockerfile
FROM us-central1-docker.pkg.dev/my-project/workstation-images/codeoss/rstudio:codeoss-locked--rstudio-locked

# your additions here
```

**Package management**
- Use `apt-get` only. Do not use `yum`, `dnf`, `apk`, or others.
- Always pair `apt-get update` with `install` in the same `RUN` step and clean up after.

```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends my-tool && \
    rm -rf /var/lib/apt/lists/*
```

**User context**
- The container runs as `user` (non-root).
- Do not add `USER root` without switching back. Do not add to sudoers — `sudo` is removed by the hardening layer.

**Startup scripts**
- Scripts in `/etc/workstation-startup.d/` run in filename order at boot.
- Do not overwrite existing scripts (`100_*`, `210_*`).
- Add your own with a unique prefix, e.g. `220_my-tool.sh`.

**Ports** — 80 and 8787 are reserved.

**Architecture** — `linux/amd64` only.

**Layer hygiene** — no binary blobs, no credentials, no `.env` files in any layer.

---

## Rules

- **Only modify your own folder.** PRs touching files outside your folder will be rejected.
- **No privilege escalation.** Do not install `sudo` or modify `/etc/sudoers`. The hardening layer removes it regardless.
- **No secrets.** Do not embed passwords, tokens, or credentials. Use Secret Manager at runtime.

---

## What the hardening layer applies

Applied automatically on top of every image:

| Step | Detail |
|---|---|
| OS security patches | `apt-get upgrade` for all CVE fixes |
| Package removal | `sudo`, `gdebi-core`, `dirmngr`, `software-properties-common` removed |
| sudo disabled | Binary removed + sudoers drop-in as belt-and-suspenders |
| SUID/SGID strip | Setuid bits removed from non-essential binaries |
| Restrictive umask | `umask 027` — new files default to `640` |
| Core dumps disabled | Hard/soft core limit 0, `suid_dumpable=0` |
| iptables egress | Outbound restricted to DNS + HTTP/S (requires `NET_ADMIN` cap at runtime) |

---

## Need help?

Open an issue or ask in the team channel.
