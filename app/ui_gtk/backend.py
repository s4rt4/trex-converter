"""Bridge between the GTK4 UI and the asyncio task backend.

Two responsibilities:

* :func:`build_task` — turn a page's collected options plus its input(s)
  and output target into a :class:`~app.core.task.Task`, resolving the
  output path exactly like the old Qt ``ConversionPage`` did (per-kind
  directory-in / directory-out / output-folder rules) and tagging the
  task with the engine the queue should run it on.

* :class:`QueueController` — own the :class:`~app.core.queue.TaskQueue`,
  which lives on an asyncio event loop in a dedicated daemon thread. The
  GTK side calls thread-safe ``submit`` / ``cancel`` / ``retry``; task
  events from the loop are marshalled back onto the GTK main loop with
  ``GLib.idle_add`` so widgets are only ever touched on the UI thread.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from gi.repository import GLib

from app.core.runner import create_default_queue
from app.core.task import Task


@dataclass(frozen=True, slots=True)
class KindBackend:
    engine: str
    default_output: str
    directory_output: bool = False
    directory_input: bool = False


# Per-kind backend metadata, mirroring PAGE_CONFIGS in app.ui.main_window
# (which can't be imported here — it pulls in PySide6). engine == the
# engine_name the TaskQueue resolves via registry.engine_by_name.
KIND_CONFIG: dict[str, KindBackend] = {
    "image": KindBackend("imagemagick", "webp"),
    "video": KindBackend("ffmpeg", "mp4"),
    "audio": KindBackend("ffmpeg", "mp3"),
    "document": KindBackend("libreoffice", "pdf"),
    "subtitle": KindBackend("subtitle", "vtt"),
    "ocr": KindBackend("tesseract", "txt"),
    "pdf": KindBackend("pdf", "pdf"),
    "pdf-merge": KindBackend("pdf", "pdf"),
    "pdf-split": KindBackend("pdf", "folder", directory_output=True),
    "pdf-numbering": KindBackend("pdf", "pdf"),
    "pdf-extract-images": KindBackend("pdf", "folder", directory_output=True),
    "pdf-extract-attachments": KindBackend("pdf", "folder", directory_output=True),
    "slides-to-images": KindBackend("libreoffice", "folder", directory_output=True),
    "document-merge": KindBackend("libreoffice", "pdf"),
    "video-concat": KindBackend("ffmpeg", "mp4"),
    "audio-mix": KindBackend("ffmpeg", "mp3"),
    "image-montage": KindBackend("imagemagick", "png"),
    "subtitle-merge": KindBackend("subtitle", "srt"),
    "archive": KindBackend("archive", "folder", directory_output=True),
    "archive-compress": KindBackend("archive", "zip", directory_input=True),
    "qr": KindBackend("qr", "png"),
    "svg": KindBackend("inkscape", "png"),
    "subtitle-extract": KindBackend("ffmpeg", "srt"),
    "pdf-compare": KindBackend("pdf", "folder", directory_output=True),
    "ebook": KindBackend("pandoc", "epub"),
    "metadata": KindBackend("exiftool", "jpg"),
}


def build_task(
    kind: str,
    primary: Path,
    *,
    extra_inputs: Sequence[Path] = (),
    output_dir: Path | None = None,
    format_out: str | None = None,
    options: dict | None = None,
) -> Task:
    """Build a queue :class:`Task` for ``kind`` from a page's selections."""
    cfg = KIND_CONFIG[kind]
    fmt = (format_out or cfg.default_output).lower().lstrip(".")
    out_dir = str(output_dir) if output_dir else ""

    if cfg.directory_output:
        base = Path(out_dir) if out_dir else primary.parent
        target = base / primary.stem
    elif cfg.directory_input:
        base = Path(out_dir) if out_dir else primary.parent
        target = base / f"{primary.name}.{fmt}"
    elif out_dir:
        target = Path(out_dir) / f"{primary.stem}.{fmt}"
    else:
        target = primary.with_suffix(f".{fmt}")

    format_in = "folder" if cfg.directory_input else primary.suffix.lower().lstrip(".")
    return Task(
        input_path=primary,
        output_path=target,
        format_in=format_in or fmt,
        format_out=fmt,
        engine=cfg.engine,
        options=dict(options or {}),
        extra_inputs=list(extra_inputs),
    )


# A factory matching create_default_queue's signature, for test injection.
QueueFactory = Callable[[], object]


class QueueController:
    """Owns the TaskQueue on a background asyncio loop and bridges to GTK.

    ``on_change`` is invoked on the GTK main thread with a fresh snapshot
    list of tasks whenever any task changes.
    """

    def __init__(
        self,
        on_change: Callable[[list[Task]], None],
        *,
        queue_factory: QueueFactory = create_default_queue,
    ) -> None:
        self._on_change = on_change
        self._queue_factory = queue_factory
        self._queue = None
        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        self._thread = threading.Thread(
            target=self._run_loop, name="trex-queue", daemon=True
        )
        self._thread.start()
        self._ready.wait()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._queue = self._queue_factory()
        self._queue.subscribe(self._on_task_event)
        self._queue.start()
        self._ready.set()
        self._loop.run_forever()

    # -- loop-thread → GTK-thread -----------------------------------------

    def _on_task_event(self, _task: Task) -> None:
        # Runs on the loop thread. Snapshot here (cheap, GIL-safe) and hand
        # the list to the GTK thread; never touch widgets from here.
        snapshot = list(self._queue.all())
        GLib.idle_add(self._deliver, snapshot)

    def _deliver(self, snapshot: list[Task]) -> bool:
        self._on_change(snapshot)
        return False  # one-shot idle callback

    # -- GTK-thread → loop-thread -----------------------------------------

    def submit(self, task: Task) -> None:
        self._loop.call_soon_threadsafe(self._queue.add, task)

    def cancel(self, task_id: str) -> None:
        self._loop.call_soon_threadsafe(self._queue.cancel, task_id)

    def retry(self, task_id: str) -> None:
        self._loop.call_soon_threadsafe(self._safe_retry, task_id)

    def _safe_retry(self, task_id: str) -> None:
        try:
            self._queue.retry(task_id)
        except ValueError:
            pass  # not in a retryable state anymore

    def snapshot(self) -> list[Task]:
        """Current tasks (GIL-safe read of the queue's dict snapshot)."""
        if self._queue is None:
            return []
        return list(self._queue.all())

    def shutdown(self) -> None:
        """Best-effort graceful stop: close the queue and stop the loop."""
        if self._queue is not None:
            future = asyncio.run_coroutine_threadsafe(
                self._queue.close(), self._loop
            )
            try:
                future.result(timeout=5)
            except Exception:
                pass
        self._loop.call_soon_threadsafe(self._loop.stop)
