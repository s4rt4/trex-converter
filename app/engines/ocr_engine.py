from __future__ import annotations

from abc import abstractmethod

from app.core.task import Task
from app.engines.base import BaseEngine, EngineCapabilities, StubEngine


class BaseOCREngine(BaseEngine):
    @abstractmethod
    async def extract_text(self, task: Task) -> str:
        raise NotImplementedError


class TesseractOCREngine(StubEngine):
    def __init__(self) -> None:
        super().__init__(
            name="tesseract",
            supported_pairs={
                ("png", "txt"),
                ("jpg", "txt"),
                ("jpeg", "txt"),
                ("pdf", "txt"),
            },
            requires_binary="tesseract",
        )

    async def extract_text(self, task: Task) -> str:
        task.append_log("tesseract stub OCR executed")
        return ""

    @property
    def capabilities(self) -> EngineCapabilities:
        return super().capabilities
