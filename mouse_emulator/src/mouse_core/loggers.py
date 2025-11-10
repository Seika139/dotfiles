from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Literal, Self, TextIO, cast


@dataclass(slots=True)
class SessionLogger:
    """シンプルなセッションログ出力ヘルパー。"""

    path: Path | None
    mode: Literal["append", "overwrite"] = "append"
    timestamp: bool = True
    _handle: TextIO | None = None

    def __post_init__(self) -> None:
        if self.path is None:
            return
        resolved = self.path.expanduser()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        file_mode = "a" if self.mode == "append" else "w"
        handle = cast("TextIO", resolved.open(file_mode, encoding="utf-8"))
        self._handle = handle
        self.path = resolved

    def log(self, message: str) -> None:
        if self._handle is None:
            return
        line = message
        if self.timestamp:
            current = datetime.now(tz=UTC).astimezone()
            timestamp = current.isoformat(sep=" ", timespec="seconds")
            line = f"[{timestamp}] {message}"
        self._handle.write(line + "\n")
        self._handle.flush()

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
