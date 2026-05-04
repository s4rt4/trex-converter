from __future__ import annotations

import asyncio
import re
from pathlib import Path
from types import ModuleType

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


PDF_IMAGE_FORMATS = {"jpg", "jpeg", "png"}
PDF_TEXT_FORMATS = {"txt", "html"}
SUPPORTED_PAIRS = (
    {("pdf", format_out) for format_out in PDF_IMAGE_FORMATS}
    | {("pdf", "pdf")}
    | {("pdf", format_out) for format_out in PDF_TEXT_FORMATS}
)
DEFAULT_DPI = 200
PDF_METADATA_FIELDS = ("title", "author", "subject", "keywords", "creator", "producer")
PDF_OPERATIONS = {
    "extract_pages",
    "reorder",
    "rotate",
    "compress",
    "repair",
    "encrypt",
    "decrypt",
    "strip_metadata",
    "edit_metadata",
    "watermark_text",
}
GRAVITY_TO_FRACTION = {
    "northwest": (0.05, 0.08),
    "north": (0.5, 0.08),
    "northeast": (0.95, 0.08),
    "west": (0.05, 0.5),
    "center": (0.5, 0.5),
    "east": (0.95, 0.5),
    "southwest": (0.05, 0.95),
    "south": (0.5, 0.95),
    "southeast": (0.95, 0.95),
}


class PDFEngine(BaseEngine):
    name = "pdf"

    def __init__(self) -> None:
        self._capabilities = EngineCapabilities(
            supports_progress=True,
            supports_cancel=False,
            requires_binary="python:fitz",
        )

    async def convert(self, task: Task) -> None:
        format_out = task.format_out.lower()
        output_path = Path(task.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format_out in PDF_IMAGE_FORMATS:
            await self._render_pages(task, output_path)
        elif format_out == "txt":
            await self._extract_text(task, output_path)
        elif format_out == "html":
            await self._extract_html(task, output_path)
        elif format_out == "pdf":
            await self._run_pdf_operation(task, output_path)
        else:
            raise RuntimeError(f"Unsupported PDF output format: {task.format_out}")

    def supports(self, format_in: str, format_out: str) -> bool:
        return (format_in.lower(), format_out.lower()) in SUPPORTED_PAIRS

    @property
    def capabilities(self) -> EngineCapabilities:
        return self._capabilities

    async def _render_pages(self, task: Task, output_path: Path) -> None:
        fitz = _load_fitz()
        dpi = _dpi(task)
        task.append_log(
            f"Rendering PDF pages at {dpi} DPI to {task.format_out.upper()}"
        )
        document = fitz.open(str(task.input_path))
        try:
            page_count = len(document)
            if page_count == 0:
                raise RuntimeError("PDF has no pages")

            pages = _selected_pages(task, page_count)
            for index, page_number in enumerate(pages, start=1):
                page = document.load_page(page_number)
                pixmap = page.get_pixmap(dpi=dpi, alpha=False)
                page_output = _page_output_path(output_path, page_number, len(pages))
                pixmap.save(str(page_output))
                task.append_log(f"Rendered page {page_number + 1}: {page_output}")
                task.progress = index / len(pages)
                await asyncio.sleep(0)
        finally:
            _close(document)

    async def _extract_text(self, task: Task, output_path: Path) -> None:
        fitz = _load_fitz()
        task.append_log("Extracting text via PyMuPDF")
        document = fitz.open(str(task.input_path))
        try:
            page_count = len(document)
            chunks: list[str] = []
            for index in range(page_count):
                page = document.load_page(index)
                chunks.append(page.get_text())
                task.progress = (index + 1) / max(page_count, 1)
                await asyncio.sleep(0)
        finally:
            _close(document)

        output_path.write_text("\n".join(chunks), encoding="utf-8")
        task.append_log(f"Wrote text: {output_path}")
        task.progress = 1.0

    async def _run_qpdf_repair(self, task: Task, output_path: Path) -> None:
        command = ["qpdf", str(task.input_path), str(output_path)]
        task.append_log("Running: " + " ".join(command))
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await process.communicate()
        for stream in (stdout_bytes, stderr_bytes):
            text = stream.decode("utf-8", errors="replace").strip()
            if text:
                task.append_log(text)
        # qpdf returns 0 = success, 3 = success with warnings (non-fatal)
        if process.returncode not in (0, 3):
            raise RuntimeError(f"qpdf exited with code {process.returncode}")
        task.append_log(f"Repaired PDF written to {output_path}")
        task.progress = 1.0

    async def _extract_html(self, task: Task, output_path: Path) -> None:
        fitz = _load_fitz()
        task.append_log("Extracting HTML via PyMuPDF")
        document = fitz.open(str(task.input_path))
        try:
            page_count = len(document)
            page_chunks: list[str] = []
            for index in range(page_count):
                page = document.load_page(index)
                page_chunks.append(
                    f'<section class="pdf-page" data-page="{index + 1}">'
                )
                page_chunks.append(page.get_text("html"))
                page_chunks.append("</section>")
                task.progress = (index + 1) / max(page_count, 1)
                await asyncio.sleep(0)
        finally:
            _close(document)

        title = Path(task.input_path).stem
        body = "\n".join(page_chunks)
        document_html = (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '<meta charset="utf-8">\n'
            f"<title>{title}</title>\n"
            "</head>\n"
            "<body>\n"
            f"{body}\n"
            "</body>\n"
            "</html>\n"
        )
        output_path.write_text(document_html, encoding="utf-8")
        task.append_log(f"Wrote HTML: {output_path}")
        task.progress = 1.0

    async def _run_pdf_operation(self, task: Task, output_path: Path) -> None:
        operation = (task.options.get("operation") or "extract_pages").lower()
        if operation not in PDF_OPERATIONS:
            raise RuntimeError(f"Unsupported PDF operation: {operation}")

        if operation == "repair":
            await self._run_qpdf_repair(task, output_path)
            return

        fitz = _load_fitz()
        task.append_log(f"PDF operation: {operation}")

        password = task.options.get("password") or task.options.get("password_user")
        document = fitz.open(str(task.input_path))
        try:
            if document.needs_pass:
                if not password:
                    raise RuntimeError("PDF is encrypted; provide password")
                if not document.authenticate(str(password)):
                    raise RuntimeError("Invalid password for encrypted PDF")

            page_count = len(document)
            if page_count == 0:
                raise RuntimeError("PDF has no pages")

            handler = {
                "extract_pages": _op_extract_pages,
                "reorder": _op_reorder,
                "rotate": _op_rotate,
                "compress": _op_compress,
                "encrypt": _op_encrypt,
                "decrypt": _op_decrypt,
                "strip_metadata": _op_strip_metadata,
                "edit_metadata": _op_edit_metadata,
                "watermark_text": _op_watermark_text,
            }[operation]

            handler(document, fitz, task, page_count)
            task.progress = 0.95

            save_kwargs = _save_kwargs_for(operation, fitz, task)
            document.save(str(output_path), **save_kwargs)
        finally:
            _close(document)

        task.append_log(f"Wrote PDF: {output_path}")
        task.progress = 1.0


def _op_extract_pages(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    pages = _parse_page_range(task.options.get("pages"), page_count)
    if not pages:
        raise RuntimeError("No pages selected for extraction")
    document.select(pages)
    task.append_log(f"Extracted {len(pages)} page(s)")


def _op_reorder(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    pages = _parse_page_range(task.options.get("pages"), page_count)
    if not pages:
        raise RuntimeError("Reorder requires an explicit page list (e.g. 3,1,2,4)")
    document.select(pages)
    task.append_log(f"Reordered to {len(pages)} page(s) in given order")


def _op_edit_metadata(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    metadata: dict[str, str] = {}
    for field in PDF_METADATA_FIELDS:
        value = task.options.get(f"meta_{field}")
        if value is None or value == "":
            continue
        metadata[field] = str(value)
    if not metadata:
        raise RuntimeError(
            "Provide at least one metadata field (title, author, subject, keywords, creator, producer)"
        )
    document.set_metadata(metadata)
    task.append_log(f"Set metadata: {', '.join(sorted(metadata.keys()))}")


def _op_rotate(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    degrees = _int_option(task.options.get("rotation_degrees")) or 90
    degrees = ((degrees % 360) + 360) % 360
    target_pages = _parse_page_range(task.options.get("pages"), page_count) or list(
        range(page_count)
    )
    for index in target_pages:
        page = document.load_page(index)
        page.set_rotation((page.rotation + degrees) % 360)
    task.append_log(f"Rotated {len(target_pages)} page(s) by {degrees}°")


def _op_compress(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    task.append_log("Compressing via PyMuPDF garbage collection + deflate")


def _op_encrypt(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    if not task.options.get("password_user") and not task.options.get("password_owner"):
        raise RuntimeError("Encryption requires password_user or password_owner")
    task.append_log("Applied encryption on save")


def _op_decrypt(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    task.append_log("Decrypting (saving without encryption)")


def _op_strip_metadata(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    document.set_metadata({})
    task.append_log("Stripped document metadata")


def _op_watermark_text(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    text = task.options.get("watermark_text")
    if not text:
        raise RuntimeError("watermark_text option is required")
    gravity = str(task.options.get("watermark_position") or "center").lower()
    fraction = GRAVITY_TO_FRACTION.get(gravity, GRAVITY_TO_FRACTION["center"])
    fontsize = _int_option(task.options.get("watermark_size")) or 48
    opacity = _int_option(task.options.get("watermark_opacity"))
    if opacity is None:
        opacity = 35
    fill_opacity = max(0.0, min(1.0, opacity / 100.0))
    color = (0.5, 0.5, 0.5)

    for index in range(page_count):
        page = document.load_page(index)
        rect = page.rect
        x = rect.x0 + rect.width * fraction[0]
        y = rect.y0 + rect.height * fraction[1]
        page.insert_text(
            (x, y),
            str(text),
            fontsize=fontsize,
            color=color,
            fill_opacity=fill_opacity,
        )
    task.append_log(
        f"Watermarked {page_count} page(s) at {gravity} (size {fontsize}, opacity {opacity}%)"
    )


def _save_kwargs_for(operation: str, fitz: ModuleType, task: Task) -> dict:
    if operation == "compress":
        return {"garbage": 4, "deflate": True, "clean": True}

    if operation == "encrypt":
        permissions = -1
        return {
            "encryption": getattr(fitz, "PDF_ENCRYPT_AES_256", 4),
            "owner_pw": str(task.options.get("password_owner") or ""),
            "user_pw": str(task.options.get("password_user") or ""),
            "permissions": permissions,
        }

    if operation == "decrypt":
        return {
            "encryption": getattr(fitz, "PDF_ENCRYPT_NONE", 0),
            "garbage": 3,
            "deflate": True,
        }

    return {"garbage": 3, "deflate": True}


def _load_fitz() -> ModuleType:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required for PDF processing. "
            "Reinstall dependencies with: pip install -e ."
        ) from exc
    return fitz


def _close(document) -> None:
    close = getattr(document, "close", None)
    if close:
        close()


def _dpi(task: Task) -> int:
    value = task.options.get("dpi", DEFAULT_DPI)
    try:
        dpi = int(value)
    except (TypeError, ValueError):
        return DEFAULT_DPI
    return max(72, min(600, dpi))


def _int_option(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _selected_pages(task: Task, page_count: int) -> list[int]:
    page_range = task.options.get("pages")
    if page_range:
        parsed = _parse_page_range(page_range, page_count)
        if parsed:
            return parsed

    page = task.options.get("page")
    if page in (None, "", "all"):
        return list(range(page_count))

    try:
        page_number = int(page)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("PDF page option must be a 1-based page number") from exc

    if page_number < 1 or page_number > page_count:
        raise RuntimeError(f"PDF page {page_number} is outside 1-{page_count}")
    return [page_number - 1]


def _parse_page_range(raw: object, page_count: int) -> list[int]:
    if raw in (None, "", "all"):
        return []
    text = str(raw).replace(" ", "")
    if not text:
        return []

    selected: list[int] = []
    seen: set[int] = set()
    pattern = re.compile(r"^(\d+)(?:-(\d+))?$")
    for token in text.split(","):
        if not token:
            continue
        match = pattern.match(token)
        if not match:
            raise RuntimeError(f"Invalid page range token: {token}")
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        if start < 1 or end < 1 or start > page_count or end > page_count:
            raise RuntimeError(
                f"Page range {token} outside document (1-{page_count})"
            )
        if start > end:
            start, end = end, start
        for page_number in range(start, end + 1):
            zero_based = page_number - 1
            if zero_based not in seen:
                seen.add(zero_based)
                selected.append(zero_based)
    return selected


def _page_output_path(output_path: Path, page_index: int, selected_count: int) -> Path:
    if selected_count == 1:
        return output_path
    return output_path.with_name(
        f"{output_path.stem}-{page_index + 1:03d}{output_path.suffix}"
    )
