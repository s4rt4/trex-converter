"""Data model for the sidebar navigation.

The destinations and their grouping mirror ``SIDEBAR_GROUPS`` in the old
Qt ``app.ui.main_window``, so both UIs expose the same set of converters
in the same order. Titles are the user-facing names (sentence case, one
language per the house style); ``icon`` is a *logical* name resolved
through :mod:`app.ui_gtk.icons`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NavItem:
    id: str
    title: str
    icon: str


@dataclass(frozen=True, slots=True)
class NavGroup:
    title: str
    items: tuple[NavItem, ...]


# Standalone destination shown above the grouped converters.
DASHBOARD = NavItem("dashboard", "Dashboard", "dashboard")

# Converter destinations, grouped exactly like the Qt sidebar. Every item
# uses its group's logical icon for now; per-item icons can be refined
# once the Lucide set is in place.
NAV_GROUPS: tuple[NavGroup, ...] = (
    NavGroup("Image", (
        NavItem("image", "Image", "image"),
        NavItem("image-montage", "Image montage", "image-montage"),
        NavItem("svg", "SVG / Vector", "svg"),
    )),
    NavGroup("Video", (
        NavItem("video", "Video", "video"),
        NavItem("video-concat", "Video concat", "video-concat"),
    )),
    NavGroup("Audio", (
        NavItem("audio", "Audio", "audio"),
        NavItem("audio-mix", "Audio mix", "audio-mix"),
    )),
    NavGroup("Document", (
        NavItem("document", "Document", "document"),
        NavItem("document-merge", "Document merge", "document-merge"),
        NavItem("ebook", "Ebook", "ebook"),
        NavItem("slides-to-images", "Slides to images", "slides-to-images"),
    )),
    NavGroup("PDF", (
        NavItem("pdf", "PDF tools", "pdf"),
        NavItem("pdf-merge", "PDF merge", "pdf-merge"),
        NavItem("pdf-split", "PDF split", "pdf-split"),
        NavItem("pdf-numbering", "PDF numbering", "pdf-numbering"),
        NavItem("pdf-extract-images", "PDF extract images", "pdf-extract-images"),
        NavItem("pdf-extract-attachments", "PDF extract attachments", "pdf-extract-attachments"),
        NavItem("pdf-compare", "PDF compare", "pdf-compare"),
    )),
    NavGroup("Subtitle", (
        NavItem("subtitle", "Subtitle", "subtitle"),
        NavItem("subtitle-merge", "Subtitle merge", "subtitle-merge"),
        NavItem("subtitle-extract", "Subtitle extract", "subtitle-extract"),
    )),
    NavGroup("Archive", (
        NavItem("archive", "Archive", "archive"),
        NavItem("archive-compress", "Archive compress", "archive-compress"),
    )),
    NavGroup("Utility", (
        NavItem("ocr", "OCR", "ocr"),
        NavItem("qr", "QR / Barcode", "qr"),
        NavItem("metadata", "Metadata", "metadata"),
    )),
)


def all_items() -> list[NavItem]:
    """Flat list of every navigable destination, in display order."""
    items = [DASHBOARD]
    for group in NAV_GROUPS:
        items.extend(group.items)
    return items


def find_item(item_id: str) -> NavItem | None:
    for item in all_items():
        if item.id == item_id:
            return item
    return None
