ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# ── 1. Apply OS security patches ─────────────────────────────────────────────
RUN apt-get update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# ── 2. Remove high-risk packages ─────────────────────────────────────────────
# sudo allows privilege escalation; remove if present.
# gdebi / dirmngr / software-properties-common are build-time only tools.
RUN apt-get remove -y --purge \
        sudo \
        gdebi-core \
        dirmngr \
        software-properties-common \
        2>/dev/null || true && \
    apt-get autoremove -y 2>/dev/null || true && \
    rm -rf /var/lib/apt/lists/*

# Belt-and-suspenders: remove the sudo binary directly in case it was
# installed outside apt (e.g. copied in by a user Dockerfile layer).
RUN rm -f /usr/bin/sudo /usr/sbin/sudo && \
    echo 'sudo disabled' > /etc/sudoers.d/disable-sudo && \
    chmod 0440 /etc/sudoers.d/disable-sudo

# ── 3. Strip SUID/SGID bits from non-essential binaries ──────────────────────
# Prevents local privilege escalation via setuid executables.
RUN find / -xdev \( -perm -4000 -o -perm -2000 \) -type f \
    ! -path '/usr/bin/passwd' \
    ! -path '/usr/bin/su' \
    ! -path '/usr/bin/newgrp' \
    ! -path '/usr/bin/gpasswd' \
    ! -path '/usr/bin/chsh' \
    ! -path '/usr/bin/chfn' \
    ! -path '/usr/lib/openssh/ssh-keysign' \
    -exec chmod a-s {} + 2>/dev/null || true

# ── 4. Enforce restrictive umask for all sessions ────────────────────────────
# New files default to 640 (owner rw, group r, other none).
RUN echo 'umask 027' >> /etc/profile && \
    echo 'umask 027' >> /etc/bash.bashrc

# ── 5. Restrict core dumps ───────────────────────────────────────────────────
# Core dumps can expose sensitive memory contents.
RUN echo '* hard core 0' >> /etc/security/limits.conf && \
    echo '* soft core 0' >> /etc/security/limits.conf && \
    echo 'fs.suid_dumpable = 0' >> /etc/sysctl.d/99-hardening.conf

# ── 6. iptables egress rules (applied at container startup) ──────────────────
# Writes a startup script that locks down outbound traffic.
# Requires the container to be run with --cap-add NET_ADMIN.
# Allows: DNS (53), HTTP(S) (80/443), RStudio/Code OSS ports (8787, 80).
# Blocks: everything else outbound, preventing arbitrary data exfiltration.
RUN printf '#!/bin/bash\n\
set -e\n\
echo "=== Applying iptables egress rules ==="\n\
\n\
# Flush existing rules\n\
iptables -F OUTPUT 2>/dev/null || { echo "WARN: iptables not available (missing NET_ADMIN cap) - skipping"; exit 0; }\n\
\n\
# Default policy: drop all outbound\n\
iptables -P OUTPUT DROP\n\
\n\
# Allow established/related connections\n\
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT\n\
\n\
# Allow loopback\n\
iptables -A OUTPUT -o lo -j ACCEPT\n\
\n\
# Allow DNS\n\
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT\n\
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT\n\
\n\
# Allow HTTPS (package updates, GCP metadata, auth)\n\
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT\n\
\n\
# Allow HTTP (apt repos over plain HTTP)\n\
iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT\n\
\n\
echo "=== iptables egress rules applied ==="\n' \
    > /etc/workstation-startup.d/100_iptables-hardening.sh && \
    chmod +x /etc/workstation-startup.d/100_iptables-hardening.sh
