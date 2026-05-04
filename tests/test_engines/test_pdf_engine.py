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
