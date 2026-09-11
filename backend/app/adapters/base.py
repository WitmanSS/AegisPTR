from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SecurityToolAdapter(ABC):
    """Base interface for security tool adapters."""

    name: str = "unknown"
    version: str = "unknown"

    @abstractmethod
    def detect(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def validate(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def build_command(self, target: str, options: dict[str, Any] | None = None) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def execute(self, target: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def parse_output(self, raw_output: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, record: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        raise NotImplementedError
