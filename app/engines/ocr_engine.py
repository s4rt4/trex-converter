from __future__ import annotations

import asyncio
import re
import tempfile
from pathlib import Path
from types import ModuleType

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


OCR_IMAGE_INPUT_FORMATS = ("png", "jpg", "jpeg", "tif", "tiff", "bmp")
OCR_INPUT_FORMATS = (*OCR_IMAGE_INPUT_FORMATS, "pdf")
OCR_OUTPUT_FORMATS = ("txt", "pdf", "hocr", "tsv")
SUPPORTED_PAIRS = {
    (fmt_in, fmt_out)
    for fmt_in in OCR_INPUT_FORMATS
    for fmt_out in OCR_OUTPUT_FORMATS
}

VALID_PSM = set(range(0, 14))
VALID_OEM = {0, 1, 2, 3}

_OUTPUT_EXT = {"pdf": ".pdf", "hocr": ".hocr", "tsv": ".tsv", "txt": ".txt"}
_OSD_ROTATE_RE = re.compile(r"^Rotate:\s*(-?\d+)", re.MULTILINE)
_HOCR_PAGE_RE = re.compile(
    r"<div\s+class=['\"]ocr_page['\"].*?</div>\s*(?=<div\s+class=['\"]ocr_page['\"]|</body>)",
    re.DOTALL,
)
_HOCR_PAGE_ID_RE = re.compile(r"id=['\"]page_\d+['\"]")


class TesseractOCREngine(BaseEngine):
    name = "tesseract"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=True,
            supports_cancel=True,
            requires_binary="tesseract",
        )
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def convert(self, task: Task) -> None:
        if task.format_in.lower() == "pdf":
            await self._convert_pdf(task)
        else:
            await self._convert_image(task)

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

    async def _convert_image(self, task: Task) -> None:
        command = self._build_command(task)
        task.append_log("Running: " + " ".join(command))

        Path(task.output_path).parent.mkdir(parents=True, exist_ok=True)

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes[task.id] = process

        try:
            _, stderr_bytes = await process.communicate()
            stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
            if stderr_text:
                for line in stderr_text.splitlines():
                    if line.strip():
                        task.append_log(line.strip())

            if process.returncode != 0:
                raise RuntimeError(f"tesseract exited with code {process.returncode}")
            task.progress = 1.0
        except asyncio.CancelledError:
            await self.cancel(task)
            raise
        finally:
            self._processes.pop(task.id, None)

    async def _convert_pdf(self, task: Task) -> None:
        fitz = _load_fitz()
        Path(task.output_path).parent.mkdir(parents=True, exist_ok=True)

        format_out = task.format_out.lower()
        if format_out not in _OUTPUT_EXT:
            raise RuntimeError(f"Unsupported OCR output format: {task.format_out}")

        dpi = _clamped_dpi(task.options.get("ocr_dpi"))
        auto_rotate = bool(task.options.get("ocr_auto_rotate"))

        document = fitz.open(str(task.input_path))
        try:
            page_count = len(document)
            if page_count == 0:
                raise RuntimeError("PDF has no pages")
            task.append_log(f"OCR pipeline: {page_count} page(s) at {dpi} DPI")

            with tempfile.TemporaryDirectory(prefix="trex-ocr-") as tmpdir_str:
                tmpdir = Path(tmpdir_str)
                page_outputs: list[Path] = []
                try:
                    for index in range(page_count):
                        page_image = await self._render_page(
                            document, index, tmpdir, dpi, auto_rotate, task, fitz
                        )
                        page_output = await self._ocr_page(
                            page_image, tmpdir, index, format_out, task
                        )
                        page_outputs.append(page_output)
                        task.progress = 0.05 + 0.85 * ((index + 1) / page_count)
                        await asyncio.sleep(0)
                except asyncio.CancelledError:
                    await self.cancel(task)
                    raise

                _stitch_outputs(page_outputs, Path(task.output_path), format_out, fitz)
        finally:
            _close(document)

        task.append_log(f"Wrote OCR output: {task.output_path}")
        task.progress = 1.0

    async def _render_page(
        self,
        document,
        page_index: int,
        tmpdir: Path,
        dpi: int,
        auto_rotate: bool,
        task: Task,
        fitz: ModuleType,
    ) -> Path:
        page = document.load_page(page_index)
        page_image = tmpdir / f"page-{page_index + 1:04d}.png"
        pixmap = page.get_pixmap(dpi=dpi, alpha=False)
        pixmap.save(str(page_image))

        if auto_rotate:
            rotation = await self._detect_rotation(page_image, task)
            if rotation:
                page.set_rotation((page.rotation + rotation) % 360)
                rotated = page.get_pixmap(dpi=dpi, alpha=False)
                rotated.save(str(page_image))
                task.append_log(
                    f"Page {page_index + 1}: auto-rotated by {rotation}°"
                )

        return page_image

    async def _detect_rotation(self, image_path: Path, task: Task) -> int:
        command = ["tesseract", str(image_path), "-", "--psm", "0"]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes[task.id] = process
        try:
            stdout_bytes, _ = await process.communicate()
        finally:
            self._processes.pop(task.id, None)
        return parse_osd_rotation(stdout_bytes.decode("utf-8", errors="replace"))

    async def _ocr_page(
        self,
        page_image: Path,
        tmpdir: Path,
        page_index: int,
        format_out: str,
        task: Task,
    ) -> Path:
        page_stem = tmpdir / f"page-{page_index + 1:04d}"
        command = ["tesseract", str(page_image), str(page_stem)]
        command.extend(_language_args(task.options))
        command.extend(_psm_oem_args(task.options))
        command.extend(_format_args(format_out))

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes[task.id] = process
        try:
            _, stderr_bytes = await process.communicate()
            if process.returncode != 0:
                stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
                raise RuntimeError(
                    f"tesseract page {page_index + 1} failed (exit {process.returncode}): {stderr_text}"
                )
        finally:
            self._processes.pop(task.id, None)

        return page_stem.with_suffix(_OUTPUT_EXT[format_out])

    def _build_command(self, task: Task) -> list[str]:
        output_path = Path(task.output_path)
        output_stem = str(output_path.with_suffix(""))

        command = ["tesseract", str(task.input_path), output_stem]
        command.extend(_language_args(task.options))
        command.extend(_psm_oem_args(task.options))
        command.extend(_format_args(task.format_out.lower()))
        return command


def _language_args(options: dict) -> list[str]:
    language = (options.get("ocr_language") or "eng").strip()
    if not language:
        language = "eng"
    return ["-l", language]


def _psm_oem_args(options: dict) -> list[str]:
    args: list[str] = []
    psm = _int_option(options.get("ocr_psm"))
    if psm is not None:
        if psm not in VALID_PSM:
            raise RuntimeError(f"Invalid PSM (expected 0-13): {psm}")
        args.extend(["--psm", str(psm)])
    oem = _int_option(options.get("ocr_oem"))
    if oem is not None:
        if oem not in VALID_OEM:
            raise RuntimeError(f"Invalid OEM (expected 0-3): {oem}")
        args.extend(["--oem", str(oem)])
    return args


def _format_args(format_out: str) -> list[str]:
    if format_out == "pdf":
        return ["pdf"]
    if format_out == "hocr":
        return ["hocr"]
    if format_out == "tsv":
        return ["tsv"]
    return []


def parse_osd_rotation(text: str) -> int:
    match = _OSD_ROTATE_RE.search(text)
    if not match:
        return 0
    rotation = int(match.group(1))
    normalized = ((rotation % 360) + 360) % 360
    if normalized not in (0, 90, 180, 270):
        return 0
    return normalized


def stitch_text_pages(chunks: list[str]) -> str:
    cleaned = [chunk.rstrip("\n") for chunk in chunks]
    return "\n\f\n".join(cleaned).rstrip("\n") + "\n"


def stitch_hocr_pages(chunks: list[str]) -> str:
    if not chunks:
        return ""

    first = chunks[0]
    body_open = first.find("<body>")
    if body_open == -1:
        return first
    head = first[: body_open + len("<body>")] + "\n"

    page_divs: list[str] = []
    counter = 1
    for chunk in chunks:
        for match in _HOCR_PAGE_RE.finditer(chunk):
            div = match.group(0).rstrip()
            div = _HOCR_PAGE_ID_RE.sub(f"id='page_{counter}'", div, count=1)
            page_divs.append(div)
            counter += 1

    return head + "\n".join(page_divs) + "\n</body>\n</html>\n"


def stitch_tsv_pages(chunks: list[str]) -> str:
    if not chunks:
        return ""
    first_lines = chunks[0].splitlines()
    if not first_lines:
        return ""
    header = first_lines[0]
    output: list[str] = [header]
    for chunk in chunks:
        for line in chunk.splitlines()[1:]:
            output.append(line)
    return "\n".join(output) + "\n"


def _stitch_outputs(
    page_paths: list[Path],
    target_path: Path,
    format_out: str,
    fitz: ModuleType,
) -> None:
    if format_out == "pdf":
        result = fitz.open()
        try:
            for pdf_path in page_paths:
                chunk = fitz.open(str(pdf_path))
                try:
                    result.insert_pdf(chunk)
                finally:
                    _close(chunk)
            result.save(str(target_path))
        finally:
            _close(result)
        return

    chunks = [path.read_text(encoding="utf-8", errors="replace") for path in page_paths]
    if format_out == "txt":
        target_path.write_text(stitch_text_pages(chunks), encoding="utf-8")
    elif format_out == "hocr":
        target_path.write_text(stitch_hocr_pages(chunks), encoding="utf-8")
    elif format_out == "tsv":
        target_path.write_text(stitch_tsv_pages(chunks), encoding="utf-8")
    else:
        raise RuntimeError(f"Unsupported OCR stitch format: {format_out}")


def _load_fitz() -> ModuleType:
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError(
                "PyMuPDF is required for PDF OCR. Reinstall dependencies with: pip install -e ."
            ) from exc
    return fitz


def _close(document) -> None:
    close = getattr(document, "close", None)
    if close:
        close()


def _clamped_dpi(value: object) -> int:
    parsed = _int_option(value)
    if parsed is None:
        return 300
    return max(72, min(600, parsed))


def _int_option(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
