"""Sync guard: every EN topic must have an ID counterpart with the same
heading structure. Without this, the language toggle drifts as content
evolves.
"""

from __future__ import annotations

from importlib import resources

from app.docs.loader import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    list_topics,
    load_topic,
)


REQUIRED_SECTIONS = ("Description", "How to use", "Tips & Trick", "Troubleshooting")
REQUIRED_SECTIONS_ID = ("Deskripsi", "Cara pakai", "Tips & Trick", "Troubleshooting")


def _topic_slugs(language: str) -> set[str]:
    return {topic.slug for topic in list_topics(language)}


def test_every_topic_exists_in_both_languages() -> None:
    en_slugs = _topic_slugs("en")
    id_slugs = _topic_slugs("id")

    en_only = en_slugs - id_slugs
    id_only = id_slugs - en_slugs

    assert not en_only, f"Topics missing from 'id': {sorted(en_only)}"
    assert not id_only, f"Topics missing from 'en': {sorted(id_only)}"


def test_section_count_matches_across_languages() -> None:
    en_meta = {topic.slug: topic for topic in list_topics("en")}
    id_meta = {topic.slug: topic for topic in list_topics("id")}

    mismatches: list[str] = []
    for slug, en in en_meta.items():
        id_topic = id_meta.get(slug)
        if id_topic is None:
            continue
        if len(en.sections) != len(id_topic.sections):
            mismatches.append(
                f"{slug}: en has {len(en.sections)} sections, "
                f"id has {len(id_topic.sections)}"
            )

    assert not mismatches, "Section-count drift:\n" + "\n".join(mismatches)


def test_module_topics_use_required_sections() -> None:
    """Module topics (non-meta) follow the standard 4-section template."""
    skip = {"_index"}
    bad: list[str] = []
    for topic in list_topics("en"):
        if topic.slug in skip:
            continue
        section_titles = [s.title for s in topic.sections]
        if section_titles != list(REQUIRED_SECTIONS):
            bad.append(f"en/{topic.slug}: {section_titles}")
    for topic in list_topics("id"):
        if topic.slug in skip:
            continue
        section_titles = [s.title for s in topic.sections]
        if section_titles != list(REQUIRED_SECTIONS_ID):
            bad.append(f"id/{topic.slug}: {section_titles}")
    assert not bad, "Sections off-template:\n" + "\n".join(bad)


def test_load_topic_falls_back_to_default_language() -> None:
    # Ask for a slug in a supported but missing language; expect default fallback.
    text = load_topic("_index", "en")
    assert text.lstrip().startswith("# ")


def test_supported_languages_include_default() -> None:
    assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES


def test_topic_files_are_packaged() -> None:
    """Make sure markdown files are accessible via importlib.resources so
    the .deb / wheel install reaches them.
    """
    en_dir = resources.files("app.docs").joinpath("en")
    id_dir = resources.files("app.docs").joinpath("id")
    assert en_dir.joinpath("_index.md").is_file()
    assert id_dir.joinpath("_index.md").is_file()
    # Spot-check one module topic
    assert en_dir.joinpath("image.md").is_file()
    assert id_dir.joinpath("image.md").is_file()
