"""Validate a page's curated output formats against the conversion registry.

Each converter page shows a *curated* list of output formats (kept short
and scannable on purpose) and is tagged with exactly one engine per kind
(see :data:`app.ui_gtk.backend.KIND_CONFIG`). The task queue runs that
engine — so an output format the engine can't actually produce would fail
at conversion time.

``list_supported_outputs`` is no help here: it merges every engine, so for
a ``.png`` input it also reports ``txt`` / ``hocr`` (OCR) and ``svg``
(trace) which the Image page's ImageMagick engine can't emit. Instead we
filter the curated list against the set of outputs the *page's own engine*
produces anywhere in the registry. This drops stale formats without
flooding the picker with obscure or wrong-engine ones.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from functools import lru_cache

from app.core.registry import ConversionRegistry
from app.ui_gtk.backend import KIND_CONFIG

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _registry() -> ConversionRegistry:
    return ConversionRegistry()


@lru_cache(maxsize=None)
def _engine_outputs(engine_name: str) -> frozenset[str]:
    """Every output format the named engine produces anywhere in the registry."""
    return frozenset(
        entry.format_out
        for entry in _registry().all_entries()
        if entry.engine_name == engine_name
    )


def supported_outputs(kind: str, formats: Sequence[str]) -> list[str]:
    """Filter ``formats`` to those the engine for ``kind`` can produce.

    Order is preserved. If the engine isn't represented in the registry, or
    the filter would empty the list (a misconfiguration we don't want to
    surface as an empty picker), the curated list is returned unchanged.
    """
    cfg = KIND_CONFIG.get(kind)
    if cfg is None:
        return list(formats)
    producible = _engine_outputs(cfg.engine)
    if not producible:
        return list(formats)

    kept = [fmt for fmt in formats if fmt.lower() in producible]
    dropped = [fmt for fmt in formats if fmt.lower() not in producible]
    if dropped:
        logger.warning(
            "Dropping unsupported output formats for %s (%s engine): %s",
            kind, cfg.engine, ", ".join(dropped),
        )
    return kept or list(formats)


def picker_args(
    kind: str,
    formats: Sequence[str],
    *,
    common: Sequence[str] | None = None,
    default: str | None = None,
) -> dict:
    """Registry-validated kwargs for a :class:`FormatPicker` (formats/common/default)."""
    valid = supported_outputs(kind, formats)
    args: dict = {"formats": valid}
    if common is not None:
        args["common"] = [fmt for fmt in common if fmt in valid]
    if default is not None:
        args["default"] = default if default in valid else valid[0]
    return args
