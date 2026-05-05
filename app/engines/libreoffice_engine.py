from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


TEXT_INPUTS = {"doc", "docx", "odt", "rtf"}
TEXT_OUTPUTS = {"docx", "odt", "rtf", "html", "epub", "txt", "pdf"}
SPREADSHEET_INPUTS = {"xls", "xlsx", "ods"}
SPREADSHEET_OUTPUTS = {"xlsx", "ods", "csv", "html", "pdf"}
PRESENTATION_INPUTS = {"ppt", "pptx", "odp"}
PRESENTATION_OUTPUTS = {"pptx", "odp", "pdf"}

SUPPORTED_INPUT_FORMATS = TEXT_INPUTS | SPREADSHEET_INPUTS | PRESENTATION_INPUTS

SUPPORTED_PAIRS = (
    {(fmt_in, fmt_out) for fmt_in in TEXT_INPUTS for fmt_out in TEXT_OUTPUTS}
    | {(fmt_in, fmt_out) for fmt_in in SPREADSHEET_INPUTS for fmt_out in SPREADSHEET_OUTPUTS}
    | {(fmt_in, fmt_out) for fmt_in in PRESENTATION_INPUTS for fmt_out in PRESENTATION_OUTPUTS}
    | {(fmt_in, "folder") for fmt_in in PRESENTATION_INPUTS}
)
DEFAULT_TIMEOUT_SECONDS = 120


class LibreOfficeEngine(BaseEngine):
    name = "libreoffice"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=False,
            supports_cancel=True,
            requires_binary="libreoffice",
        )
        self._processes: dict[str, asyncio.subprocess.Process] = {}

    async def convert(self, task: Task) -> None:
        operation = str(task.options.get("operation") or "").lower()
        if operation == "bulk_merge_to_pdf":
            await self._bulk_merge_to_pdf(task)
            return
        if operation == "slides_to_images":
            await self._slides_to_images(task)
            return

        output_path = Path(task.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="trex-libreoffice-") as temp_dir:
            temp_output_dir = Path(temp_dir)
            target_format = _convert_to_format(task.format_out, task.options)
            await self._convert_one(
                task, task.input_path, temp_output_dir, task.format_out, target_format
            )
            produced_path = _find_converted_file(
                task.input_path, temp_output_dir, task.format_out
            )
            shutil.move(str(produced_path), str(output_path))
            task.progress = 1.0

    async def _convert_one(
        self,
        task: Task,
        input_path: Path,
        output_dir: Path,
        format_out: str,
        target_format: str | None = None,
    ) -> None:
        command = [
            "libreoffice",
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--convert-to",
            target_format or format_out,
            "--outdir",
            str(output_dir),
            str(input_path),
        ]
        task.append_log("Running: " + " ".join(command))
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._processes[task.id] = process
        try:
            timeout = _timeout_seconds(task)
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
            _append_output(task, stdout)
            _append_output(task, stderr)
            if process.returncode != 0:
                raise RuntimeError(
                    f"LibreOffice exited with code {process.returncode}"
                )
        except asyncio.TimeoutError as exc:
            await self.cancel(task)
            raise RuntimeError(
                f"LibreOffice timed out after {_timeout_seconds(task)} seconds"
            ) from exc
        except asyncio.CancelledError:
            await self.cancel(task)
            raise
        finally:
            self._processes.pop(task.id, None)

    async def _slides_to_images(self, task: Task) -> None:
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError(
                "PyMuPDF is required for PPTX slide rendering."
            ) from exc

        output_dir = Path(task.output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        image_format = str(task.options.get("slides_image_format") or "png").lower()
        if image_format not in {"png", "jpg", "jpeg"}:
            raise RuntimeError(f"slides_image_format must be png or jpg, got {image_format}")
        dpi = max(72, min(600, int(task.options.get("slides_dpi") or 200)))

        task.append_log(
            f"Slides to {image_format.upper()}: rendering via PDF intermediate at {dpi} DPI"
        )

        with tempfile.TemporaryDirectory(prefix="trex-slides-") as temp_dir:
            temp_root = Path(temp_dir)
            await self._convert_one(task, task.input_path, temp_root, "pdf")
            pdf_path = _find_converted_file(task.input_path, temp_root, "pdf")

            stem = Path(task.input_path).stem
            document = fitz.open(str(pdf_path))
            try:
                page_count = len(document)
                if page_count == 0:
                    raise RuntimeError("Slide deck has no pages after conversion")
                for index in range(page_count):
                    page = document.load_page(index)
                    pixmap = page.get_pixmap(dpi=dpi, alpha=False)
                    out_name = f"{stem}-{index + 1:03d}.{image_format}"
                    pixmap.save(str(output_dir / out_name))
                    task.append_log(f"Wrote slide {index + 1}/{page_count}: {out_name}")
                    task.progress = 0.4 + 0.55 * ((index + 1) / page_count)
                    await asyncio.sleep(0)
            finally:
                document.close()

        task.append_log(f"Wrote {page_count} slide image(s) to {output_dir}")
        task.progress = 1.0

    async def _bulk_merge_to_pdf(self, task: Task) -> None:
        sources = list(task.inputs)
        if len(sources) < 2:
            raise RuntimeError("Bulk merge requires at least two input documents")

        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError(
                "PyMuPDF is required for bulk merge. Reinstall with: pip install -e ."
            ) from exc

        output_path = Path(task.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        task.append_log(f"Bulk merge: combining {len(sources)} document(s) to PDF")

        with tempfile.TemporaryDirectory(prefix="trex-bulk-merge-") as temp_dir:
            temp_root = Path(temp_dir)
            stage_pdfs: list[Path] = []
            for index, source in enumerate(sources, start=1):
                if source.suffix.lower().lstrip(".") == "pdf":
                    stage_pdfs.append(source)
                    task.append_log(f"[{index}/{len(sources)}] kept PDF: {source.name}")
                else:
                    convert_dir = temp_root / f"src-{index:03d}"
                    convert_dir.mkdir(parents=True, exist_ok=True)
                    await self._convert_one(task, source, convert_dir, "pdf")
                    produced = _find_converted_file(source, convert_dir, "pdf")
                    stage_pdfs.append(produced)
                    task.append_log(
                        f"[{index}/{len(sources)}] converted {source.name} -> PDF"
                    )
                task.progress = 0.05 + 0.7 * (index / len(sources))
                await asyncio.sleep(0)

            result = fitz.open()
            try:
                for pdf_path in stage_pdfs:
                    chunk = fitz.open(str(pdf_path))
                    try:
                        result.insert_pdf(chunk)
                    finally:
                        chunk.close()
                if len(result) == 0:
                    raise RuntimeError("Bulk merge produced an empty PDF")
                result.save(str(output_path), garbage=3, deflate=True)
            finally:
                result.close()

        task.append_log(f"Wrote merged PDF: {output_path} ({len(sources)} sources)")
        task.progress = 1.0

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

    def _build_command(self, task: Task, output_dir: Path) -> list[str]:
        return [
            "libreoffice",
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--convert-to",
            task.format_out,
            "--outdir",
            str(output_dir),
            str(task.input_path),
        ]


def _convert_to_format(format_out: str, options: dict) -> str:
    """Build the --convert-to argument, honoring the pdf_a flag for PDF outputs."""
    suffix = format_out.lower()
    if suffix == "pdf" and options.get("pdf_a"):
        # SelectPdfVersion=1 -> PDF/A-1a (LibreOffice writer_pdf_Export filter).
        return (
            'pdf:writer_pdf_Export:'
            '{"SelectPdfVersion":{"type":"long","value":"1"}}'
        )
    return suffix


def _timeout_seconds(task: Task) -> float:
    timeout = task.options.get("timeout", DEFAULT_TIMEOUT_SECONDS)
    try:
        return float(timeout)
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT_SECONDS


def _append_output(task: Task, output: bytes) -> None:
    text = output.decode("utf-8", errors="replace").strip()
    if text:
        task.append_log(text)


def _find_converted_file(input_path: Path, output_dir: Path, format_out: str) -> Path:
    suffix = format_out.lower()
    expected_path = output_dir / f"{Path(input_path).stem}.{suffix}"
    if expected_path.exists():
        return expected_path

    matches = sorted(output_dir.glob(f"*.{suffix}"))
    if len(matches) == 1:
        return matches[0]

    raise RuntimeError(
        f"LibreOffice did not produce a .{suffix} output file"
    )
