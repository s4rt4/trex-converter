from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
from importlib.util import find_spec

from app.utils.logger import configure_logging


# Python modules whose absence makes the app unusable. The values are the
# install names (which may differ from the import name).
REQUIRED_PYTHON_DEPS: tuple[tuple[str, str], ...] = (
    ("PySide6", "PySide6"),
    ("qasync", "qasync"),
    ("fitz", "PyMuPDF"),
    ("qtawesome", "qtawesome"),
)

# Optional Python modules — affect a single feature, not whole-app launch.
OPTIONAL_PYTHON_DEPS: tuple[tuple[str, str, str], ...] = (
    ("pdf2docx", "pdf2docx", "PDF -> DOCX conversion"),
)

# Engine binaries grouped by the user-facing module they back. These are
# Recommends in the .deb so they may be missing on a stripped install.
RECOMMENDED_BINARIES: tuple[tuple[str, str], ...] = (
    ("ffmpeg", "Video and Audio modules"),
    ("magick", "Image module (ImageMagick)"),
    ("libreoffice", "Document and Slides modules"),
    ("qpdf", "PDF repair / linearize"),
    ("tesseract", "OCR module"),
    ("inkscape", "SVG / Vector module"),
    ("potrace", "SVG pixmap-to-vector trace"),
    ("pandoc", "Ebook module"),
    ("exiftool", "Metadata module"),
    ("qrencode", "QR generate"),
    ("zbarimg", "QR / barcode decode"),
)

INSTALL_HINT_APT_PYTHON = (
    "sudo apt install python3-pyside6.qtwidgets python3-pymupdf \\\n"
    "  python3-qasync python3-qtawesome"
)
INSTALL_HINT_PIP_PDF2DOCX = (
    "sudo pip install --break-system-packages pdf2docx\n"
    "    # or in a venv:\n"
    "    python3 -m venv --system-site-packages ~/.venv-trex && \\\n"
    "      ~/.venv-trex/bin/pip install pdf2docx"
)
INSTALL_HINT_APT = (
    "sudo apt install ffmpeg imagemagick libreoffice qpdf tesseract-ocr \\\n"
    "  inkscape potrace pandoc libimage-exiftool-perl qrencode zbar-tools \\\n"
    "  python3-tinycss2"
)


def _missing_python_deps() -> list[tuple[str, str]]:
    return [
        (mod, pkg)
        for mod, pkg in REQUIRED_PYTHON_DEPS
        if find_spec(mod) is None
    ]


def _missing_binaries() -> list[tuple[str, str]]:
    return [
        (binary, label)
        for binary, label in RECOMMENDED_BINARIES
        if shutil.which(binary) is None
    ]


def _missing_optional_python_deps() -> list[tuple[str, str, str]]:
    return [
        (mod, pkg, label)
        for mod, pkg, label in OPTIONAL_PYTHON_DEPS
        if find_spec(mod) is None
    ]


def _show_fatal_error(title: str, message: str) -> None:
    """Surface a fatal error to the user when even the GUI toolkit is missing.

    Tries zenity first (common on GNOME-derived desktops), falls back to
    xmessage, and finally prints to stderr.
    """
    print(f"{title}\n\n{message}", file=sys.stderr)
    if shutil.which("zenity"):
        subprocess.run(
            ["zenity", "--error", f"--title={title}", f"--text={message}", "--width=520"],
            check=False,
        )
        return
    if shutil.which("xmessage"):
        subprocess.run(
            ["xmessage", "-center", "-buttons", "OK", f"{title}\n\n{message}"],
            check=False,
        )


def _show_qt_dialog(
    *, title: str, summary: str, detail: str, fatal: bool
) -> bool:
    """Show a Qt dialog. Returns True when the user chose to continue."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QMessageBox

    owns_app = QApplication.instance() is None
    app = QApplication.instance() or QApplication(sys.argv)
    box = QMessageBox()
    box.setIcon(QMessageBox.Icon.Critical if fatal else QMessageBox.Icon.Warning)
    box.setWindowTitle(title)
    box.setText(summary)
    box.setDetailedText(detail)
    box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    if fatal:
        box.setStandardButtons(QMessageBox.StandardButton.Close)
    else:
        box.setStandardButtons(
            QMessageBox.StandardButton.Ignore | QMessageBox.StandardButton.Close
        )
        box.setDefaultButton(QMessageBox.StandardButton.Ignore)
    choice = box.exec()
    if owns_app:
        # Drop the temporary QApplication so the real run can build a fresh one.
        del app
    return choice == QMessageBox.StandardButton.Ignore


def _format_python_deps_message(missing: list[tuple[str, str]]) -> tuple[str, str]:
    apt_pkgs = {
        "PySide6": "python3-pyside6.qtwidgets",
        "PyMuPDF": "python3-pymupdf",
        "qasync": "python3-qasync",
        "qtawesome": "python3-qtawesome",
    }
    apt_missing = [apt_pkgs[pkg] for _, pkg in missing if pkg in apt_pkgs]
    pip_missing = [pkg for _, pkg in missing if pkg not in apt_pkgs]

    parts = [
        "T-Rex Converter cannot start because required Python "
        "dependencies are missing.",
        "",
        "Missing modules:",
        *(f"  - {pkg}" for _, pkg in missing),
        "",
    ]
    if apt_missing:
        parts.extend([
            "Install via apt (recommended on Debian / Ubuntu):",
            "",
            "    sudo apt install " + " \\\n      ".join(apt_missing),
            "",
        ])
    if pip_missing:
        parts.extend([
            "Install via pip (these are not in Debian apt):",
            "",
            "    " + INSTALL_HINT_PIP_PDF2DOCX
            if pip_missing == ["pdf2docx"]
            else "    sudo pip install --break-system-packages "
            + " ".join(pip_missing),
            "",
        ])
    summary = "\n".join(parts)
    detail = "Python module -> install package\n" + "\n".join(
        f"  {mod} -> {apt_pkgs.get(pkg, pkg + ' (pip)')}"
        for mod, pkg in missing
    )
    return summary, detail


def _preflight_checks() -> bool:
    """Run dep checks before building the main window. Returns False to abort."""
    missing_py = _missing_python_deps()
    if missing_py:
        # If PySide6 itself is missing we can't show a Qt dialog. Fall back.
        pyside_missing = any(mod == "PySide6" for mod, _ in missing_py)
        summary, detail = _format_python_deps_message(missing_py)
        if pyside_missing:
            _show_fatal_error("T-Rex Converter — missing dependencies", f"{summary}\n\n{detail}")
        else:
            _show_qt_dialog(
                title="T-Rex Converter — missing dependencies",
                summary=summary,
                detail=detail,
                fatal=True,
            )
        return False

    missing_bin = _missing_binaries()
    missing_opt = _missing_optional_python_deps()
    if missing_bin or missing_opt:
        summary, detail = _format_optional_message(missing_bin, missing_opt)
        keep_going = _show_qt_dialog(
            title="T-Rex Converter — optional dependencies missing",
            summary=summary,
            detail=detail,
            fatal=False,
        )
        if not keep_going:
            return False
    return True


def _format_optional_message(
    missing_bin: list[tuple[str, str]],
    missing_opt: list[tuple[str, str, str]],
) -> tuple[str, str]:
    parts = [
        "Some optional dependencies are missing. The app still launches, "
        "but the affected features below will fail if you try them.",
        "",
    ]
    if missing_bin:
        parts.append("Missing engine binaries:")
        parts.extend(f"  - {b} ({label})" for b, label in missing_bin)
        parts.append("")
        parts.append("Install on Debian / Ubuntu:")
        parts.append("")
        parts.append("    " + INSTALL_HINT_APT)
        parts.append("")
    if missing_opt:
        parts.append("Missing optional Python modules:")
        parts.extend(f"  - {pkg} ({label})" for _, pkg, label in missing_opt)
        parts.append("")
        parts.append("Install pdf2docx (not in Debian apt):")
        parts.append("")
        parts.append("    " + INSTALL_HINT_PIP_PDF2DOCX)
        parts.append("")
    parts.append("Click Ignore to continue, Close to quit.")
    detail = "\n".join(
        [f"{b}\t{label}" for b, label in missing_bin]
        + [f"{pkg}\t{label}" for _, pkg, label in missing_opt]
    )
    return "\n".join(parts), detail


def main() -> int:
    configure_logging()

    if not _preflight_checks():
        return 1

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from qasync import QEventLoop
    from app.ui.main_window import MainWindow

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
