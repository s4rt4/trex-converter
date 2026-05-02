# Changelog

## Unreleased

- Reworked the main UI into a sidebar layout with separate Image, Video, Document, and PDF Tools pages.
- Added category-specific task forms and filtered task queues per page.

## 0.3.0

- Added real async ImageMagick engine execution with resize, quality, and strip options.
- Added SQLite task repository for history and restart recovery.
- Added persistent queue integration and GUI startup resume hook.
- Added tests for ImageMagick execution and SQLite task persistence.

## 0.2.0

- Added real async FFmpeg engine execution with `asyncio.create_subprocess_exec`.
- Added FFmpeg progress parsing from `-progress pipe:2`.
- Added FFmpeg cancellation that terminates the subprocess.
- Connected the PySide6 queue UI to the in-memory task queue.
- Added per-task progress bars plus cancel and retry buttons.
- Added tests for FFmpeg command execution, progress parsing, queue cancel, retry, registry, dependency checks, and presets.

## 0.1.0

- Added core project structure, task model, in-memory queue, dependency checker, registry, engine abstraction, UI skeleton, preset loading, Debian packaging placeholders, and baseline tests.
