"""Entry point for the GTK4 / libadwaita interface.

Run from the project venv:

    .venv/bin/python -m app.gtk_main

The venv is configured with ``include-system-site-packages = true`` so it
sees the system PyGObject (``gi``) while keeping the venv's own engine
dependencies (PyMuPDF, …). The bare system ``python3`` also works but has
no PyMuPDF, so PDF conversions would fail there.

Some engines still need their CLI binaries on PATH (pandoc, qpdf,
qrencode, zbarimg); install those separately to enable ebook / QR / the
qpdf-backed PDF operations.
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
