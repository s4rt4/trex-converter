#!/usr/bin/env bash
# Launch the GTK4 / libadwaita interface from the project venv.
#
# Always uses .venv (which sees the system gi/PIL plus its own fitz/PySide6)
# and sets PYTHONPATH, so it works regardless of which shell/python is
# active. Just run:  ./run-gtk.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$REPO_ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "venv python not found at $PYTHON" >&2
    echo "Create it first:  python3 -m venv .venv  (then install deps)" >&2
    exit 1
fi

exec env PYTHONPATH="$REPO_ROOT" "$PYTHON" -m app.gtk_main "$@"
