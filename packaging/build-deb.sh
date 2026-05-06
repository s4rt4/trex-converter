#!/bin/bash
# Build the t-rex-converter .deb package using dpkg-buildpackage.
#
# Run from the project root:
#     ./packaging/build-deb.sh
#
# The build expects the standard Debian packaging layout: it copies
# packaging/debian/ to a fresh ./debian/ at the repo root (where dh expects
# it), invokes dpkg-buildpackage, then cleans up. The resulting .deb,
# .changes, .buildinfo, and source artefacts land in the parent directory
# of the project (Debian convention).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -d "$ROOT/debian" ] && [ ! -L "$ROOT/debian" ]; then
    echo "error: $ROOT/debian already exists; refusing to overwrite" >&2
    exit 1
fi

ln -snf packaging/debian "$ROOT/debian"
trap 'rm -f "$ROOT/debian"' EXIT

if ! command -v dpkg-buildpackage >/dev/null 2>&1; then
    echo "error: dpkg-buildpackage missing — install the 'dpkg-dev' package" >&2
    exit 1
fi

# -us / -uc: skip GPG signing (the user can sign later with debsign).
# -b:       build only the binary package (no source tarball expected).
dpkg-buildpackage -us -uc -b "$@"

echo
echo "Built artefacts (one directory above project root):"
ls -1 "$ROOT/.." | grep -E '^t-rex-converter_.*\.(deb|changes|buildinfo)$' || true
