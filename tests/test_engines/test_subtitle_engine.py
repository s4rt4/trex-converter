from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.subtitle_engine import (
    SubtitleEngine,
    format_srt,
    format_vtt,
    parse_srt,
    parse_vtt,
)


SAMPLE_SRT = """\
1
00:00:01,000 --> 00:00:04,000
Hello, world!

2
00:00:05,500 --> 00:00:08,250
Second cue
on two lines
"""

SAMPLE_VTT = """\
WEBVTT

00:00:01.000 --> 00:00:04.000
Hello, world!

00:00:05.500 --> 00:00:08.250
Second cue
on two lines
"""


def test_supports_subtitle_pairs() -> None:
    engine = SubtitleEngine()

    assert engine.supports("srt", "vtt")
    assert engine.supports("vtt", "srt")
    assert engine.supports("srt", "srt")
    assert engine.supports("vtt", "vtt")
    assert not engine.supports("ass", "srt")
    assert not engine.supports("srt", "txt")


def test_parse_srt_extracts_cues_with_timestamps() -> None:
    cues = parse_srt(SAMPLE_SRT)

    assert len(cues) == 2
    assert cues[0].start_seconds == pytest.approx(1.0)
    assert cues[0].end_seconds == pytest.approx(4.0)
    assert cues[0].text == "Hello, world!"
    assert cues[1].start_seconds == pytest.approx(5.5)
    assert cues[1].end_seconds == pytest.approx(8.25)
    assert cues[1].text == "Second cue\non two lines"


def test_parse_vtt_skips_header_and_extracts_cues() -> None:
    cues = parse_vtt(SAMPLE_VTT)

    assert len(cues) == 2
    assert cues[0].text == "Hello, world!"
    assert cues[1].text == "Second cue\non two lines"


def test_parse_vtt_skips_note_blocks() -> None:
    text = (
        "WEBVTT\n\n"
        "NOTE This is a comment\n\n"
        "00:00:01.000 --> 00:00:02.000\n"
        "Real cue\n"
    )

    cues = parse_vtt(text)

    assert len(cues) == 1
    assert cues[0].text == "Real cue"


def test_format_srt_uses_comma_separator_and_numbers_cues() -> None:
    cues = parse_vtt(SAMPLE_VTT)

    output = format_srt(cues)

    assert "1\n00:00:01,000 --> 00:00:04,000\nHello, world!" in output
    assert "2\n00:00:05,500 --> 00:00:08,250" in output


def test_format_vtt_uses_dot_separator_and_webvtt_header() -> None:
    cues = parse_srt(SAMPLE_SRT)

    output = format_vtt(cues)

    assert output.startswith("WEBVTT\n\n")
    assert "00:00:01.000 --> 00:00:04.000" in output
    assert "00:00:05.500 --> 00:00:08.250" in output


@pytest.mark.asyncio
async def test_engine_converts_srt_to_vtt(tmp_path) -> None:
    input_path = tmp_path / "in.srt"
    input_path.write_text(SAMPLE_SRT, encoding="utf-8")
    output_path = tmp_path / "out.vtt"

    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="srt",
        format_out="vtt",
        engine="subtitle",
    )

    await SubtitleEngine().convert(task)

    output = output_path.read_text(encoding="utf-8")
    assert output.startswith("WEBVTT\n")
    assert "00:00:01.000 --> 00:00:04.000" in output
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_engine_applies_time_shift(tmp_path) -> None:
    input_path = tmp_path / "in.srt"
    input_path.write_text(SAMPLE_SRT, encoding="utf-8")
    output_path = tmp_path / "out.srt"

    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="srt",
        format_out="srt",
        engine="subtitle",
        options={"time_shift_seconds": 2.5},
    )

    await SubtitleEngine().convert(task)

    output = output_path.read_text(encoding="utf-8")
    assert "00:00:03,500 --> 00:00:06,500" in output
    assert "00:00:08,000 --> 00:00:10,750" in output


@pytest.mark.asyncio
async def test_engine_negative_shift_clamps_to_zero(tmp_path) -> None:
    input_path = tmp_path / "in.srt"
    input_path.write_text(SAMPLE_SRT, encoding="utf-8")
    output_path = tmp_path / "out.srt"

    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="srt",
        format_out="srt",
        engine="subtitle",
        options={"time_shift_seconds": -10},
    )

    await SubtitleEngine().convert(task)

    output = output_path.read_text(encoding="utf-8")
    # Both cues start before the shift; clamped to 00:00:00,000
    assert "00:00:00,000 --> 00:00:00,000" in output


@pytest.mark.asyncio
async def test_engine_raises_when_no_cues(tmp_path) -> None:
    input_path = tmp_path / "empty.srt"
    input_path.write_text("not a valid subtitle file", encoding="utf-8")
    output_path = tmp_path / "out.srt"

    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="srt",
        format_out="srt",
        engine="subtitle",
    )

    with pytest.raises(RuntimeError, match="No subtitle cues"):
        await SubtitleEngine().convert(task)


def test_format_time_pads_to_three_milliseconds_digits() -> None:
    cues = parse_srt("1\n00:00:00,005 --> 00:00:00,010\nTest\n")

    output = format_srt(cues)

    assert "00:00:00,005 --> 00:00:00,010" in output
