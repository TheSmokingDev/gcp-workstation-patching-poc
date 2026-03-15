FROM us-central1-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest

# ── pyenv ────────────────────────────────────────────────────────────────────
# Install build dependencies required to compile any Python version via pyenv
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libncursesw5-dev \
        libxml2-dev \
        libxmlsec1-dev \
        libffi-dev \
        liblzma-dev \
        xz-utils \
        tk-dev \
        git \
        curl && \
    rm -rf /var/lib/apt/lists/*

ENV PYENV_ROOT=/opt/pyenv
ENV PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"

RUN git clone --depth=1 https://github.com/pyenv/pyenv.git "$PYENV_ROOT" && \
    chown -R user:user "$PYENV_ROOT"

# Make pyenv available in interactive and login shells
RUN echo 'export PYENV_ROOT=/opt/pyenv' > /etc/profile.d/pyenv.sh && \
    echo 'export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"' >> /etc/profile.d/pyenv.sh && \
    echo 'eval "$(pyenv init -)"' >> /etc/profile.d/pyenv.sh && \
    chmod +x /etc/profile.d/pyenv.sh

ARG BLOCK_CODEOSS_DOWNLOADS=true

# Hide the "Download..." context menu item via CSS
RUN if [ "$BLOCK_CODEOSS_DOWNLOADS" = "true" ]; then \
    sed -i 's|</head>|<style>li.action-item:has([aria-label="Download..."]){display:none !important;}</style></head>|' \
        /opt/code-oss/out/vs/code/browser/workbench/workbench.html; \
fi

# Neutralize the browser download trigger in the workbench JS
RUN if [ "$BLOCK_CODEOSS_DOWNLOADS" = "true" ]; then \
    WORKBENCH_JS="/opt/code-oss/out/vs/code/browser/workbench/workbench.js" && \
    sed -i -E 's/([a-zA-Z0-9_]+)\.download=([a-zA-Z0-9_]+),\1\.href=([a-zA-Z0-9_]+),\1\.click\(\)/void 0/g' "$WORKBENCH_JS"; \
fi

ENV USER=user
