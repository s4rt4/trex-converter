from pathlib import Path

import pytest

from app.core.presets import (
    delete_preset,
    list_presets,
    load_preset,
    save_preset,
)


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    target = save_preset("image", "high quality", {"quality": 95}, base=tmp_path)
    assert target.exists()
    assert target.parent.name == "image"
    assert target.stem == "high quality"

    loaded = load_preset("image", "high quality", base=tmp_path)
    assert loaded == {"quality": 95}


def test_list_presets_sorted(tmp_path: Path) -> None:
    save_preset("image", "z", {"a": 1}, base=tmp_path)
    save_preset("image", "a", {"b": 2}, base=tmp_path)
    save_preset("image", "m", {"c": 3}, base=tmp_path)

    assert list_presets("image", base=tmp_path) == ["a", "m", "z"]


def test_list_presets_returns_empty_for_unknown_kind(tmp_path: Path) -> None:
    assert list_presets("nonexistent-kind", base=tmp_path) == []


def test_load_missing_returns_empty(tmp_path: Path) -> None:
    assert load_preset("image", "ghost", base=tmp_path) == {}


def test_load_corrupt_json_returns_empty(tmp_path: Path) -> None:
    folder = tmp_path / "image"
    folder.mkdir()
    (folder / "broken.json").write_text("not-json", encoding="utf-8")

    assert load_preset("image", "broken", base=tmp_path) == {}


def test_load_non_dict_returns_empty(tmp_path: Path) -> None:
    folder = tmp_path / "image"
    folder.mkdir()
    (folder / "list.json").write_text("[1, 2, 3]", encoding="utf-8")

    assert load_preset("image", "list", base=tmp_path) == {}


def test_delete_preset(tmp_path: Path) -> None:
    save_preset("video", "trim-cut", {"trim_start": "00:00:05"}, base=tmp_path)
    assert delete_preset("video", "trim-cut", base=tmp_path) is True
    assert delete_preset("video", "trim-cut", base=tmp_path) is False
    assert load_preset("video", "trim-cut", base=tmp_path) == {}


def test_save_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Preset name"):
        save_preset("image", "../escape", {}, base=tmp_path)
    with pytest.raises(ValueError):
        save_preset("image", "", {}, base=tmp_path)
    with pytest.raises(ValueError):
        save_preset("image", "x" * 50, {}, base=tmp_path)


def test_save_accepts_spaces_underscores_hyphens(tmp_path: Path) -> None:
    target = save_preset(
        "image", "My Preset_1-final", {"strip": True}, base=tmp_path
    )
    assert target.exists()
