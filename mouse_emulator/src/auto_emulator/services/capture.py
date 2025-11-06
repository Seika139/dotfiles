from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from PIL import Image, ImageGrab

from mouse_core.region import Region


@dataclass(slots=True)
class CaptureConfig:
    retry_count: int = 0
    retry_interval: float = 0.05


class ScreenCaptureService(Protocol):
    def capture(
        self, region: Region | None = None
    ) -> Image.Image:  # pragma: no cover - protocol
        ...


class PILScreenCaptureService:
    """Pillow の ImageGrab を利用したシンプルなキャプチャ実装。"""

    def __init__(self, config: CaptureConfig | None = None) -> None:
        self._config = config or CaptureConfig()

    def capture(self, region: Region | None = None) -> Image.Image:
        bbox = None
        if region is not None:
            bbox = (
                int(region.left),
                int(region.top),
                int(region.right),
                int(region.bottom),
            )
        attempts = self._config.retry_count + 1
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                return ImageGrab.grab(bbox=bbox)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(self._config.retry_interval)
        if last_error is not None:
            raise last_error
        raise RuntimeError("スクリーンキャプチャに失敗しました")


class FileSequenceCaptureService:
    """テスト用途: 指定した画像群を順次返すキャプチャサービス。"""

    def __init__(self, images: list[Image.Image]) -> None:
        if not images:
            raise ValueError("少なくとも1枚の画像が必要です")
        self._images = images
        self._index = 0

    def capture(self, region: Region | None = None) -> Image.Image:
        image = self._images[self._index]
        if region is not None:
            cropped = image.crop(
                (
                    int(region.left),
                    int(region.top),
                    int(region.right),
                    int(region.bottom),
                ),
            )
        else:
            cropped = image
        self._index = (self._index + 1) % len(self._images)
        return cropped.copy()
