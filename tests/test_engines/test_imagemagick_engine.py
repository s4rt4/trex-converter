from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.imagemagick_engine import ImageMagickEngine


@pytest.mark.asyncio
async def test_imagemagick_engine_runs_subprocess(tmp_path, monkeypatch) -> None:
    fake_magick = tmp_path / "magick"
    fake_magick.write_text(
        "#!/bin/sh\n"
        "echo converted >&2\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_magick.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    task = Task(
        input_path=Path("input.png"),
        output_path=Path("output.webp"),
        format_in="png",
        format_out="webp",
        engine="imagemagick",
        options={"quality": 82, "strip": True, "resize": "1280x1280>"},
    )

    await ImageMagickEngine().convert(task)

    assert task.progress == 1.0
    assert any("Running: magick input.png -resize 1280x1280> -quality 82 -strip output.webp" in line for line in task.log)
    assert "converted" in task.log


def test_imagemagick_supports_registered_pairs() -> None:
    engine = ImageMagickEngine()

    assert engine.supports("png", "webp")
    assert engine.supports("png", "jpeg")
    assert engine.supports("png", "avif")
    assert engine.supports("webp", "tiff")
    assert not engine.supports("mp4", "png")
