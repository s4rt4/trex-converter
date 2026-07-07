#!/bin/bash
# Build the t-rex-converter RPM (GTK4 front-end).
#
# Run from anywhere:
#     ./packaging/build-rpm.sh
#
# Uses a throwaway _topdir under ./build/rpm, sources the tarball from
# `git archive HEAD` (so only committed files are packaged), and reads
# the version from app/__init__.py — the single source of truth.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

command -v rpmbuild >/dev/null 2>&1 || {
    echo "error: rpmbuild missing — install the 'rpm-build' package" >&2
    exit 1
}

VERSION="$(python3 - <<'EOF'
import pathlib, re
text = pathlib.Path("app/__init__.py").read_text()
print(re.search(r'__version__ = "([^"]+)"', text).group(1))
EOF
)"

TOP="$ROOT/build/rpm"
rm -rf "$TOP"
mkdir -p "$TOP"/{SOURCES,SPECS,BUILD,RPMS,SRPMS}

git archive --format=tar.gz --prefix="t-rex-converter-$VERSION/" \
    -o "$TOP/SOURCES/t-rex-converter-$VERSION.tar.gz" HEAD

rpmbuild -bb \
    --define "_topdir $TOP" \
    --define "app_version $VERSION" \
    "$ROOT/packaging/t-rex-converter.spec"

echo
echo "Built RPMs:"
find "$TOP/RPMS" -name '*.rpm' -exec ls -lh {} \;
