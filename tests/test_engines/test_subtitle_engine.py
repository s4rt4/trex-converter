from pathlib import Path

import pytest

from app.core.task import Task
from app.engines.subtitle_engine import (
    SubtitleEngine,
    format_ass,
    format_srt,
    format_vtt,
    parse_ass,
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
    # Wave 2: ASS now part of the matrix
    assert engine.supports("ass", "srt")
    assert engine.supports("srt", "ass")
    assert engine.supports("vtt", "ass")
    assert engine.supports("ass", "vtt")
    assert engine.supports("ass", "ass")
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


# ---- Wave 2: ASS support ----


SAMPLE_ASS = """\
[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour
Style: Default,Arial,32,&H00FFFFFF

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,Hello, world!
Dialogue: 0,0:00:05.50,0:00:08.25,Default,,0,0,0,,Second cue\\Non two lines
Comment: 0,0:00:10.00,0:00:11.00,Default,,0,0,0,,A comment that should be skipped
"""


def test_parse_ass_extracts_dialogue_lines_and_skips_comments() -> None:
    cues = parse_ass(SAMPLE_ASS)

    assert len(cues) == 2
    assert cues[0].start_seconds == pytest.approx(1.0)
    assert cues[0].end_seconds == pytest.approx(4.0)
    assert cues[0].text == "Hello, world!"
    assert cues[1].start_seconds == pytest.approx(5.5)
    assert cues[1].end_seconds == pytest.approx(8.25)
    # \N is converted to a real newline
    assert cues[1].text == "Second cue\non two lines"


def test_parse_ass_handles_comma_in_text_field() -> None:
    text = (
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,Hello, world, again\n"
    )

    cues = parse_ass(text)

    assert len(cues) == 1
    # Commas inside the Text field are preserved (split bounded by Format index)
    assert cues[0].text == "Hello, world, again"


def test_format_ass_emits_script_info_styles_and_events() -> None:
    cues = parse_srt(
        "1\n00:00:01,000 --> 00:00:04,000\nLine A\n\n"
        "2\n00:00:05,500 --> 00:00:08,250\nLine B\n"
    )

    output = format_ass(cues)

    assert "[Script Info]" in output
    assert "ScriptType: v4.00+" in output
    assert "[V4+ Styles]" in output
    assert "Style: Default,Arial," in output
    assert "[Events]" in output
    assert "Format: Layer, Start, End, Style," in output
    assert "Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,Line A" in output
    assert "Dialogue: 0,0:00:05.50,0:00:08.25,Default,,0,0,0,,Line B" in output


def test_format_ass_encodes_newlines_as_backslash_N() -> None:
    cues = parse_srt(
        "1\n00:00:01,000 --> 00:00:02,000\nFirst line\nSecond line\n"
    )

    output = format_ass(cues)

    assert "First line\\NSecond line" in output


def test_ass_round_trip_preserves_cues() -> None:
    original = parse_ass(SAMPLE_ASS)
    formatted = format_ass(original)
    reparsed = parse_ass(formatted)

    assert len(reparsed) == len(original)
    for before, after in zip(original, reparsed):
        assert before.start_seconds == pytest.approx(after.start_seconds)
        assert before.end_seconds == pytest.approx(after.end_seconds)
        assert before.text == after.text


def test_format_ass_time_pads_centiseconds_to_two_digits() -> None:
    cues = parse_ass(
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "Dialogue: 0,0:00:00.05,0:00:00.10,Default,,0,0,0,,X\n"
    )

    output = format_ass(cues)

    assert "0:00:00.05,0:00:00.10" in output


@pytest.mark.asyncio
async def test_engine_converts_srt_to_ass(tmp_path) -> None:
    input_path = tmp_path / "in.srt"
    input_path.write_text(SAMPLE_SRT, encoding="utf-8")
    output_path = tmp_path / "out.ass"

    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="srt",
        format_out="ass",
        engine="subtitle",
    )

    await SubtitleEngine().convert(task)

    output = output_path.read_text(encoding="utf-8")
    assert "[Events]" in output
    assert "Dialogue: 0,0:00:01.00,0:00:04.00,Default" in output
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_engine_converts_ass_to_srt_with_time_shift(tmp_path) -> None:
    input_path = tmp_path / "in.ass"
    input_path.write_text(SAMPLE_ASS, encoding="utf-8")
    output_path = tmp_path / "out.srt"

    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="ass",
        format_out="srt",
        engine="subtitle",
        options={"time_shift_seconds": 1.5},
    )

    await SubtitleEngine().convert(task)

    output = output_path.read_text(encoding="utf-8")
    assert "00:00:02,500 --> 00:00:05,500" in output
    assert "00:00:07,000 --> 00:00:09,750" in output


# ---- Multi-input wave: merge ----


SAMPLE_SRT_FIRST = """\
1
00:00:01,000 --> 00:00:03,000
First A

2
00:00:04,000 --> 00:00:06,000
First B
"""

SAMPLE_SRT_SECOND = """\
1
00:00:00,500 --> 00:00:02,500
Second A

2
00:00:03,000 --> 00:00:05,000
Second B
"""


@pytest.mark.asyncio
async def test_engine_merge_shift_mode_chains_files_sequentially(tmp_path) -> None:
    a = tmp_path / "a.srt"
    b = tmp_path / "b.srt"
    a.write_text(SAMPLE_SRT_FIRST, encoding="utf-8")
    b.write_text(SAMPLE_SRT_SECOND, encoding="utf-8")
    out = tmp_path / "merged.srt"

    task = Task(
        input_path=a,
        output_path=out,
        format_in="srt",
        format_out="srt",
        engine="subtitle",
        options={"operation": "merge"},
        extra_inputs=[b],
    )

    await SubtitleEngine().convert(task)

    output = out.read_text(encoding="utf-8")
    # First file unchanged
    assert "00:00:01,000 --> 00:00:03,000" in output
    assert "00:00:04,000 --> 00:00:06,000" in output
    # Second file shifted by first file's max end (6.0s) + gap (0)
    assert "00:00:06,500 --> 00:00:08,500" in output
    assert "00:00:09,000 --> 00:00:11,000" in output


@pytest.mark.asyncio
async def test_engine_merge_shift_mode_respects_gap(tmp_path) -> None:
    a = tmp_path / "a.srt"
    b = tmp_path / "b.srt"
    a.write_text(SAMPLE_SRT_FIRST, encoding="utf-8")
    b.write_text(SAMPLE_SRT_SECOND, encoding="utf-8")

    task = Task(
        input_path=a,
        output_path=tmp_path / "out.srt",
        format_in="srt",
        format_out="srt",
        engine="subtitle",
        options={"operation": "merge", "subtitle_merge_gap": 1.5},
        extra_inputs=[b],
    )

    await SubtitleEngine().convert(task)

    output = (tmp_path / "out.srt").read_text(encoding="utf-8")
    # Second file shifted by 6.0 + 1.5 = 7.5s
    assert "00:00:08,000 --> 00:00:10,000" in output


@pytest.mark.asyncio
async def test_engine_merge_append_mode_sorts_by_start_time(tmp_path) -> None:
    a = tmp_path / "a.srt"
    b = tmp_path / "b.srt"
    a.write_text(SAMPLE_SRT_FIRST, encoding="utf-8")
    b.write_text(SAMPLE_SRT_SECOND, encoding="utf-8")
    out = tmp_path / "merged.srt"

    task = Task(
        input_path=a,
        output_path=out,
        format_in="srt",
        format_out="srt",
        engine="subtitle",
        options={"operation": "merge", "subtitle_merge_mode": "append"},
        extra_inputs=[b],
    )

    await SubtitleEngine().convert(task)

    text = out.read_text(encoding="utf-8")
    # All four cues are present, sorted by start time:
    # 0.5s (Second A), 1.0s (First A), 3.0s (Second B), 4.0s (First B)
    pos_first_a = text.index("First A")
    pos_first_b = text.index("First B")
    pos_second_a = text.index("Second A")
    pos_second_b = text.index("Second B")
    assert pos_second_a < pos_first_a < pos_second_b < pos_first_b


@pytest.mark.asyncio
async def test_engine_merge_handles_mixed_input_formats(tmp_path) -> None:
    a = tmp_path / "a.srt"
    b = tmp_path / "b.vtt"
    a.write_text(SAMPLE_SRT, encoding="utf-8")
    b.write_text(SAMPLE_VTT, encoding="utf-8")
    out = tmp_path / "merged.ass"

    task = Task(
        input_path=a,
        output_path=out,
        format_in="srt",
        format_out="ass",
        engine="subtitle",
        options={"operation": "merge"},
        extra_inputs=[b],
    )

    await SubtitleEngine().convert(task)

    output = out.read_text(encoding="utf-8")
    assert "[Events]" in output
    # First file's cues (1-4s and 5.5-8.25s), then second file's cues shifted by 8.25s
    # Second file's 1.0s cue becomes 9.25s -> "0:00:09.25"
    assert "0:00:09.25" in output


@pytest.mark.asyncio
async def test_engine_merge_requires_at_least_two_inputs(tmp_path) -> None:
    a = tmp_path / "a.srt"
    a.write_text(SAMPLE_SRT, encoding="utf-8")

    task = Task(
        input_path=a,
        output_path=tmp_path / "out.srt",
        format_in="srt",
        format_out="srt",
        engine="subtitle",
        options={"operation": "merge"},
    )

    with pytest.raises(RuntimeError, match="at least two"):
        await SubtitleEngine().convert(task)


@pytest.mark.asyncio
async def test_engine_merge_rejects_unknown_mode(tmp_path) -> None:
    a = tmp_path / "a.srt"
    b = tmp_path / "b.srt"
    a.write_text(SAMPLE_SRT_FIRST, encoding="utf-8")
    b.write_text(SAMPLE_SRT_SECOND, encoding="utf-8")

    task = Task(
        input_path=a,
        output_path=tmp_path / "out.srt",
        format_in="srt",
        format_out="srt",
        engine="subtitle",
        options={"operation": "merge", "subtitle_merge_mode": "weird"},
        extra_inputs=[b],
    )

    with pytest.raises(RuntimeError, match="subtitle_merge_mode"):
        await SubtitleEngine().convert(task)
