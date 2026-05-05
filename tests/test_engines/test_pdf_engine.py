from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.task import Task
from app.engines.pdf_engine import PDFEngine


class FakePixmap:
    def __init__(self, store: list[str]) -> None:
        self._store = store

    def save(self, path: str) -> None:
        self._store.append(path)
        Path(path).write_text("image", encoding="utf-8")


class FakeRect:
    x0 = 0.0
    y0 = 0.0
    width = 100.0
    height = 200.0


class FakePage:
    def __init__(self, page_number: int, *, pixmap_store: list[str] | None = None) -> None:
        self.page_number = page_number
        self.rotation = 0
        self.rect = FakeRect()
        self._pixmap_store = pixmap_store
        self.text_calls: list[dict] = []

    def get_pixmap(self, dpi: int, alpha: bool):
        return FakePixmap(self._pixmap_store if self._pixmap_store is not None else [])

    def set_rotation(self, value: int) -> None:
        self.rotation = value

    def get_text(self) -> str:
        return f"page {self.page_number}"

    def insert_text(self, point, text, **kwargs) -> None:
        self.text_calls.append({"point": point, "text": text, **kwargs})


class FakeDocument:
    def __init__(self, page_count: int = 3, *, needs_pass: bool = False) -> None:
        self._pages = [FakePage(i) for i in range(page_count)]
        self.needs_pass = needs_pass
        self.selected_pages: list[int] | None = None
        self.metadata_calls: list[dict] = []
        self.save_calls: list[tuple[str, dict]] = []
        self.authenticated_with: str | None = None

    def __len__(self) -> int:
        return len(self._pages)

    def load_page(self, page_number: int):
        return self._pages[page_number]

    def authenticate(self, password: str) -> bool:
        self.authenticated_with = password
        return password == "right"

    def select(self, pages: list[int]) -> None:
        self.selected_pages = list(pages)
        self._pages = [self._pages[index] for index in pages]

    def set_metadata(self, metadata: dict) -> None:
        self.metadata_calls.append(dict(metadata))

    def save(self, path: str, **kwargs) -> None:
        self.save_calls.append((path, dict(kwargs)))
        Path(path).write_text("pdf", encoding="utf-8")

    def close(self) -> None:
        return


def _install_fake_fitz(monkeypatch, document: FakeDocument) -> SimpleNamespace:
    fake_fitz = SimpleNamespace(
        open=lambda _path: document,
        PDF_ENCRYPT_AES_256=4,
        PDF_ENCRYPT_NONE=0,
    )
    monkeypatch.setitem(__import__("sys").modules, "fitz", fake_fitz)
    return fake_fitz


def _pdf_task(tmp_path: Path, options: dict) -> Task:
    return Task(
        input_path=tmp_path / "in.pdf",
        output_path=tmp_path / "out.pdf",
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        options=options,
    )


@pytest.mark.asyncio
async def test_pdf_engine_renders_all_pages_with_numbered_outputs(tmp_path, monkeypatch) -> None:
    saved_paths: list[str] = []

    class RenderPage:
        def get_pixmap(self, dpi: int, alpha: bool):
            assert dpi == 240
            assert alpha is False
            return FakePixmap(saved_paths)

    class RenderDocument:
        def __len__(self) -> int:
            return 2

        def load_page(self, page_number: int):
            return RenderPage()

        def close(self) -> None:
            return

    fake_fitz = SimpleNamespace(open=lambda _path: RenderDocument())
    monkeypatch.setitem(__import__("sys").modules, "fitz", fake_fitz)

    task = Task(
        input_path=tmp_path / "scan.pdf",
        output_path=tmp_path / "pages" / "scan.png",
        format_in="pdf",
        format_out="png",
        engine="pdf",
        options={"dpi": 240},
    )

    await PDFEngine().convert(task)

    assert task.progress == 1.0
    assert saved_paths == [
        str(tmp_path / "pages" / "scan-001.png"),
        str(tmp_path / "pages" / "scan-002.png"),
    ]
    assert any("Rendered page 1" in line for line in task.log)


def test_pdf_engine_supports_pdf_to_image_formats() -> None:
    engine = PDFEngine()

    assert engine.supports("pdf", "png")
    assert engine.supports("pdf", "jpg")
    assert engine.supports("pdf", "jpeg")
    assert engine.supports("pdf", "pdf")
    assert engine.supports("pdf", "txt")
    assert not engine.supports("png", "pdf")


@pytest.mark.asyncio
async def test_extract_text_writes_concatenated_pages(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=3)
    _install_fake_fitz(monkeypatch, document)

    task = Task(
        input_path=tmp_path / "doc.pdf",
        output_path=tmp_path / "doc.txt",
        format_in="pdf",
        format_out="txt",
        engine="pdf",
        options={},
    )

    await PDFEngine().convert(task)

    output = (tmp_path / "doc.txt").read_text(encoding="utf-8")
    assert output == "page 0\npage 1\npage 2"
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_extract_pages_selects_parsed_range(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=10)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "extract_pages", "pages": "1-3,5,8-9"})

    await PDFEngine().convert(task)

    assert document.selected_pages == [0, 1, 2, 4, 7, 8]
    assert document.save_calls
    saved_path, kwargs = document.save_calls[0]
    assert saved_path == str(tmp_path / "out.pdf")
    assert kwargs == {"garbage": 3, "deflate": True}


@pytest.mark.asyncio
async def test_extract_pages_requires_selection(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=3)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "extract_pages", "pages": ""})

    with pytest.raises(RuntimeError, match="No pages selected"):
        await PDFEngine().convert(task)


@pytest.mark.asyncio
async def test_extract_pages_rejects_out_of_range(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=3)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "extract_pages", "pages": "1-5"})

    with pytest.raises(RuntimeError, match="outside document"):
        await PDFEngine().convert(task)


@pytest.mark.asyncio
async def test_rotate_applies_to_specified_pages(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=4)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(
        tmp_path,
        {"operation": "rotate", "pages": "2-3", "rotation_degrees": 270},
    )

    await PDFEngine().convert(task)

    assert document._pages[0].rotation == 0
    assert document._pages[1].rotation == 270
    assert document._pages[2].rotation == 270
    assert document._pages[3].rotation == 0


@pytest.mark.asyncio
async def test_rotate_defaults_to_all_pages_when_no_range(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=3)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "rotate"})

    await PDFEngine().convert(task)

    assert [page.rotation for page in document._pages] == [90, 90, 90]


@pytest.mark.asyncio
async def test_compress_uses_garbage_and_deflate_save_kwargs(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=2)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "compress"})

    await PDFEngine().convert(task)

    _, kwargs = document.save_calls[0]
    assert kwargs == {"garbage": 4, "deflate": True, "clean": True}


@pytest.mark.asyncio
async def test_encrypt_emits_aes_save_kwargs(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=1)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(
        tmp_path,
        {
            "operation": "encrypt",
            "password_user": "open-me",
            "password_owner": "edit-me",
        },
    )

    await PDFEngine().convert(task)

    _, kwargs = document.save_calls[0]
    assert kwargs["encryption"] == 4
    assert kwargs["user_pw"] == "open-me"
    assert kwargs["owner_pw"] == "edit-me"
    assert kwargs["permissions"] == -1


@pytest.mark.asyncio
async def test_encrypt_requires_a_password(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=1)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "encrypt"})

    with pytest.raises(RuntimeError, match="password_user or password_owner"):
        await PDFEngine().convert(task)


@pytest.mark.asyncio
async def test_decrypt_authenticates_then_writes_unencrypted(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=2, needs_pass=True)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "decrypt", "password_user": "right"})

    await PDFEngine().convert(task)

    assert document.authenticated_with == "right"
    _, kwargs = document.save_calls[0]
    assert kwargs == {"encryption": 0, "garbage": 3, "deflate": True}


@pytest.mark.asyncio
async def test_encrypted_pdf_without_password_raises(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=1, needs_pass=True)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "compress"})

    with pytest.raises(RuntimeError, match="encrypted; provide password"):
        await PDFEngine().convert(task)


@pytest.mark.asyncio
async def test_encrypted_pdf_rejects_wrong_password(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=1, needs_pass=True)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(
        tmp_path,
        {"operation": "compress", "password": "wrong"},
    )

    with pytest.raises(RuntimeError, match="Invalid password"):
        await PDFEngine().convert(task)


@pytest.mark.asyncio
async def test_strip_metadata_clears_document_metadata(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=1)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "strip_metadata"})

    await PDFEngine().convert(task)

    assert document.metadata_calls == [{}]


@pytest.mark.asyncio
async def test_watermark_text_inserts_text_on_every_page(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=2)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(
        tmp_path,
        {
            "operation": "watermark_text",
            "watermark_text": "DRAFT",
            "watermark_position": "southeast",
            "watermark_size": 60,
            "watermark_opacity": 50,
        },
    )

    await PDFEngine().convert(task)

    for page in document._pages:
        assert len(page.text_calls) == 1
        call = page.text_calls[0]
        assert call["text"] == "DRAFT"
        assert call["fontsize"] == 60
        assert call["fill_opacity"] == pytest.approx(0.5)
        # gravity southeast => x ≈ 95% width, y ≈ 95% height
        assert call["point"] == pytest.approx((95.0, 190.0))


@pytest.mark.asyncio
async def test_watermark_text_requires_text(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=1)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "watermark_text"})

    with pytest.raises(RuntimeError, match="watermark_text option is required"):
        await PDFEngine().convert(task)


@pytest.mark.asyncio
async def test_unknown_operation_raises(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=1)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "frobnicate"})

    with pytest.raises(RuntimeError, match="Unsupported PDF operation"):
        await PDFEngine().convert(task)


@pytest.mark.asyncio
async def test_reorder_passes_explicit_order_to_select(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=4)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "reorder", "pages": "3,1,2,4"})

    await PDFEngine().convert(task)

    # 1-based input "3,1,2,4" maps to 0-based [2, 0, 1, 3]
    assert document.selected_pages == [2, 0, 1, 3]


@pytest.mark.asyncio
async def test_reorder_requires_pages(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=3)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "reorder"})

    with pytest.raises(RuntimeError, match="Reorder requires"):
        await PDFEngine().convert(task)


@pytest.mark.asyncio
async def test_edit_metadata_writes_only_provided_fields(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=1)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(
        tmp_path,
        {
            "operation": "edit_metadata",
            "meta_title": "My PDF",
            "meta_author": "Sarta",
            "meta_keywords": "trex, converter",
        },
    )

    await PDFEngine().convert(task)

    assert document.metadata_calls == [
        {"title": "My PDF", "author": "Sarta", "keywords": "trex, converter"}
    ]


@pytest.mark.asyncio
async def test_edit_metadata_requires_at_least_one_field(tmp_path, monkeypatch) -> None:
    document = FakeDocument(page_count=1)
    _install_fake_fitz(monkeypatch, document)

    task = _pdf_task(tmp_path, {"operation": "edit_metadata"})

    with pytest.raises(RuntimeError, match="at least one metadata field"):
        await PDFEngine().convert(task)


@pytest.mark.asyncio
async def test_extract_html_writes_html_document(tmp_path, monkeypatch) -> None:
    class HtmlPage:
        def __init__(self, index: int) -> None:
            self._index = index

        def get_text(self, kind: str = "") -> str:
            assert kind == "html"
            return f"<p>page {self._index + 1}</p>"

    class HtmlDocument:
        def __init__(self) -> None:
            self._pages = [HtmlPage(i) for i in range(2)]

        def __len__(self) -> int:
            return 2

        def load_page(self, index: int):
            return self._pages[index]

        def close(self) -> None:
            return

    fake_fitz = SimpleNamespace(
        open=lambda _path: HtmlDocument(),
        PDF_ENCRYPT_AES_256=4,
        PDF_ENCRYPT_NONE=0,
    )
    monkeypatch.setitem(__import__("sys").modules, "fitz", fake_fitz)

    task = Task(
        input_path=tmp_path / "doc.pdf",
        output_path=tmp_path / "doc.html",
        format_in="pdf",
        format_out="html",
        engine="pdf",
        options={},
    )

    await PDFEngine().convert(task)

    output = (tmp_path / "doc.html").read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in output
    assert '<title>doc</title>' in output
    assert '<section class="pdf-page" data-page="1">' in output
    assert "<p>page 1</p>" in output
    assert "<p>page 2</p>" in output
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_repair_runs_qpdf_subprocess(tmp_path, monkeypatch) -> None:
    fake_qpdf = tmp_path / "qpdf"
    fake_qpdf.write_text(
        "#!/bin/sh\n"
        "input=\"$1\"\n"
        "output=\"$2\"\n"
        "printf 'repaired-pdf' > \"$output\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_qpdf.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    input_path = tmp_path / "broken.pdf"
    input_path.write_bytes(b"%PDF-1.4 fake")
    output_path = tmp_path / "fixed.pdf"

    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        options={"operation": "repair"},
    )

    await PDFEngine().convert(task)

    assert output_path.read_text(encoding="utf-8") == "repaired-pdf"
    assert task.progress == 1.0
    assert any("Running: qpdf" in line for line in task.log)


@pytest.mark.asyncio
async def test_repair_treats_qpdf_warning_exit_as_success(tmp_path, monkeypatch) -> None:
    fake_qpdf = tmp_path / "qpdf"
    fake_qpdf.write_text(
        "#!/bin/sh\n"
        "output=\"$2\"\n"
        "printf 'repaired-with-warnings' > \"$output\"\n"
        "echo 'WARNING: minor issue' >&2\n"
        "exit 3\n",
        encoding="utf-8",
    )
    fake_qpdf.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    input_path = tmp_path / "broken.pdf"
    input_path.write_bytes(b"%PDF-1.4 fake")
    output_path = tmp_path / "fixed.pdf"

    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        options={"operation": "repair"},
    )

    await PDFEngine().convert(task)

    assert output_path.read_text(encoding="utf-8") == "repaired-with-warnings"


@pytest.mark.asyncio
async def test_repair_raises_on_qpdf_error(tmp_path, monkeypatch) -> None:
    fake_qpdf = tmp_path / "qpdf"
    fake_qpdf.write_text(
        "#!/bin/sh\n"
        "echo 'fatal' >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    fake_qpdf.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    input_path = tmp_path / "broken.pdf"
    input_path.write_bytes(b"%PDF-1.4")
    output_path = tmp_path / "fixed.pdf"

    task = Task(
        input_path=input_path,
        output_path=output_path,
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        options={"operation": "repair"},
    )

    with pytest.raises(RuntimeError, match="qpdf exited with code 2"):
        await PDFEngine().convert(task)


def test_pdf_engine_supports_html_output() -> None:
    engine = PDFEngine()

    assert engine.supports("pdf", "html")


def _write_pdf(path: Path, fitz, marker: str, page_count: int = 1) -> None:
    document = fitz.open()
    for index in range(page_count):
        page = document.new_page(width=200, height=200)
        page.insert_text((50, 100), f"{marker}-{index + 1}")
    document.save(str(path))
    document.close()


@pytest.mark.asyncio
async def test_merge_concatenates_two_pdfs(tmp_path) -> None:
    fitz = pytest.importorskip("fitz")
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    _write_pdf(a, fitz, "A", page_count=2)
    _write_pdf(b, fitz, "B", page_count=3)
    output = tmp_path / "merged.pdf"

    task = Task(
        input_path=a,
        output_path=output,
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        options={"operation": "merge"},
        extra_inputs=[b],
    )

    await PDFEngine().convert(task)

    merged = fitz.open(str(output))
    try:
        assert len(merged) == 5
        assert "A-1" in merged.load_page(0).get_text()
        assert "B-1" in merged.load_page(2).get_text()
        assert "B-3" in merged.load_page(4).get_text()
    finally:
        merged.close()
    assert task.progress == 1.0


@pytest.mark.asyncio
async def test_merge_preserves_input_order(tmp_path) -> None:
    fitz = pytest.importorskip("fitz")
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    third = tmp_path / "third.pdf"
    _write_pdf(first, fitz, "FIRST")
    _write_pdf(second, fitz, "SECOND")
    _write_pdf(third, fitz, "THIRD")
    output = tmp_path / "out.pdf"

    task = Task(
        input_path=second,  # primary on purpose to verify ordering follows task.inputs
        output_path=output,
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        options={"operation": "merge"},
        extra_inputs=[first, third],
    )

    await PDFEngine().convert(task)

    merged = fitz.open(str(output))
    try:
        # Order matches task.inputs: primary first, then extras in given order.
        assert "SECOND" in merged.load_page(0).get_text()
        assert "FIRST" in merged.load_page(1).get_text()
        assert "THIRD" in merged.load_page(2).get_text()
    finally:
        merged.close()


@pytest.mark.asyncio
async def test_merge_requires_at_least_two_inputs(tmp_path) -> None:
    fitz = pytest.importorskip("fitz")
    only = tmp_path / "only.pdf"
    _write_pdf(only, fitz, "ONLY")

    task = Task(
        input_path=only,
        output_path=tmp_path / "out.pdf",
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        options={"operation": "merge"},
    )

    with pytest.raises(RuntimeError, match="at least two"):
        await PDFEngine().convert(task)


@pytest.mark.asyncio
async def test_merge_rejects_encrypted_input(tmp_path) -> None:
    fitz = pytest.importorskip("fitz")
    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    _write_pdf(a, fitz, "A")
    # Build an encrypted PDF
    document = fitz.open()
    document.new_page(width=100, height=100)
    document.save(
        str(b),
        encryption=getattr(fitz, "PDF_ENCRYPT_AES_256", 4),
        owner_pw="o",
        user_pw="u",
        permissions=-1,
    )
    document.close()

    task = Task(
        input_path=a,
        output_path=tmp_path / "out.pdf",
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        options={"operation": "merge"},
        extra_inputs=[b],
    )

    with pytest.raises(RuntimeError, match="encrypted"):
        await PDFEngine().convert(task)


# ---- PDF split ----


@pytest.mark.asyncio
async def test_split_every_n_writes_files_into_directory(tmp_path) -> None:
    fitz = pytest.importorskip("fitz")
    src = tmp_path / "src.pdf"
    document = fitz.open()
    for index in range(7):
        page = document.new_page(width=200, height=200)
        page.insert_text((50, 100), f"P{index + 1}")
    document.save(str(src))
    document.close()

    out_dir = tmp_path / "out"

    task = Task(
        input_path=src,
        output_path=out_dir,
        format_in="pdf",
        format_out="folder",
        engine="pdf",
        options={"split_mode": "every_n", "split_pages_per_file": 3},
    )

    await PDFEngine().convert(task)

    files = sorted(out_dir.glob("*.pdf"))
    assert [f.name for f in files] == ["src-001.pdf", "src-002.pdf", "src-003.pdf"]
    # 7 pages / 3 per file -> 3 files: 3 + 3 + 1
    sizes = [len(fitz.open(str(f))) for f in files]
    assert sizes == [3, 3, 1]


@pytest.mark.asyncio
async def test_split_custom_ranges(tmp_path) -> None:
    fitz = pytest.importorskip("fitz")
    src = tmp_path / "src.pdf"
    document = fitz.open()
    for index in range(10):
        document.new_page(width=200, height=200)
    document.save(str(src))
    document.close()

    out_dir = tmp_path / "out"

    task = Task(
        input_path=src,
        output_path=out_dir,
        format_in="pdf",
        format_out="folder",
        engine="pdf",
        options={"split_mode": "range", "split_ranges": "1-3, 4-6, 7-10"},
    )

    await PDFEngine().convert(task)

    files = sorted(out_dir.glob("*.pdf"))
    assert len(files) == 3
    assert [len(fitz.open(str(f))) for f in files] == [3, 3, 4]


@pytest.mark.asyncio
async def test_split_range_mode_requires_ranges(tmp_path) -> None:
    fitz = pytest.importorskip("fitz")
    src = tmp_path / "src.pdf"
    document = fitz.open()
    document.new_page(width=200, height=200)
    document.save(str(src))
    document.close()

    task = Task(
        input_path=src,
        output_path=tmp_path / "out",
        format_in="pdf",
        format_out="folder",
        engine="pdf",
        options={"split_mode": "range"},
    )

    with pytest.raises(RuntimeError, match="split_ranges"):
        await PDFEngine().convert(task)


@pytest.mark.asyncio
async def test_split_unknown_mode_raises(tmp_path) -> None:
    fitz = pytest.importorskip("fitz")
    src = tmp_path / "src.pdf"
    document = fitz.open()
    document.new_page(width=200, height=200)
    document.save(str(src))
    document.close()

    task = Task(
        input_path=src,
        output_path=tmp_path / "out",
        format_in="pdf",
        format_out="folder",
        engine="pdf",
        options={"split_mode": "every_other_blue_moon"},
    )

    with pytest.raises(RuntimeError, match="Unsupported split_mode"):
        await PDFEngine().convert(task)


def test_pdf_engine_supports_pdf_to_folder() -> None:
    assert PDFEngine().supports("pdf", "folder")


# ---- PDF watermark image ----


@pytest.mark.asyncio
async def test_watermark_image_inserts_image_on_each_page(tmp_path) -> None:
    fitz = pytest.importorskip("fitz")
    src = tmp_path / "src.pdf"
    document = fitz.open()
    for _ in range(2):
        document.new_page(width=400, height=400)
    document.save(str(src))
    document.close()

    # Create a 1x1 PNG via fitz Pixmap + save
    image_path = tmp_path / "logo.png"
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 50, 50), 0)
    pixmap.clear_with(0)
    pixmap.save(str(image_path))

    output = tmp_path / "out.pdf"

    task = Task(
        input_path=src,
        output_path=output,
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        options={
            "operation": "watermark_image",
            "watermark_image_path": str(image_path),
            "watermark_position": "southeast",
            "watermark_image_width_fraction": 0.2,
            "watermark_opacity": 50,
        },
    )

    await PDFEngine().convert(task)

    result = fitz.open(str(output))
    try:
        # Each page gets one inserted image (XObject)
        for page in result:
            xrefs = page.get_images(full=True)
            assert len(xrefs) >= 1
    finally:
        result.close()


@pytest.mark.asyncio
async def test_watermark_image_requires_path(tmp_path) -> None:
    fitz = pytest.importorskip("fitz")
    src = tmp_path / "src.pdf"
    document = fitz.open()
    document.new_page(width=200, height=200)
    document.save(str(src))
    document.close()

    task = Task(
        input_path=src,
        output_path=tmp_path / "out.pdf",
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        options={"operation": "watermark_image"},
    )

    with pytest.raises(RuntimeError, match="watermark_image_path"):
        await PDFEngine().convert(task)


@pytest.mark.asyncio
async def test_watermark_image_path_must_exist(tmp_path) -> None:
    fitz = pytest.importorskip("fitz")
    src = tmp_path / "src.pdf"
    document = fitz.open()
    document.new_page(width=200, height=200)
    document.save(str(src))
    document.close()

    task = Task(
        input_path=src,
        output_path=tmp_path / "out.pdf",
        format_in="pdf",
        format_out="pdf",
        engine="pdf",
        options={
            "operation": "watermark_image",
            "watermark_image_path": str(tmp_path / "nonexistent.png"),
        },
    )

    with pytest.raises(RuntimeError, match="not found"):
        await PDFEngine().convert(task)
