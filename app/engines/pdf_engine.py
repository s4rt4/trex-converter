from __future__ import annotations

import asyncio
import re
from pathlib import Path
from types import ModuleType

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities


PDF_IMAGE_FORMATS = {"jpg", "jpeg", "png"}
PDF_TEXT_FORMATS = {"txt", "html"}
PDF_DOCUMENT_FORMATS = {"docx", "epub"}
PDF_FOLDER_OUTPUT = "folder"
SUPPORTED_PAIRS = (
    {("pdf", format_out) for format_out in PDF_IMAGE_FORMATS}
    | {("pdf", "pdf")}
    | {("pdf", format_out) for format_out in PDF_TEXT_FORMATS}
    | {("pdf", format_out) for format_out in PDF_DOCUMENT_FORMATS}
    | {("pdf", PDF_FOLDER_OUTPUT)}
)
DEFAULT_DPI = 200
PDF_METADATA_FIELDS = ("title", "author", "subject", "keywords", "creator", "producer")
PDF_OPERATIONS = {
    "extract_pages",
    "reorder",
    "rotate",
    "compress",
    "compress_images",
    "linearize",
    "repair",
    "encrypt",
    "decrypt",
    "strip_metadata",
    "edit_metadata",
    "watermark_text",
    "watermark_image",
    "page_numbering",
    "redact",
    "merge",
}
PDF_FOLDER_OPERATIONS = {"split", "extract_images", "extract_attachments"}
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

        if format_out == PDF_FOLDER_OUTPUT:
            operation = str(task.options.get("operation") or "split").lower()
            if operation == "split":
                await self._run_split(task, output_path)
            elif operation == "extract_images":
                await self._run_extract_images(task, output_path)
            elif operation == "extract_attachments":
                await self._run_extract_attachments(task, output_path)
            else:
                raise RuntimeError(
                    f"Unsupported folder operation: {operation} "
                    f"(expected one of: {sorted(PDF_FOLDER_OPERATIONS)})"
                )
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format_out in PDF_IMAGE_FORMATS:
            await self._render_pages(task, output_path)
        elif format_out == "txt":
            await self._extract_text(task, output_path)
        elif format_out == "html":
            await self._extract_html(task, output_path)
        elif format_out == "docx":
            await self._run_pdf_to_docx(task, output_path)
        elif format_out == "epub":
            await self._run_pdf_to_epub(task, output_path)
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

    async def _run_split(self, task: Task, output_dir: Path) -> None:
        fitz = _load_fitz()
        output_dir.mkdir(parents=True, exist_ok=True)
        mode = str(task.options.get("split_mode") or "every_n").lower()

        if mode == "size":
            await self._run_split_by_size(task, output_dir, fitz)
            return

        document = fitz.open(str(task.input_path))
        try:
            page_count = len(document)
            if page_count == 0:
                raise RuntimeError("PDF has no pages")

            chunks = _resolve_split_ranges(task.options, page_count)
            if not chunks:
                raise RuntimeError("Split produced zero output files")

            stem = Path(task.input_path).stem
            for index, (start, end) in enumerate(chunks, start=1):
                out_pdf = output_dir / f"{stem}-{index:03d}.pdf"
                chunk_doc = fitz.open()
                try:
                    chunk_doc.insert_pdf(document, from_page=start, to_page=end)
                    chunk_doc.save(str(out_pdf), garbage=3, deflate=True)
                finally:
                    _close(chunk_doc)
                task.append_log(
                    f"Wrote split {index}/{len(chunks)}: {out_pdf.name} "
                    f"(pages {start + 1}-{end + 1})"
                )
                task.progress = 0.05 + 0.9 * (index / len(chunks))
                await asyncio.sleep(0)
        finally:
            _close(document)

        task.append_log(f"Split into {len(chunks)} file(s) under {output_dir}")
        task.progress = 1.0

    async def _run_split_by_size(self, task: Task, output_dir: Path, fitz: ModuleType) -> None:
        size_mb = _float_option(task.options.get("split_size_mb"))
        if size_mb is None or size_mb <= 0:
            raise RuntimeError(
                "split_mode=size requires split_size_mb (positive number of megabytes)"
            )
        size_limit = int(size_mb * 1024 * 1024)

        document = fitz.open(str(task.input_path))
        try:
            page_count = len(document)
            if page_count == 0:
                raise RuntimeError("PDF has no pages")

            stem = Path(task.input_path).stem
            chunk_doc = fitz.open()
            chunk_start_page = 0
            chunk_pages = 0
            chunk_index = 1
            written = 0

            for page_index in range(page_count):
                chunk_doc.insert_pdf(document, from_page=page_index, to_page=page_index)
                chunk_pages += 1
                serialized = chunk_doc.tobytes(garbage=3, deflate=True)
                if len(serialized) > size_limit and chunk_pages > 1:
                    # Roll back the page that overflowed and finalize.
                    chunk_doc.delete_page(chunk_pages - 1)
                    chunk_pages -= 1
                    out_pdf = output_dir / f"{stem}-{chunk_index:03d}.pdf"
                    chunk_doc.save(str(out_pdf), garbage=3, deflate=True)
                    task.append_log(
                        f"Wrote split {chunk_index}: {out_pdf.name} "
                        f"(pages {chunk_start_page + 1}-{chunk_start_page + chunk_pages})"
                    )
                    written += 1
                    _close(chunk_doc)
                    chunk_index += 1
                    chunk_doc = fitz.open()
                    chunk_doc.insert_pdf(document, from_page=page_index, to_page=page_index)
                    chunk_start_page = page_index
                    chunk_pages = 1
                task.progress = 0.05 + 0.85 * ((page_index + 1) / page_count)
                await asyncio.sleep(0)

            if chunk_pages > 0:
                out_pdf = output_dir / f"{stem}-{chunk_index:03d}.pdf"
                chunk_doc.save(str(out_pdf), garbage=3, deflate=True)
                task.append_log(
                    f"Wrote split {chunk_index}: {out_pdf.name} "
                    f"(pages {chunk_start_page + 1}-{chunk_start_page + chunk_pages})"
                )
                written += 1
            _close(chunk_doc)
        finally:
            _close(document)

        task.append_log(
            f"Split by size {size_mb} MB into {written} file(s) under {output_dir}"
        )
        task.progress = 1.0

    async def _run_extract_images(self, task: Task, output_dir: Path) -> None:
        fitz = _load_fitz()
        output_dir.mkdir(parents=True, exist_ok=True)
        document = fitz.open(str(task.input_path))
        try:
            page_count = len(document)
            stem = Path(task.input_path).stem
            extracted = 0
            seen_xrefs: set[int] = set()
            dedupe = bool(task.options.get("extract_dedupe", True))
            for page_index in range(page_count):
                page = document.load_page(page_index)
                images = page.get_images(full=True)
                for slot, info in enumerate(images, start=1):
                    xref = info[0]
                    if dedupe and xref in seen_xrefs:
                        continue
                    seen_xrefs.add(xref)
                    image = document.extract_image(xref)
                    if not image or not image.get("image"):
                        continue
                    ext = image.get("ext") or "png"
                    extracted += 1
                    out_name = f"{stem}-page{page_index + 1:03d}-img{slot:02d}.{ext}"
                    (output_dir / out_name).write_bytes(image["image"])
                task.progress = 0.05 + 0.85 * ((page_index + 1) / max(page_count, 1))
                await asyncio.sleep(0)

            if extracted == 0:
                task.append_log("No embedded images found")
        finally:
            _close(document)

        task.append_log(f"Extracted {extracted} image(s) to {output_dir}")
        task.progress = 1.0

    async def _run_extract_attachments(self, task: Task, output_dir: Path) -> None:
        fitz = _load_fitz()
        output_dir.mkdir(parents=True, exist_ok=True)
        document = fitz.open(str(task.input_path))
        try:
            count = document.embfile_count() if hasattr(document, "embfile_count") else 0
            if count == 0:
                task.append_log("No embedded attachments found")
                task.progress = 1.0
                return

            for index in range(count):
                info = document.embfile_info(index)
                name = info.get("filename") or info.get("name") or f"attachment-{index + 1:03d}"
                payload = document.embfile_get(index)
                if payload is None:
                    continue
                safe_name = _safe_attachment_name(name)
                target = output_dir / safe_name
                if target.exists():
                    target = output_dir / f"{index + 1:03d}-{safe_name}"
                target.write_bytes(payload)
                task.append_log(f"Extracted attachment: {target.name} ({len(payload)} bytes)")
                task.progress = 0.05 + 0.85 * ((index + 1) / max(count, 1))
                await asyncio.sleep(0)
        finally:
            _close(document)

        task.append_log(f"Wrote {count} attachment(s) to {output_dir}")
        task.progress = 1.0

    async def _run_merge(self, task: Task, output_path: Path) -> None:
        fitz = _load_fitz()
        sources = list(task.inputs)
        if len(sources) < 2:
            raise RuntimeError(
                "PDF merge requires at least two input PDFs"
            )
        task.append_log(f"PDF merge: combining {len(sources)} document(s)")

        result = fitz.open()
        try:
            for index, source_path in enumerate(sources, start=1):
                chunk = fitz.open(str(source_path))
                try:
                    if chunk.needs_pass:
                        raise RuntimeError(
                            f"Cannot merge encrypted PDF: {source_path}"
                        )
                    result.insert_pdf(chunk)
                    task.append_log(
                        f"Appended {len(chunk)} page(s) from {source_path.name}"
                    )
                finally:
                    _close(chunk)
                task.progress = 0.05 + 0.85 * (index / len(sources))
                await asyncio.sleep(0)
            if len(result) == 0:
                raise RuntimeError("Merged PDF has no pages")
            result.save(str(output_path), garbage=3, deflate=True)
        finally:
            _close(result)

        task.append_log(f"Wrote merged PDF: {output_path} ({len(sources)} sources)")
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

    async def _run_pdf_to_docx(self, task: Task, output_path: Path) -> None:
        try:
            from pdf2docx import Converter
        except ImportError as exc:
            raise RuntimeError(
                "pdf2docx is required for PDF→DOCX. "
                "Install with: .venv/bin/pip install pdf2docx"
            ) from exc

        task.append_log("Converting PDF → DOCX via pdf2docx")

        def _convert() -> None:
            converter = Converter(str(task.input_path))
            try:
                converter.convert(str(output_path))
            finally:
                converter.close()

        await asyncio.to_thread(_convert)
        task.append_log(f"Wrote DOCX: {output_path}")
        task.progress = 1.0

    async def _run_pdf_to_epub(self, task: Task, output_path: Path) -> None:
        fitz = _load_fitz()
        document = fitz.open(str(task.input_path))
        try:
            page_count = len(document)
            if page_count == 0:
                raise RuntimeError("PDF has no pages")
            chapters: list[tuple[str, str]] = []
            for index in range(page_count):
                page = document.load_page(index)
                html_body = page.get_text("html") or ""
                chapters.append((f"chapter-{index + 1:04d}.xhtml", html_body))
                task.progress = 0.05 + 0.85 * ((index + 1) / page_count)
                await asyncio.sleep(0)
            metadata = document.metadata or {}
        finally:
            _close(document)

        title = str(metadata.get("title") or Path(task.input_path).stem)
        author = str(metadata.get("author") or "")
        await asyncio.to_thread(_write_epub, output_path, title, author, chapters)
        task.append_log(f"Wrote EPUB: {output_path} ({len(chapters)} page(s))")
        task.progress = 1.0

    async def _run_qpdf_linearize(self, task: Task, output_path: Path) -> None:
        command = ["qpdf", "--linearize", str(task.input_path), str(output_path)]
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
        if process.returncode not in (0, 3):
            raise RuntimeError(
                f"qpdf --linearize exited with code {process.returncode}"
            )
        task.append_log(f"Linearized PDF written to {output_path}")
        task.progress = 1.0

    async def _run_pdf_operation(self, task: Task, output_path: Path) -> None:
        operation = (task.options.get("operation") or "extract_pages").lower()
        if operation not in PDF_OPERATIONS:
            raise RuntimeError(f"Unsupported PDF operation: {operation}")

        if operation == "repair":
            await self._run_qpdf_repair(task, output_path)
            return

        if operation == "linearize":
            await self._run_qpdf_linearize(task, output_path)
            return

        if operation == "merge":
            await self._run_merge(task, output_path)
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
                "compress_images": _op_compress_images,
                "encrypt": _op_encrypt,
                "decrypt": _op_decrypt,
                "strip_metadata": _op_strip_metadata,
                "edit_metadata": _op_edit_metadata,
                "watermark_text": _op_watermark_text,
                "watermark_image": _op_watermark_image,
                "page_numbering": _op_page_numbering,
                "redact": _op_redact,
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


def _op_compress_images(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    target_dpi = _int_option(task.options.get("compress_images_target_dpi")) or 150
    if target_dpi < 36 or target_dpi > 600:
        raise RuntimeError(
            f"compress_images_target_dpi must be between 36 and 600, got {target_dpi}"
        )
    quality = _int_option(task.options.get("compress_images_quality")) or 75
    if quality < 1 or quality > 100:
        raise RuntimeError(
            f"compress_images_quality must be between 1 and 100, got {quality}"
        )

    seen_xrefs: set[int] = set()
    replaced = 0
    skipped = 0
    for page_index in range(page_count):
        page = document.load_page(page_index)
        rect = page.rect
        page_width_pt = max(rect.width, 1.0)
        page_height_pt = max(rect.height, 1.0)
        for info in page.get_images(full=True):
            xref = info[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            try:
                source = fitz.Pixmap(document, xref)
            except Exception as exc:  # pragma: no cover - defensive
                task.append_log(f"skip xref {xref}: {exc}")
                skipped += 1
                continue
            try:
                # Effective DPI = pixel dim ÷ rendered size (in inches).
                width_pt = page_width_pt
                height_pt = page_height_pt
                effective_dpi = max(
                    source.width / (width_pt / 72.0),
                    source.height / (height_pt / 72.0),
                )
                if effective_dpi <= target_dpi:
                    skipped += 1
                    continue
                ratio = target_dpi / effective_dpi
                new_w = max(1, int(source.width * ratio))
                new_h = max(1, int(source.height * ratio))
                try:
                    smaller = fitz.Pixmap(source, new_w, new_h)
                except Exception:  # pragma: no cover
                    skipped += 1
                    continue
                try:
                    if smaller.alpha:
                        new_bytes = smaller.tobytes("png")
                    else:
                        new_bytes = smaller.tobytes("jpeg", jpg_quality=quality)
                except TypeError:
                    # Older PyMuPDF: tobytes only accepts the format string.
                    new_bytes = smaller.tobytes("jpeg" if not smaller.alpha else "png")
                try:
                    document.update_stream(xref, new_bytes)
                    replaced += 1
                finally:
                    _close(smaller) if hasattr(smaller, "close") else None
            finally:
                _close(source) if hasattr(source, "close") else None
        task.progress = 0.05 + 0.85 * ((page_index + 1) / max(page_count, 1))

    task.append_log(
        f"Image downsample: replaced {replaced} stream(s), skipped {skipped}; "
        f"target {target_dpi} DPI, JPEG q={quality}"
    )


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


def _op_watermark_image(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    image_path = task.options.get("watermark_image_path")
    if not image_path:
        raise RuntimeError("watermark_image_path option is required")
    image_path = Path(str(image_path))
    if not image_path.exists():
        raise RuntimeError(f"Watermark image not found: {image_path}")

    gravity = str(task.options.get("watermark_position") or "center").lower()
    fraction = GRAVITY_TO_FRACTION.get(gravity, GRAVITY_TO_FRACTION["center"])
    width_fraction = _float_option(task.options.get("watermark_image_width_fraction"))
    if width_fraction is None or width_fraction <= 0:
        width_fraction = 0.25
    width_fraction = max(0.01, min(1.0, width_fraction))

    opacity = _int_option(task.options.get("watermark_opacity"))
    if opacity is None:
        opacity = 35
    overlay = max(0.0, min(1.0, opacity / 100.0))

    pixmap = fitz.Pixmap(str(image_path))
    aspect = pixmap.height / pixmap.width if pixmap.width else 1.0

    for index in range(page_count):
        page = document.load_page(index)
        rect = page.rect
        target_width = rect.width * width_fraction
        target_height = target_width * aspect
        anchor_x = rect.x0 + rect.width * fraction[0]
        anchor_y = rect.y0 + rect.height * fraction[1]
        x0 = anchor_x - target_width / 2
        y0 = anchor_y - target_height / 2
        target = fitz.Rect(x0, y0, x0 + target_width, y0 + target_height)
        page.insert_image(target, filename=str(image_path), overlay=True)
        # PyMuPDF lacks a per-image alpha argument on insert_image in older
        # versions; emulate translucency by drawing a soft fill rectangle.
        if overlay < 0.999:
            page.draw_rect(target, color=None, fill=(1, 1, 1), fill_opacity=1 - overlay, overlay=True)

    task.append_log(
        f"Watermarked {page_count} page(s) with image {image_path.name} "
        f"(width {width_fraction:.0%}, opacity {opacity}%, gravity {gravity})"
    )


def _op_page_numbering(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    template = str(task.options.get("page_number_format") or "Page {n} of {total}")
    gravity = str(task.options.get("page_number_position") or "south").lower()
    fraction = GRAVITY_TO_FRACTION.get(gravity, GRAVITY_TO_FRACTION["south"])
    fontsize = _int_option(task.options.get("page_number_size")) or 14
    start = _int_option(task.options.get("page_number_start")) or 1
    skip = _int_option(task.options.get("page_number_skip")) or 0
    color = (0, 0, 0)
    opacity = _int_option(task.options.get("page_number_opacity"))
    if opacity is None:
        opacity = 100
    fill_opacity = max(0.0, min(1.0, opacity / 100.0))

    numbered = 0
    total = max(0, page_count - skip)
    for index in range(skip, page_count):
        page = document.load_page(index)
        n = start + (index - skip)
        try:
            label = template.format(n=n, total=total, page=n)
        except (KeyError, IndexError):
            label = f"{n}"
        rect = page.rect
        x = rect.x0 + rect.width * fraction[0]
        y = rect.y0 + rect.height * fraction[1]
        # Crude horizontal centering for the standard gravities by shifting back
        # half the approximate text width (avg glyph width ~ fontsize * 0.5).
        approx_text_width = len(label) * fontsize * 0.5
        if gravity in {"north", "center", "south"}:
            x -= approx_text_width / 2
        elif gravity in {"northeast", "east", "southeast"}:
            x -= approx_text_width
        page.insert_text(
            (x, y),
            label,
            fontsize=fontsize,
            color=color,
            fill_opacity=fill_opacity,
        )
        numbered += 1

    task.append_log(
        f"Numbered {numbered} page(s) with format '{template}' "
        f"(start={start}, skip={skip}, gravity={gravity})"
    )


def _op_redact(document, fitz: ModuleType, task: Task, page_count: int) -> None:
    raw_terms = task.options.get("redact_terms")
    if isinstance(raw_terms, (list, tuple)):
        terms = [str(t).strip() for t in raw_terms if str(t).strip()]
    else:
        terms = [t.strip() for t in str(raw_terms or "").split(",") if t.strip()]
    if not terms:
        raise RuntimeError(
            "Redaction requires redact_terms (comma-separated text to black out)"
        )

    fill_color = _parse_color(
        task.options.get("redact_color"), default=(0.0, 0.0, 0.0)
    )
    pages_filter = _parse_page_range(task.options.get("pages"), page_count)
    target_pages = pages_filter or list(range(page_count))

    total_marks = 0
    for index in target_pages:
        page = document.load_page(index)
        marks = 0
        for term in terms:
            for rect in page.search_for(term):
                page.add_redact_annot(rect, fill=fill_color)
                marks += 1
        if marks:
            page.apply_redactions()
            total_marks += marks

    if total_marks == 0:
        raise RuntimeError(
            f"No redactable matches found for terms: {', '.join(terms)}"
        )
    task.append_log(
        f"Redacted {total_marks} match(es) of {len(terms)} term(s) "
        f"across {len(target_pages)} page(s)"
    )


def _parse_color(value: object, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if value is None or value == "":
        return default
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return (float(value[0]), float(value[1]), float(value[2]))
    text = str(value).strip().lower()
    presets = {
        "black": (0.0, 0.0, 0.0),
        "white": (1.0, 1.0, 1.0),
        "red": (1.0, 0.0, 0.0),
        "yellow": (1.0, 1.0, 0.0),
    }
    if text in presets:
        return presets[text]
    if text.startswith("#") and len(text) == 7:
        try:
            r = int(text[1:3], 16) / 255.0
            g = int(text[3:5], 16) / 255.0
            b = int(text[5:7], 16) / 255.0
            return (r, g, b)
        except ValueError:
            return default
    return default


def _write_epub(
    output_path: Path,
    title: str,
    author: str,
    chapters: list[tuple[str, str]],
) -> None:
    """Build a minimal EPUB 2 archive at ``output_path``.

    Each chapter is a (filename, html_body) pair. The HTML body is wrapped
    in a minimal XHTML scaffold; PyMuPDF's html output already contains
    an inline <body> but we wrap defensively.
    """
    import uuid
    import xml.sax.saxutils as saxutils
    import zipfile

    if not chapters:
        raise RuntimeError("EPUB requires at least one chapter")

    book_id = f"urn:uuid:{uuid.uuid4()}"
    safe_title = saxutils.escape(title or "Untitled")
    safe_author = saxutils.escape(author or "Unknown")

    container_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        '  <rootfiles>\n'
        '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
        '  </rootfiles>\n'
        '</container>\n'
    )

    manifest_items = "\n".join(
        f'    <item id="ch{i+1}" href="{name}" media-type="application/xhtml+xml"/>'
        for i, (name, _) in enumerate(chapters)
    )
    spine_items = "\n".join(
        f'    <itemref idref="ch{i+1}"/>'
        for i in range(len(chapters))
    )
    content_opf = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="bookid">\n'
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'    <dc:identifier id="bookid">{book_id}</dc:identifier>\n'
        f'    <dc:title>{safe_title}</dc:title>\n'
        f'    <dc:creator>{safe_author}</dc:creator>\n'
        '    <dc:language>en</dc:language>\n'
        '  </metadata>\n'
        '  <manifest>\n'
        '    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>\n'
        f'{manifest_items}\n'
        '  </manifest>\n'
        '  <spine toc="ncx">\n'
        f'{spine_items}\n'
        '  </spine>\n'
        '</package>\n'
    )

    nav_points = "\n".join(
        f'    <navPoint id="np{i+1}" playOrder="{i+1}">\n'
        f'      <navLabel><text>Page {i+1}</text></navLabel>\n'
        f'      <content src="{name}"/>\n'
        f'    </navPoint>'
        for i, (name, _) in enumerate(chapters)
    )
    toc_ncx = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
        '  <head>\n'
        f'    <meta name="dtb:uid" content="{book_id}"/>\n'
        '    <meta name="dtb:depth" content="1"/>\n'
        '  </head>\n'
        f'  <docTitle><text>{safe_title}</text></docTitle>\n'
        '  <navMap>\n'
        f'{nav_points}\n'
        '  </navMap>\n'
        '</ncx>\n'
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w") as epub:
        # Mimetype must be the FIRST entry and stored uncompressed.
        epub.writestr(
            zipfile.ZipInfo("mimetype"),
            "application/epub+zip",
            compress_type=zipfile.ZIP_STORED,
        )
        epub.writestr("META-INF/container.xml", container_xml, zipfile.ZIP_DEFLATED)
        epub.writestr("OEBPS/content.opf", content_opf, zipfile.ZIP_DEFLATED)
        epub.writestr("OEBPS/toc.ncx", toc_ncx, zipfile.ZIP_DEFLATED)
        for index, (name, body) in enumerate(chapters, start=1):
            chapter_xhtml = _wrap_xhtml(f"Page {index}", body)
            epub.writestr(f"OEBPS/{name}", chapter_xhtml, zipfile.ZIP_DEFLATED)


def _wrap_xhtml(title: str, body_html: str) -> str:
    """Wrap a fragment of HTML as an XHTML chapter document."""
    import xml.sax.saxutils as saxutils

    # PyMuPDF emits a full <html>...<body>...</body></html> document. Strip
    # the outer tags if present so we can re-wrap with our XHTML scaffold.
    stripped = body_html.strip()
    if "<body" in stripped.lower():
        start = stripped.lower().find("<body")
        gt = stripped.find(">", start)
        end = stripped.lower().rfind("</body>")
        if gt != -1 and end != -1:
            stripped = stripped[gt + 1:end].strip()

    safe_title = saxutils.escape(title)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" '
        '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
        '<html xmlns="http://www.w3.org/1999/xhtml">\n'
        f'<head><title>{safe_title}</title></head>\n'
        f'<body>\n{stripped}\n</body>\n'
        '</html>\n'
    )


def _safe_attachment_name(name: str) -> str:
    text = str(name).strip().replace("/", "_").replace("\\", "_")
    text = text.lstrip(".")
    return text or "attachment"


def _save_kwargs_for(operation: str, fitz: ModuleType, task: Task) -> dict:
    if operation in ("compress", "compress_images"):
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


def _float_option(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
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


def _resolve_split_ranges(options: dict, page_count: int) -> list[tuple[int, int]]:
    mode = str(options.get("split_mode") or "every_n").lower()

    if mode == "every_n":
        per_file = _int_option(options.get("split_pages_per_file")) or 1
        if per_file < 1:
            raise RuntimeError("split_pages_per_file must be >= 1")
        return [
            (start, min(start + per_file - 1, page_count - 1))
            for start in range(0, page_count, per_file)
        ]

    if mode == "range":
        raw = options.get("split_ranges")
        if raw in (None, ""):
            raise RuntimeError("split_mode=range requires split_ranges (e.g. '1-5,6-10')")
        ranges: list[tuple[int, int]] = []
        for token in str(raw).split(","):
            token = token.strip()
            if not token:
                continue
            indices = _parse_page_range(token, page_count)
            if not indices:
                continue
            ranges.append((indices[0], indices[-1]))
        if not ranges:
            raise RuntimeError(f"No usable ranges in split_ranges: {raw}")
        return ranges

    raise RuntimeError(f"Unsupported split_mode: {mode}")


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
