"""Entry point for the GTK4 / libadwaita interface.

Run with the *system* Python (which provides PyGObject / ``gi``):

    python3 -m app.gtk_main

The project ``.venv`` is PySide6-only and has no ``gi``; see the project
notes for the venv options if you need both in one interpreter.
"""

from __future__ import annotations

import sys

from app.utils.logger import configure_logging


def main() -> int:
    configure_logging()
    from app.ui_gtk.application import TrexApplication

    return TrexApplication().run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
