#!/usr/bin/env python3
"""
Generate a Dockerfile from a config.json.

Usage:
    # Users — base derived from folder structure, passed as CLI arg:
    python3 generate-dockerfile.py <config.json> <registry> <image> <base>

    # Teams — base declared inside config.json:
    python3 generate-dockerfile.py <config.json> <registry> <image>

Outputs the Dockerfile to stdout.

config.json schema:
{
    "base": "rstudio",            // required for teams; ignored for users (derived from path)
    "apt":  ["libgdal-dev"]       // optional
}
"""

import json
import sys


VALID_BASES = {"codeoss", "rstudio"}
DEFAULT_TAG = "codeoss-locked--rstudio-locked"


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) not in (4, 5):
        fail("Usage: generate-dockerfile.py <config.json> <registry> <image> [base]")

    config_path, registry, image = sys.argv[1], sys.argv[2], sys.argv[3]
    cli_base = sys.argv[4] if len(sys.argv) == 5 else None

    with open(config_path) as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as e:
            fail(f"Invalid JSON in {config_path}: {e}")

    base = cli_base or config.get("base")
    if not base:
        fail('"base" is required in config.json for team images (valid values: codeoss, rstudio)')
    if base not in VALID_BASES:
        fail(f"Base image '{base}' is not valid. Must be one of: {sorted(VALID_BASES)}")

    apt_pkgs = config.get("apt", [])

    lines = [
        f"FROM {registry}/{image}/{base}:{DEFAULT_TAG}",
        "",
    ]

    if apt_pkgs:
        pkg_str = " \\\n        ".join(apt_pkgs)
        lines += [
            "RUN apt-get update && \\",
            "    apt-get install -y --no-install-recommends \\",
            f"        {pkg_str} && \\",
            "    rm -rf /var/lib/apt/lists/*",
            "",
        ]

    print("\n".join(lines))


if __name__ == "__main__":
    main()
