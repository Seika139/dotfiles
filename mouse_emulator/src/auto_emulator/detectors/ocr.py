from __future__ import annotations

import re

import pytesseract  # type: ignore[import-untyped]
from PIL import Image

from auto_emulator.config import DetectorSpec, WatchConfig
from auto_emulator.detectors import register_detector
from auto_emulator.detectors.base import BaseDetector, DetectionResult
from auto_emulator.exceptions import ConfigurationError, EngineRuntimeError
from auto_emulator.runtime.context import StepRuntimeContext


def _prepare_image(
    image: Image.Image, *, grayscale: bool, threshold: int | None
) -> Image.Image:
    working = image.convert("L") if grayscale else image
    if threshold is not None:
        if not 0 <= threshold <= 255:
            msg = "threshold は 0 〜 255 の範囲で指定してください"
            raise ConfigurationError(msg)
        working = working.point(lambda value: 255 if value > threshold else 0)
    return working


@register_detector("ocr")
class OCRDetector(BaseDetector):
    def __init__(self, spec: DetectorSpec) -> None:
        super().__init__(spec)
        options = spec.options
        self.lang = str(options.get("lang", "eng"))
        self.config = options.get("tesseract_config")
        self.pattern = options.get("pattern")
        self.contains = options.get("contains")
        self.strip = bool(options.get("strip", True))
        self.lowercase = bool(options.get("lowercase", True))
        self.grayscale = bool(options.get("grayscale", True))
        threshold = options.get("threshold")
        self.threshold: int | None
        if threshold is None:
            self.threshold = None
        else:
            self.threshold = int(threshold)
        self.tesseract_cmd = options.get("tesseract_cmd")
        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = str(self.tesseract_cmd)
        if self.pattern is not None and not isinstance(self.pattern, str):
            msg = "pattern は文字列で指定してください"
            raise ConfigurationError(msg)
        if self.contains is not None and not isinstance(self.contains, str):
            msg = "contains は文字列で指定してください"
            raise ConfigurationError(msg)

    def detect(self, watch: WatchConfig, ctx: StepRuntimeContext) -> DetectionResult:
        image = self.capture(watch, ctx)
        prepared = _prepare_image(
            image,
            grayscale=self.grayscale,
            threshold=self.threshold,
        )
        try:
            text = pytesseract.image_to_string(
                prepared,
                lang=self.lang,
                config=self.config,
            )
        except (
            pytesseract.TesseractNotFoundError
        ) as exc:  # pragma: no cover - depends on env
            message = (
                "Tesseract 実行バイナリが見つかりません。"
                "tesseract_cmd オプションを確認してください。"
            )
            raise EngineRuntimeError(message) from exc
        processed = text
        if self.strip:
            processed = processed.strip()
        if self.lowercase:
            processed = processed.lower()
        matched, score = self._evaluate_text(processed)
        return DetectionResult(
            matched=matched,
            score=score,
            data={"text": processed},
            region=None,
        )

    def _evaluate_text(self, text: str) -> tuple[bool, float | None]:
        if self.pattern:
            regex = re.compile(self.pattern, re.IGNORECASE if self.lowercase else 0)
            if regex.search(text):
                return True, 1.0
            return False, 0.0
        if self.contains:
            haystack = text
            needle_source = self.contains.lower() if self.lowercase else self.contains
            needle = needle_source
            return (needle in haystack, 1.0 if needle in haystack else 0.0)
        return (bool(text), 1.0 if text else 0.0)
