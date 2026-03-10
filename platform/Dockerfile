FROM us-central1-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest

ARG BLOCK_CODEOSS_DOWNLOADS=true
ARG BLOCK_RSTUDIO_DOWNLOADS=true

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


RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common dirmngr wget && \
    wget -qO- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc \
        > /etc/apt/trusted.gpg.d/cran_ubuntu_key.asc && \
    add-apt-repository "deb https://cloud.r-project.org/bin/linux/ubuntu noble-cran40/" && \
    apt-get update && \
    apt-get install -y --no-install-recommends r-base && \
    rm -rf /var/lib/apt/lists/*

# Block R Shiny file downloads via site-wide R profile
#     Overrides shiny::downloadHandler with a no-op when the shiny package loads,
#     so download buttons/links in any Shiny app will not produce files.
RUN if [ "$BLOCK_RSTUDIO_DOWNLOADS" = "true" ]; then \
    mkdir -p /etc/R && \
    printf '%s\n' \
      'setHook(packageEvent("shiny", "onLoad"), function(...) {' \
      '  blocked_handler <- function(filename, content, contentType = NA, outputArgs = list()) {' \
      '    function(shinysession, name, ...) {' \
      '      invisible(NULL)' \
      '    }' \
      '  }' \
      '  ns <- asNamespace("shiny")' \
      '  unlockBinding("downloadHandler", ns)' \
      '  assign("downloadHandler", blocked_handler, envir = ns)' \
      '  lockBinding("downloadHandler", ns)' \
      '})' >> /etc/R/Rprofile.site; \
fi

# 4) Install RStudio Server (open source, v2026.01.0)
#    Only jammy builds are published; install extra libs for noble compat
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gdebi-core libpq5 libssl3 libsqlite3-0 libpam0g psmisc \
        lsof sudo libclang-dev && \
    wget -q https://download2.rstudio.org/server/jammy/amd64/rstudio-server-2026.01.0-392-amd64.deb -O /tmp/rstudio-server.deb && \
    gdebi --non-interactive /tmp/rstudio-server.deb && \
    rm /tmp/rstudio-server.deb && \
    rm -rf /var/lib/apt/lists/*

# 4b) Build-time verification: check rsession has all shared libs
RUN echo "--- Checking rserver ---" && \
    ldd /usr/lib/rstudio-server/bin/rserver | grep "not found" && exit 1 || true && \
    echo "--- Checking rsession ---" && \
    ldd /usr/lib/rstudio-server/bin/rsession | grep "not found" && exit 1 || true && \
    echo "--- All RStudio shared libraries found ---"

# Hide "Export..." menu item in RStudio Files pane to block file downloads
#     Targets the stable element id="rstudio_label_export_command" inside the More popup menu.
RUN if [ "$BLOCK_RSTUDIO_DOWNLOADS" = "true" ]; then \
    sed -i 's|</head>|<script>(function(){new MutationObserver(function(){var e=document.getElementById("rstudio_label_export_command");if(e){var m=e.closest(".gwt-MenuItem");if(m)m.style.display="none"}}).observe(document.documentElement,{childList:true,subtree:true})})()</script></head>|' \
        /usr/lib/rstudio-server/www/index.htm; \
fi

ENV USER=user

# 5) RStudio Server config
RUN mkdir -p /etc/rstudio && \
    printf 'www-port=8787\nwww-address=0.0.0.0\nserver-user=user\nauth-minimum-user-id=0\nwww-root-path=/\nrsession-which-r=/usr/bin/R\nserver-data-dir=/var/run/rstudio-server\ndatabase-config-file=/etc/rstudio/database.conf\n' \
        > /etc/rstudio/rserver.conf && \
    printf 'session-timeout-minutes=0\n' > /etc/rstudio/rsession.conf && \
    printf 'provider=sqlite\ndirectory=/var/lib/rstudio-server\n' \
        > /etc/rstudio/database.conf

# 6) Prepare runtime directories at build time
RUN mkdir -p /var/run/rstudio-server /var/lib/rstudio-server /var/log/rstudio

# 7) Startup script to launch RStudio Server on port 8787
RUN printf '#!/bin/bash\n\
echo "=== RStudio startup begin ==="\n\
\n\
# Ensure the user account has a proper home and shell\n\
if id -u user >/dev/null 2>&1; then\n\
  mkdir -p /home/user\n\
  chown user:user /home/user || echo "WARN: chown /home/user failed"\n\
  usermod -d /home/user -s /bin/bash user 2>/dev/null || true\n\
else\n\
  useradd -m -d /home/user -s /bin/bash user || echo "WARN: useradd failed"\n\
fi\n\
\n\
# Ensure runtime dirs exist with correct permissions\n\
mkdir -p /var/run/rstudio-server /var/lib/rstudio-server /var/log/rstudio /tmp/rstudio-rsession\n\
chown -R user:user /var/run/rstudio-server /var/lib/rstudio-server /var/log/rstudio /tmp/rstudio-rsession || echo "WARN: chown runtime dirs failed"\n\
chmod 1777 /tmp/rstudio-rsession\n\
\n\
# Check rserver binary\n\
if [ ! -x /usr/lib/rstudio-server/bin/rserver ]; then\n\
  echo "ERROR: rserver binary not found at /usr/lib/rstudio-server/bin/rserver"\n\
  ls -la /usr/lib/rstudio-server/bin/ 2>/dev/null || echo "  directory does not exist"\n\
  exit 1\n\
fi\n\
echo "rserver binary found"\n\
\n\
# Launch rserver\n\
echo "Launching rserver..."\n\
/usr/lib/rstudio-server/bin/rserver --server-daemonize=0 --auth-none=1 \\\n\
  >> /var/log/rstudio/rserver.log 2>&1 &\n\
RSERVER_PID=$!\n\
echo "RStudio Server PID: $RSERVER_PID"\n\
\n\
# Verify it is running\n\
sleep 3\n\
if kill -0 $RSERVER_PID 2>/dev/null; then\n\
  echo "RStudio Server started successfully on port 8787"\n\
else\n\
  echo "ERROR: RStudio Server exited. Log contents:"\n\
  cat /var/log/rstudio/rserver.log 2>/dev/null || echo "  (no log file)"\n\
fi\n\
echo "=== RStudio startup end ==="\n' \
    > /etc/workstation-startup.d/210_start-rstudio.sh && \
    chmod +x /etc/workstation-startup.d/210_start-rstudio.sh
