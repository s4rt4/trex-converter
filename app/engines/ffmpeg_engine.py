from __future__ import annotations

import asyncio
import re
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


VIDEO_FORMATS = ("mp4", "mov", "webm", "mkv")
AUDIO_FORMATS = ("mp3", "wav", "aac", "flac", "m4a", "opus", "ogg")
ANIMATED_OUTPUT_FORMATS = ("gif", "webp")
IMAGE_OUTPUT_FORMATS = ("png", "jpg", "jpeg")

SUPPORTED_PAIRS = (
    {(fmt_in, fmt_out) for fmt_in in VIDEO_FORMATS for fmt_out in VIDEO_FORMATS}
    | {(fmt_in, fmt_out) for fmt_in in VIDEO_FORMATS for fmt_out in AUDIO_FORMATS}
    | {(fmt_in, fmt_out) for fmt_in in AUDIO_FORMATS for fmt_out in AUDIO_FORMATS}
    | {(fmt_in, fmt_out) for fmt_in in VIDEO_FORMATS for fmt_out in ANIMATED_OUTPUT_FORMATS}
    | {(fmt_in, fmt_out) for fmt_in in VIDEO_FORMATS for fmt_out in IMAGE_OUTPUT_FORMATS}
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
GRAVITY_OVERLAY_POS = {
    "northwest": "20:20",
    "north": "(W-w)/2:20",
    "northeast": "W-w-20:20",
    "west": "20:(H-h)/2",
    "center": "(W-w)/2:(H-h)/2",
    "east": "W-w-20:(H-h)/2",
    "southwest": "20:H-h-20",
    "south": "(W-w)/2:H-h-20",
    "southeast": "W-w-20:H-h-20",
}
AUDIO_OUTPUT_FORMATS = set(AUDIO_FORMATS)
ANIMATED_OUTPUT_SET = set(ANIMATED_OUTPUT_FORMATS)
IMAGE_OUTPUT_SET = set(IMAGE_OUTPUT_FORMATS)

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
        fmt_out = task.format_out.lower()
        options = task.options

        operation = str(options.get("operation") or "").lower()
        if operation == "concat":
            return _build_concat_command(task, output_path)
        if operation == "mix":
            return _build_mix_command(task, output_path)

        if fmt_out == "gif":
            return _build_gif_command(task, output_path)

        is_audio_only = fmt_out in AUDIO_OUTPUT_FORMATS
        is_image_only = fmt_out in IMAGE_OUTPUT_SET
        is_animated_image = fmt_out == "webp"
        use_logo = bool(options.get("logo_path")) and not is_audio_only and not is_image_only

        command = ["ffmpeg", "-y", "-i", str(task.input_path)]
        if use_logo:
            command.extend(["-i", str(options["logo_path"])])
        command.extend(_trim_options(options))

        if is_image_only:
            return _finish_image_command(command, options, output_path)

        if is_animated_image:
            return _finish_webp_command(command, options, output_path)

        if use_logo:
            command.extend(["-filter_complex", _logo_filter_complex(options)])
            command.extend(["-map", "[vout]"])
            if not is_audio_only:
                command.extend(["-map", "0:a?"])
        else:
            video_filter = "" if is_audio_only else _video_filter_chain(options)
            if video_filter:
                command.extend(["-vf", video_filter])

        audio_filter = _audio_filter_chain(options, drop_audio=False)
        if audio_filter:
            command.extend(["-af", audio_filter])

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

    burn_path = options.get("burn_subtitle_path")
    if burn_path:
        filters.append(_subtitle_filter(str(burn_path)))

    watermark_text = options.get("watermark_text")
    if watermark_text:
        filters.append(_drawtext_filter(options))

    if options.get("reverse_video"):
        filters.append("reverse")

    return ",".join(filters)


def _audio_filter_chain(options: dict, *, drop_audio: bool) -> str:
    if drop_audio:
        return ""
    filters: list[str] = []

    speed = _float_option(options.get("speed"))
    if speed and speed > 0 and abs(speed - 1.0) > 1e-3:
        filters.extend(_atempo_chain(speed))

    fade_in = _float_option(options.get("fade_in_duration"))
    if fade_in and fade_in > 0:
        filters.append(f"afade=t=in:st=0:d={_format_seconds(fade_in)}")

    fade_out_duration = _float_option(options.get("fade_out_duration"))
    fade_out_start = _float_option(options.get("fade_out_start"))
    if fade_out_duration and fade_out_duration > 0:
        if fade_out_start is None or fade_out_start < 0:
            raise RuntimeError(
                "fade_out_duration requires fade_out_start (seconds from clip start)"
            )
        filters.append(
            f"afade=t=out:st={_format_seconds(fade_out_start)}:d={_format_seconds(fade_out_duration)}"
        )

    volume_db = _float_option(options.get("volume_db"))
    if volume_db is not None and abs(volume_db) > 1e-3:
        sign = "+" if volume_db > 0 else ""
        filters.append(f"volume={sign}{_format_seconds(volume_db)}dB")

    if options.get("vocal_remove"):
        filters.append("pan=stereo|c0=c0-c1|c1=c1-c0")

    if options.get("loudnorm"):
        filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

    if options.get("reverse_video"):
        filters.append("areverse")

    return ",".join(filters)


def _format_seconds(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text or "0"


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


def _subtitle_filter(path: str) -> str:
    escaped = (
        str(path)
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )
    if path.lower().endswith(".ass") or path.lower().endswith(".ssa"):
        return f"ass={escaped}"
    return f"subtitles={escaped}"


def _logo_filter_complex(options: dict) -> str:
    video_chain = _video_filter_chain(options)
    parts: list[str] = []
    if video_chain:
        parts.append(f"[0:v]{video_chain}[v0]")
        v_in = "[v0]"
    else:
        v_in = "[0:v]"

    logo_width = _int_option(options.get("logo_width")) or 120
    logo_opacity = _int_option(options.get("logo_opacity"))
    if logo_opacity is None:
        logo_opacity = 100
    alpha = max(0.0, min(1.0, logo_opacity / 100.0))

    logo_chain = f"[1:v]scale={logo_width}:-1"
    if alpha < 0.999:
        logo_chain += f",format=rgba,colorchannelmixer=aa={alpha:.2f}"
    parts.append(f"{logo_chain}[logo]")

    gravity = str(options.get("logo_position") or "southeast").lower()
    if gravity not in GRAVITY_OVERLAY_POS:
        raise RuntimeError(f"Unknown logo position: {gravity}")
    parts.append(f"{v_in}[logo]overlay={GRAVITY_OVERLAY_POS[gravity]}[vout]")

    return ";".join(parts)


def _build_concat_command(task: Task, output_path: Path) -> list[str]:
    sources = list(task.inputs)
    if len(sources) < 2:
        raise RuntimeError("Concat requires at least two input files")

    fmt_out = task.format_out.lower()
    is_audio_only = fmt_out in AUDIO_OUTPUT_FORMATS
    n = len(sources)

    command = ["ffmpeg", "-y"]
    for source in sources:
        command.extend(["-i", str(source)])

    if is_audio_only:
        labels = "".join(f"[{i}:a:0]" for i in range(n))
        filter_complex = f"{labels}concat=n={n}:v=0:a=1[outa]"
        command.extend(["-filter_complex", filter_complex])
        command.extend(["-map", "[outa]"])
    else:
        labels = "".join(f"[{i}:v:0][{i}:a:0]" for i in range(n))
        filter_complex = f"{labels}concat=n={n}:v=1:a=1[outv][outa]"
        command.extend(["-filter_complex", filter_complex])
        command.extend(["-map", "[outv]", "-map", "[outa]"])

    command.extend(_codec_options(task))
    command.extend(["-progress", "pipe:2", "-nostats", str(output_path)])
    return command


_MIX_DURATIONS = {"longest", "shortest", "first"}


def _build_mix_command(task: Task, output_path: Path) -> list[str]:
    sources = list(task.inputs)
    if len(sources) < 2:
        raise RuntimeError("Mix requires at least two input files")

    duration = str(task.options.get("mix_duration") or "longest").lower()
    if duration not in _MIX_DURATIONS:
        raise RuntimeError(
            f"mix_duration must be one of {sorted(_MIX_DURATIONS)}, got {duration}"
        )
    normalize = task.options.get("mix_normalize")
    if normalize is None:
        normalize = True

    n = len(sources)
    command = ["ffmpeg", "-y"]
    for source in sources:
        command.extend(["-i", str(source)])

    labels = "".join(f"[{i}:a:0]" for i in range(n))
    chain = f"amix=inputs={n}:duration={duration}:normalize={1 if normalize else 0}"
    filter_complex = f"{labels}{chain}[outa]"
    command.extend(["-filter_complex", filter_complex])
    command.extend(["-map", "[outa]"])

    command.extend(_codec_options(task))
    command.extend(["-progress", "pipe:2", "-nostats", str(output_path)])
    return command


def _build_gif_command(task: Task, output_path: Path) -> list[str]:
    options = task.options
    fps = _int_option(options.get("gif_fps")) or 12
    width = _int_option(options.get("gif_width")) or 480

    pre_chain = _video_filter_chain(options)
    base = f"fps={fps},scale={width}:-1:flags=lanczos"
    pre = f"{pre_chain}," if pre_chain else ""
    filter_complex = (
        f"[0:v]{pre}{base},split[a][b];"
        f"[a]palettegen=max_colors=256[p];"
        f"[b][p]paletteuse=dither=bayer:bayer_scale=5"
    )

    command = ["ffmpeg", "-y", "-i", str(task.input_path)]
    command.extend(_trim_options(options))
    command.extend(["-filter_complex", filter_complex])
    command.extend(["-loop", "0", "-an"])
    command.extend(["-progress", "pipe:2", "-nostats", str(output_path)])
    return command


def _finish_webp_command(command: list[str], options: dict, output_path: Path) -> list[str]:
    fps = _int_option(options.get("webp_fps")) or 15
    width = _int_option(options.get("webp_width")) or 480

    pre_chain = _video_filter_chain(options)
    base = f"fps={fps},scale={width}:-1:flags=lanczos"
    vf = f"{pre_chain},{base}" if pre_chain else base

    command.extend(["-vf", vf])
    quality = _int_option(options.get("webp_quality")) or 75
    command.extend([
        "-c:v", "libwebp",
        "-loop", "0",
        "-lossless", "0",
        "-compression_level", "6",
        "-q:v", str(quality),
        "-an",
    ])
    command.extend(["-progress", "pipe:2", "-nostats", str(output_path)])
    return command


def _finish_image_command(command: list[str], options: dict, output_path: Path) -> list[str]:
    if options.get("thumbnail_grid"):
        command.extend(["-vf", _thumbnail_grid_filter(options)])
        command.extend(["-frames:v", "1", "-an", str(output_path)])
        return command

    vf = _video_filter_chain(options)
    if vf:
        command.extend(["-vf", vf])
    command.extend(["-frames:v", "1", "-an", str(output_path)])
    return command


def _thumbnail_grid_filter(options: dict) -> str:
    rows = max(1, _int_option(options.get("thumbnail_rows")) or 4)
    cols = max(1, _int_option(options.get("thumbnail_cols")) or 4)
    interval = max(1, _int_option(options.get("thumbnail_interval")) or 60)
    tile_width = max(64, _int_option(options.get("thumbnail_tile_width")) or 320)
    return (
        f"select='not(mod(n\\,{interval}))',"
        f"scale={tile_width}:-1,"
        f"tile={cols}x{rows}"
    )


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

    channels = task.options.get("audio_channels")
    if channels:
        options.extend(["-ac", str(channels)])

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

    options.extend(_metadata_options(task.options))

    return options


_ID3_FIELDS = {
    "title": "title",
    "artist": "artist",
    "album": "album",
    "year": "date",
    "track": "track",
    "genre": "genre",
    "comment": "comment",
    "album_artist": "album_artist",
}


def _metadata_options(options: dict) -> list[str]:
    args: list[str] = []
    for option_key, ffmpeg_key in _ID3_FIELDS.items():
        value = options.get(f"id3_{option_key}")
        if value is None or value == "":
            continue
        args.extend(["-metadata", f"{ffmpeg_key}={value}"])
    return args


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
