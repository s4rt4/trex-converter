"""Documentation loader.

Topic markdown files live at ``app/docs/<lang>/<slug>.md``. Each file starts
with an H1 heading that becomes the topic title; sub-headings become section
anchors that the search dropdown surfaces.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable


SUPPORTED_LANGUAGES = ("en", "id")
DEFAULT_LANGUAGE = "id"


@dataclass(frozen=True, slots=True)
class TopicSection:
    title: str       # The heading text, e.g. "Tips & Trick"
    anchor: str      # Slug used in setMarkdown anchors, e.g. "tips--trick"


@dataclass(frozen=True, slots=True)
class TopicMeta:
    slug: str        # File stem, e.g. "image-montage"
    title: str       # H1 from the file, e.g. "Image Montage"
    sections: tuple[TopicSection, ...]


def list_topics(language: str = DEFAULT_LANGUAGE) -> list[TopicMeta]:
    """Return every topic available for ``language``, sorted by slug.

    The welcome page (``_index``) is forced to the front.
    """
    folder = _docs_folder(language)
    metas: list[TopicMeta] = []
    for entry in sorted(folder.iterdir(), key=lambda p: p.name):
        if not entry.is_file() or not entry.name.endswith(".md"):
            continue
        slug = entry.name[:-3]
        text = entry.read_text(encoding="utf-8")
        metas.append(_parse_meta(slug, text))
    metas.sort(key=lambda m: (0 if m.slug == "_index" else 1, m.slug))
    return metas


def load_topic(slug: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Return the raw markdown body for ``slug`` in the requested language.

    Falls back to the default language when the requested file is missing.
    Raises ``FileNotFoundError`` only when neither language has the topic.
    """
    candidates = [language] if language in SUPPORTED_LANGUAGES else []
    if DEFAULT_LANGUAGE not in candidates:
        candidates.append(DEFAULT_LANGUAGE)
    for lang in candidates:
        folder = _docs_folder(lang)
        target = folder / f"{slug}.md"
        try:
            return target.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
    raise FileNotFoundError(f"Documentation topic '{slug}' missing in all languages")


def _docs_folder(language: str) -> Traversable:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{language}'; expected one of {SUPPORTED_LANGUAGES}"
        )
    return resources.files("app.docs").joinpath(language)


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def _parse_meta(slug: str, text: str) -> TopicMeta:
    title = slug
    sections: list[TopicSection] = []
    for match in _HEADING_RE.finditer(text):
        level = len(match.group(1))
        heading = match.group(2).strip()
        if level == 1 and title == slug:
            title = heading
            continue
        if level == 2:
            sections.append(TopicSection(title=heading, anchor=_slugify(heading)))
    return TopicMeta(slug=slug, title=title, sections=tuple(sections))


def _slugify(text: str) -> str:
    """Match Qt's QTextBrowser markdown anchor scheme: lowercase + dashed."""
    text = text.strip().lower()
    # Replace non-word groups with single dashes; keep alnum.
    text = re.sub(r"[^\w]+", "-", text)
    return text.strip("-")
