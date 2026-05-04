from __future__ import annotations

import asyncio
import re
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


VIDEO_FORMATS = ("mp4", "mov", "webm", "mkv")
AUDIO_OUT_FROM_VIDEO = ("mp3", "wav", "aac")

SUPPORTED_PAIRS = (
    {(fmt_in, fmt_out) for fmt_in in VIDEO_FORMATS for fmt_out in VIDEO_FORMATS}
    | {(fmt_in, fmt_out) for fmt_in in VIDEO_FORMATS for fmt_out in AUDIO_OUT_FROM_VIDEO}
    | {("wav", "mp3"), ("flac", "mp3"), ("mp3", "wav")}
)

RESOLUTION_PRESETS = {
    "4k": "3840:-2",
    "1440p": "2560:-2",
    "1080p": "1920:-2",
    "720p": "1280:-2",
    "480p": "854:-2",
    "360p": "640:-2",
}
COMPRESS_PRESETS = {
    "ultrafast",
    "superfast",
    "veryfast",
    "faster",
    "fast",
    "medium",
    "slow",
    "slower",
    "veryslow",
}
GRAVITY_DRAWTEXT_POS = {
    "northwest": ("20", "20"),
    "north": ("(w-text_w)/2", "20"),
    "northeast": ("w-text_w-20", "20"),
    "west": ("20", "(h-text_h)/2"),
    "center": ("(w-text_w)/2", "(h-text_h)/2"),
    "east": ("w-text_w-20", "(h-text_h)/2"),
    "southwest": ("20", "h-text_h-20"),
    "south": ("(w-text_w)/2", "h-text_h-20"),
    "southeast": ("w-text_w-20", "h-text_h-20"),
}
AUDIO_OUTPUT_FORMATS = {"mp3", "wav", "aac", "flac", "m4a", "opus", "ogg"}

_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_CROP_FREE_RE = re.compile(r"^(\d+)x(\d+)\+(\d+)\+(\d+)$")


class FFmpegEngine(BaseEngine):
    name = "ffmpeg"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=True,
            supports_cancel=True,
            requires_binary="ffmpeg",
        )
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def convert(self, task: Task) -> None:
        command = self._build_command(task)
        task.append_log("Running: " + " ".join(command))
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes[task.id] = process
        duration_seconds: float | None = None

        try:
            assert process.stderr is not None
            while True:
                raw_line = await process.stderr.readline()
                if not raw_line:
                    break
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                duration_seconds = duration_seconds or _parse_duration(line)
                progress = _parse_progress(line, duration_seconds)
                if progress is not None:
                    task.progress = progress
                elif _should_log(line):
                    task.append_log(line)

            return_code = await process.wait()
            if return_code != 0:
                raise RuntimeError(f"ffmpeg exited with code {return_code}")
            task.progress = 1.0
        except asyncio.CancelledError:
            await self.cancel(task)
            raise
        finally:
            self._processes.pop(task.id, None)

    async def cancel(self, task: Task) -> None:
        process = self._processes.get(task.id)
        if process and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=3)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        task.mark_cancelled()

    def supports(self, format_in: str, format_out: str) -> bool:
        return (format_in.lower(), format_out.lower()) in SUPPORTED_PAIRS

    @property
    def capabilities(self) -> EngineCapabilities:
        return self._capabilities

    def _build_command(self, task: Task) -> list[str]:
        output_path = Path(task.output_path)
        command = ["ffmpeg", "-y", "-i", str(task.input_path)]

        command.extend(_trim_options(task.options))

        is_audio_only = task.format_out in AUDIO_OUTPUT_FORMATS
        video_filters = "" if is_audio_only else _video_filter_chain(task.options)
        if video_filters:
            command.extend(["-vf", video_filters])

        audio_filters = _audio_filter_chain(task.options, drop_audio=False)
        if audio_filters:
            command.extend(["-af", audio_filters])

        command.extend(_codec_options(task))
        command.extend(["-progress", "pipe:2", "-nostats", str(output_path)])
        return command


def _trim_options(options: dict) -> list[str]:
    args: list[str] = []
    start = options.get("trim_start")
    if start:
        args.extend(["-ss", str(start)])
    end = options.get("trim_end")
    if end:
        args.extend(["-to", str(end)])
    return args


def _video_filter_chain(options: dict) -> str:
    filters: list[str] = []

    crop = options.get("crop")
    if crop:
        filters.append(f"crop={_parse_crop(crop)}")

    rotation = _int_option(options.get("rotation_degrees"))
    if rotation:
        filters.extend(_rotation_filters(rotation))

    if options.get("flip_horizontal"):
        filters.append("hflip")
    if options.get("flip_vertical"):
        filters.append("vflip")

    resolution = options.get("resolution_preset")
    if resolution:
        scale = RESOLUTION_PRESETS.get(str(resolution).lower())
        if not scale:
            raise RuntimeError(f"Unknown resolution preset: {resolution}")
        filters.append(f"scale={scale}")

    speed = _float_option(options.get("speed"))
    if speed and speed > 0 and abs(speed - 1.0) > 1e-3:
        filters.append(f"setpts={1 / speed:.6f}*PTS")

    watermark_text = options.get("watermark_text")
    if watermark_text:
        filters.append(_drawtext_filter(options))

    return ",".join(filters)


def _audio_filter_chain(options: dict, *, drop_audio: bool) -> str:
    if drop_audio:
        return ""
    filters: list[str] = []
    speed = _float_option(options.get("speed"))
    if speed and speed > 0 and abs(speed - 1.0) > 1e-3:
        filters.extend(_atempo_chain(speed))
    return ",".join(filters)


def _atempo_chain(speed: float) -> list[str]:
    if not 0.5 <= speed <= 2.0:
        raise RuntimeError("speed must be between 0.5 and 2.0 for audio sync")
    return [f"atempo={speed:.6f}"]


def _rotation_filters(degrees: int) -> list[str]:
    normalized = ((degrees % 360) + 360) % 360
    if normalized == 0:
        return []
    if normalized == 90:
        return ["transpose=1"]
    if normalized == 180:
        return ["transpose=2,transpose=2"]
    if normalized == 270:
        return ["transpose=2"]
    raise RuntimeError(f"Rotation must be a multiple of 90 degrees, got {degrees}")


def _parse_crop(value: str) -> str:
    text = str(value).strip()
    if ":" in text and "+" not in text:
        return text
    match = _CROP_FREE_RE.match(text)
    if not match:
        raise RuntimeError(f"Invalid crop spec (expected WxH+X+Y): {value}")
    width, height, x, y = match.groups()
    return f"{width}:{height}:{x}:{y}"


def _drawtext_filter(options: dict) -> str:
    text = str(options.get("watermark_text"))
    gravity = str(options.get("watermark_position") or "southeast").lower()
    if gravity not in GRAVITY_DRAWTEXT_POS:
        raise RuntimeError(f"Unknown watermark position: {gravity}")
    fontsize = _int_option(options.get("watermark_size")) or 36
    opacity = _int_option(options.get("watermark_opacity"))
    if opacity is None:
        opacity = 60
    alpha = max(0.0, min(1.0, opacity / 100.0))
    x_expr, y_expr = GRAVITY_DRAWTEXT_POS[gravity]

    parts = [
        f"drawtext=text='{_escape_drawtext(text)}'",
        "font=Sans",
        f"fontsize={fontsize}",
        f"fontcolor=white@{alpha:.2f}",
        "borderw=2",
        "bordercolor=black@0.6",
        f"x={x_expr}",
        f"y={y_expr}",
    ]
    return ":".join(parts)


def _escape_drawtext(text: str) -> str:
    return text.replace("\\", "\\\\").replace("'", "\\'")


def _codec_options(task: Task) -> list[str]:
    options: list[str] = []
    if task.format_out in AUDIO_OUTPUT_FORMATS:
        options.append("-vn")

    bitrate = task.options.get("bitrate")
    if bitrate:
        options.extend(["-b:a", str(bitrate)])

    sample_rate = task.options.get("sample_rate")
    if sample_rate:
        options.extend(["-ar", str(sample_rate)])

    video_codec = task.options.get("video_codec")
    if video_codec:
        options.extend(["-c:v", str(video_codec)])

    audio_codec = task.options.get("audio_codec")
    if audio_codec:
        options.extend(["-c:a", str(audio_codec)])

    crf = _int_option(task.options.get("crf"))
    if crf is not None and task.format_out not in AUDIO_OUTPUT_FORMATS:
        if not video_codec:
            options.extend(["-c:v", "libx264"])
        options.extend(["-crf", str(crf)])

    preset = task.options.get("compress_preset")
    if preset:
        if str(preset).lower() not in COMPRESS_PRESETS:
            raise RuntimeError(f"Unknown compress preset: {preset}")
        options.extend(["-preset", str(preset).lower()])

    return options


def _parse_duration(line: str) -> float | None:
    match = _DURATION_RE.search(line)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _parse_progress(line: str, duration_seconds: float | None) -> float | None:
    if line == "progress=end":
        return 1.0
    if not duration_seconds:
        return None

    if line.startswith("out_time_ms="):
        value = line.split("=", 1)[1]
        try:
            elapsed_seconds = int(value) / 1_000_000
        except ValueError:
            return None
        return max(0.0, min(0.99, elapsed_seconds / duration_seconds))

    if line.startswith("out_time="):
        value = line.split("=", 1)[1]
        try:
            hours, minutes, seconds = value.split(":")
            elapsed_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        except ValueError:
            return None
        return max(0.0, min(0.99, elapsed_seconds / duration_seconds))

    return None


def _should_log(line: str) -> bool:
    return not (
        line.startswith("frame=")
        or line.startswith("fps=")
        or line.startswith("stream_")
        or line.startswith("total_size=")
        or line.startswith("out_time")
        or line.startswith("dup_frames=")
        or line.startswith("drop_frames=")
        or line.startswith("speed=")
        or line.startswith("progress=")
        or line.startswith("bitrate=")
    )


def _int_option(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _float_option(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
