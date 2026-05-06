import json

from app.core.settings import Settings


def test_settings_default_values() -> None:
    settings = Settings()

    assert settings.output_dir == ""
    assert settings.max_concurrency == 2
    assert settings.default_image_quality == 82
    assert settings.default_pdf_dpi == 200


def test_settings_load_returns_defaults_when_missing(tmp_path) -> None:
    path = tmp_path / "absent.json"

    settings = Settings.load(path)

    assert settings == Settings()


def test_settings_load_returns_defaults_for_corrupt_json(tmp_path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("not json", encoding="utf-8")

    settings = Settings.load(path)

    assert settings == Settings()


def test_settings_save_then_load_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.json"
    original = Settings(
        output_dir="/tmp/out",
        max_concurrency=4,
        default_image_quality=90,
        default_pdf_dpi=300,
    )

    original.save(path)
    loaded = Settings.load(path)

    assert loaded == original
    payload = json.loads(path.read_text(encoding="utf-8"))
    # New default fields land in the JSON too; assert the user-set fields
    # round-trip exactly without pinning the full dict shape.
    assert payload["output_dir"] == "/tmp/out"
    assert payload["max_concurrency"] == 4
    assert payload["default_image_quality"] == 90
    assert payload["default_pdf_dpi"] == 300


def test_settings_load_ignores_unknown_keys(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"output_dir": "/x", "rogue": 99, "max_concurrency": 3}),
        encoding="utf-8",
    )

    settings = Settings.load(path)

    assert settings.output_dir == "/x"
    assert settings.max_concurrency == 3
    assert not hasattr(settings, "rogue")


def test_settings_load_returns_defaults_when_payload_not_dict(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    settings = Settings.load(path)

    assert settings == Settings()
