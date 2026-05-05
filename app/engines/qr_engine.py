from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


GENERATE_PAIRS = {("txt", "png"), ("txt", "svg")}
DECODE_INPUT_FORMATS = ("png", "jpg", "jpeg", "bmp", "tif", "tiff", "gif", "webp")
DECODE_PAIRS = {(fmt, "txt") for fmt in DECODE_INPUT_FORMATS}
SUPPORTED_PAIRS = GENERATE_PAIRS | DECODE_PAIRS

ECC_LEVELS = {"L", "M", "Q", "H"}
QRENCODE_TYPES = {"png": "PNG", "svg": "SVG"}


class QREngine(BaseEngine):
    name = "qr"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=False,
            supports_cancel=True,
            requires_binary="qrencode",
            extra_binaries=("zbarimg",),
        )
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def convert(self, task: Task) -> None:
        pair = (task.format_in.lower(), task.format_out.lower())
        if pair in GENERATE_PAIRS:
            await self._generate(task)
        elif pair in DECODE_PAIRS:
            await self._decode(task)
        else:
            raise RuntimeError(
                f"Unsupported QR conversion: {task.format_in} -> {task.format_out}"
            )

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

    async def _generate(self, task: Task) -> None:
        output_path = Path(task.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = build_generate_command(task)
        task.append_log("Running: " + " ".join(command))
        await self._run(command, task, "qrencode")
        task.append_log(f"Wrote QR code: {output_path}")
        task.progress = 1.0

    async def _decode(self, task: Task) -> None:
        output_path = Path(task.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = build_decode_command(task)
        task.append_log("Running: " + " ".join(command))

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes[task.id] = process
        try:
            stdout_bytes, stderr_bytes = await process.communicate()
        except asyncio.CancelledError:
            await self.cancel(task)
            raise
        finally:
            self._processes.pop(task.id, None)

        if process.returncode not in (0, 4):
            stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"zbarimg exited with code {process.returncode}: {stderr_text}"
            )

        decoded = stdout_bytes.decode("utf-8", errors="replace").rstrip("\n")
        if not decoded:
            raise RuntimeError("zbarimg found no barcodes in the input image")

        output_path.write_text(decoded + "\n", encoding="utf-8")
        task.append_log(f"Wrote decoded text: {output_path}")
        task.progress = 1.0

    async def _run(self, command: list[str], task: Task, label: str) -> None:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes[task.id] = process
        try:
            _, stderr_bytes = await process.communicate()
        except asyncio.CancelledError:
            await self.cancel(task)
            raise
        finally:
            self._processes.pop(task.id, None)

        if process.returncode != 0:
            stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"{label} exited with code {process.returncode}: {stderr_text}"
            )


def build_generate_command(task: Task) -> list[str]:
    options = task.options
    output_path = Path(task.output_path)
    fmt_out = task.format_out.lower()
    if fmt_out not in QRENCODE_TYPES:
        raise RuntimeError(f"Unsupported QR output format: {task.format_out}")

    command = [
        "qrencode",
        "-r", str(task.input_path),
        "-o", str(output_path),
        "-t", QRENCODE_TYPES[fmt_out],
    ]

    size = _int_option(options.get("qr_size"))
    if size is not None:
        if size < 1 or size > 50:
            raise RuntimeError(f"qr_size must be between 1 and 50, got {size}")
        command.extend(["-s", str(size)])

    margin = _int_option(options.get("qr_margin"))
    if margin is not None:
        if margin < 0 or margin > 32:
            raise RuntimeError(f"qr_margin must be between 0 and 32, got {margin}")
        command.extend(["-m", str(margin)])

    level = options.get("qr_ecc_level")
    if level:
        normalized = str(level).upper()
        if normalized not in ECC_LEVELS:
            raise RuntimeError(f"qr_ecc_level must be one of L/M/Q/H, got {level}")
        command.extend(["-l", normalized])

    return command


def build_decode_command(task: Task) -> list[str]:
    return ["zbarimg", "--raw", "-q", str(task.input_path)]


def _int_option(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
