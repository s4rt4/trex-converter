from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


SUBTITLE_FORMATS = ("srt", "vtt", "ass")
SUPPORTED_PAIRS = {
    (fmt_in, fmt_out)
    for fmt_in in SUBTITLE_FORMATS
    for fmt_out in SUBTITLE_FORMATS
}

_TIMESTAMP_RE = re.compile(
    r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)"
)
_BLOCK_SPLIT_RE = re.compile(r"\r?\n\r?\n+")
_ASS_TIMESTAMP_RE = re.compile(r"^(\d+):(\d+):(\d+)\.(\d+)$")


_ASS_DEFAULT_STYLE = (
    "Style: Default,Arial,32,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,"
    "0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1"
)
_ASS_FORMAT_HEADER = (
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
    "Effect, Text"
)
_ASS_STYLE_FORMAT = (
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
    "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
    "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
    "Alignment, MarginL, MarginR, MarginV, Encoding"
)
_ASS_HEADER = (
    "[Script Info]\n"
    "ScriptType: v4.00+\n"
    "PlayResX: 1280\n"
    "PlayResY: 720\n"
    "\n"
    "[V4+ Styles]\n"
    f"{_ASS_STYLE_FORMAT}\n"
    f"{_ASS_DEFAULT_STYLE}\n"
    "\n"
    "[Events]\n"
    f"{_ASS_FORMAT_HEADER}\n"
)


@dataclass(slots=True)
class Cue:
    start_seconds: float
    end_seconds: float
    text: str


class SubtitleEngine(BaseEngine):
    name = "subtitle"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=False,
            supports_cancel=False,
            requires_binary="",
        )

    async def convert(self, task: Task) -> None:
        input_text = Path(task.input_path).read_text(encoding="utf-8-sig")

        format_in = task.format_in.lower()
        format_out = task.format_out.lower()

        parsers = {"srt": parse_srt, "vtt": parse_vtt, "ass": parse_ass}
        formatters = {"srt": format_srt, "vtt": format_vtt, "ass": format_ass}

        if format_in not in parsers:
            raise RuntimeError(f"Unsupported subtitle input: {task.format_in}")
        if format_out not in formatters:
            raise RuntimeError(f"Unsupported subtitle output: {task.format_out}")

        cues = parsers[format_in](input_text)
        if not cues:
            raise RuntimeError("No subtitle cues found in input file")

        offset = _float_option(task.options.get("time_shift_seconds"))
        if offset:
            cues = [
                Cue(
                    start_seconds=max(0.0, cue.start_seconds + offset),
                    end_seconds=max(0.0, cue.end_seconds + offset),
                    text=cue.text,
                )
                for cue in cues
            ]
            task.append_log(f"Applied time shift: {offset:+g}s")

        output = formatters[format_out](cues)
        output_path = Path(task.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        task.append_log(f"Wrote {len(cues)} cue(s) to {output_path}")
        task.progress = 1.0

    async def cancel(self, task: Task) -> None:
        task.mark_cancelled()

    def supports(self, format_in: str, format_out: str) -> bool:
        return (format_in.lower(), format_out.lower()) in SUPPORTED_PAIRS

    @property
    def capabilities(self) -> EngineCapabilities:
        return self._capabilities


def parse_srt(text: str) -> list[Cue]:
    return _parse_cues(text, skip_prefixes=())


def parse_vtt(text: str) -> list[Cue]:
    return _parse_cues(text, skip_prefixes=("WEBVTT", "NOTE", "STYLE", "REGION"))


def _parse_cues(text: str, *, skip_prefixes: tuple[str, ...]) -> list[Cue]:
    cues: list[Cue] = []
    for block in _BLOCK_SPLIT_RE.split(text.strip()):
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if any(lines[0].startswith(prefix) for prefix in skip_prefixes):
            continue

        ts_match = _TIMESTAMP_RE.search(lines[0])
        if ts_match:
            text_lines = lines[1:]
        elif len(lines) >= 2 and (ts_match := _TIMESTAMP_RE.search(lines[1])):
            text_lines = lines[2:]
        else:
            continue

        h1, m1, s1, ms1, h2, m2, s2, ms2 = ts_match.groups()
        cues.append(
            Cue(
                start_seconds=_to_seconds(h1, m1, s1, ms1),
                end_seconds=_to_seconds(h2, m2, s2, ms2),
                text="\n".join(text_lines),
            )
        )
    return cues


def parse_ass(text: str) -> list[Cue]:
    cues: list[Cue] = []
    section: str | None = None
    text_field_index = 9  # default if no Format header is seen

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        if section != "events":
            continue

        if line.startswith("Format:"):
            fields = [
                field.strip().lower()
                for field in line[len("Format:"):].split(",")
            ]
            try:
                text_field_index = fields.index("text")
            except ValueError:
                text_field_index = 9
            continue

        if not line.startswith(("Dialogue:", "Comment:")):
            continue
        if line.startswith("Comment:"):
            continue

        body = line[len("Dialogue:"):].lstrip()
        parts = body.split(",", text_field_index)
        if len(parts) <= text_field_index:
            continue

        start = _parse_ass_time(parts[1].strip())
        end = _parse_ass_time(parts[2].strip())
        if start is None or end is None:
            continue

        cue_text = parts[-1].replace("\\N", "\n").replace("\\n", "\n")
        cues.append(Cue(start_seconds=start, end_seconds=end, text=cue_text))

    return cues


def format_srt(cues: list[Cue]) -> str:
    parts: list[str] = []
    for index, cue in enumerate(cues, 1):
        parts.append(str(index))
        parts.append(
            f"{_format_time(cue.start_seconds, ',')} --> "
            f"{_format_time(cue.end_seconds, ',')}"
        )
        parts.append(cue.text)
        parts.append("")
    return "\n".join(parts).rstrip("\n") + "\n"


def format_vtt(cues: list[Cue]) -> str:
    parts: list[str] = ["WEBVTT", ""]
    for cue in cues:
        parts.append(
            f"{_format_time(cue.start_seconds, '.')} --> "
            f"{_format_time(cue.end_seconds, '.')}"
        )
        parts.append(cue.text)
        parts.append("")
    return "\n".join(parts).rstrip("\n") + "\n"


def format_ass(cues: list[Cue]) -> str:
    parts: list[str] = [_ASS_HEADER]
    for cue in cues:
        text = cue.text.replace("\n", "\\N")
        parts.append(
            f"Dialogue: 0,"
            f"{_format_ass_time(cue.start_seconds)},"
            f"{_format_ass_time(cue.end_seconds)},"
            f"Default,,0,0,0,,{text}\n"
        )
    return "".join(parts)


def _to_seconds(hours: str, minutes: str, seconds: str, milliseconds: str) -> float:
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(milliseconds) / 1000.0
    )


def _parse_ass_time(text: str) -> float | None:
    match = _ASS_TIMESTAMP_RE.match(text)
    if not match:
        return None
    hours, minutes, seconds, centiseconds = match.groups()
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(centiseconds) / 100.0
    )


def _format_time(value: float, separator: str) -> str:
    total_ms = max(0, int(round(value * 1000)))
    hours, total_ms = divmod(total_ms, 3_600_000)
    minutes, total_ms = divmod(total_ms, 60_000)
    seconds, milliseconds = divmod(total_ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{milliseconds:03d}"


def _format_ass_time(value: float) -> str:
    total_cs = max(0, int(round(value * 100)))
    hours, total_cs = divmod(total_cs, 360_000)
    minutes, total_cs = divmod(total_cs, 6_000)
    seconds, centiseconds = divmod(total_cs, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def _float_option(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
