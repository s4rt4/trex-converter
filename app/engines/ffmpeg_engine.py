from __future__ import annotations

import asyncio
import re
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


SUPPORTED_PAIRS = {
    ("mp4", "mp3"),
    ("mp4", "webm"),
    ("mov", "mp4"),
    ("wav", "mp3"),
    ("flac", "mp3"),
}

_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


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
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(task.input_path),
        ]
        command.extend(_codec_options(task))
        command.extend(["-progress", "pipe:2", "-nostats", str(output_path)])
        return command


def _codec_options(task: Task) -> list[str]:
    options: list[str] = []
    if task.format_out == "mp3":
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
