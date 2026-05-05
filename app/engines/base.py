from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.task import Task


@dataclass(frozen=True, slots=True)
class EngineCapabilities:
    supports_progress: bool
    supports_cancel: bool
    requires_binary: str
    extra_binaries: tuple[str, ...] = ()


class BaseEngine(ABC):
    name: str = "base"

    @abstractmethod
    async def convert(self, task: Task) -> None:
        raise NotImplementedError

    @abstractmethod
    def supports(self, format_in: str, format_out: str) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def capabilities(self) -> EngineCapabilities:
        raise NotImplementedError

    async def cancel(self, task: Task) -> None:
        task.mark_cancelled()


class StubEngine(BaseEngine):
    name = "stub"

    def __init__(
        self,
        name: str,
        supported_pairs: set[tuple[str, str]],
        requires_binary: str,
        supports_progress: bool = False,
    ) -> None:
        self.name = name
        self._supported_pairs = {
            (format_in.lower(), format_out.lower())
            for format_in, format_out in supported_pairs
        }
        self._capabilities = EngineCapabilities(
            supports_progress=supports_progress,
            supports_cancel=True,
            requires_binary=requires_binary,
        )

    async def convert(self, task: Task) -> None:
        task.append_log(f"{self.name} stub conversion executed")
        task.progress = 1.0

    def supports(self, format_in: str, format_out: str) -> bool:
        return (format_in.lower(), format_out.lower()) in self._supported_pairs

    @property
    def capabilities(self) -> EngineCapabilities:
        return self._capabilities
