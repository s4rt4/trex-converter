from __future__ import annotations

import sys
import asyncio

from app.utils.logger import configure_logging


def main() -> int:
    configure_logging()
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication
        from qasync import QEventLoop
        from app.ui.main_window import MainWindow
    except ImportError as exc:
        print(
            "PySide6 is required to run the GUI. Install with: "
            "pip install -e .",
            file=sys.stderr,
        )
        print(f"Import error: {exc}", file=sys.stderr)
        return 1

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
    app = QApplication(sys.argv)
    _apply_light_palette(app)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    with loop:
        loop.run_forever()
    return 0


def _apply_light_palette(app) -> None:
    from PySide6.QtGui import QColor, QPalette
    from app.ui.theme import (
        BRAND_ACCENT,
        BRAND_DARK,
        BRAND_SURFACE,
        BRAND_SURFACE_MUTED,
        BRAND_SURFACE_SOFT,
        BRAND_TEXT,
    )

    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BRAND_SURFACE))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(BRAND_TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(BRAND_SURFACE_SOFT))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(BRAND_SURFACE_MUTED))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(BRAND_SURFACE_SOFT))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(BRAND_TEXT))
    palette.setColor(QPalette.ColorRole.Text, QColor(BRAND_TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(BRAND_SURFACE_SOFT))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(BRAND_TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(BRAND_ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(BRAND_DARK))
    app.setPalette(palette)


if __name__ == "__main__":
    raise SystemExit(main())
