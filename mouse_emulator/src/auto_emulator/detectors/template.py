from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

from auto_emulator.config import DetectorSpec, WatchConfig
from auto_emulator.detectors import register_detector
from auto_emulator.detectors.base import BaseDetector, DetectionResult
from auto_emulator.exceptions import ConfigurationError
from auto_emulator.runtime.context import StepRuntimeContext
from mouse_core.region import Region

MATCH_METHODS: dict[str, int] = {
    "TM_CCOEFF": cv2.TM_CCOEFF,
    "TM_CCOEFF_NORMED": cv2.TM_CCOEFF_NORMED,
    "TM_CCORR": cv2.TM_CCORR,
    "TM_CCORR_NORMED": cv2.TM_CCORR_NORMED,
    "TM_SQDIFF": cv2.TM_SQDIFF,
    "TM_SQDIFF_NORMED": cv2.TM_SQDIFF_NORMED,
}


def _load_template(path: str, grayscale: bool) -> np.ndarray:
    template_path = Path(path)
    if not template_path.exists():
        msg = f"テンプレート画像が見つかりません: {path}"
        raise ConfigurationError(msg)
    flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
    template = cv2.imread(str(template_path), flag)
    if template is None:
        msg = f"テンプレート画像を読み込めませんでした: {path}"
        raise ConfigurationError(msg)
    return template


@register_detector("template")
class TemplateMatchDetector(BaseDetector):
    def __init__(self, spec: DetectorSpec) -> None:
        super().__init__(spec)
        options = spec.options
        template_path = options.get("template_path")
        if not isinstance(template_path, str):
            msg = "template_path は文字列で指定してください"
            raise ConfigurationError(msg)
        self.template_path = template_path
        self.grayscale = bool(options.get("grayscale", True))
        self._template: np.ndarray | None = None
        method_name = str(options.get("match_method", "TM_CCOEFF_NORMED")).upper()
        if method_name not in MATCH_METHODS:
            msg = f"未対応のテンプレートマッチング手法です: {method_name}"
            raise ConfigurationError(msg)
        self.method = MATCH_METHODS[method_name]
        self.threshold = float(options.get("threshold", 0.8))
        if not 0 <= self.threshold <= 1:
            msg = "threshold は 0.0〜1.0 で指定してください"
            raise ConfigurationError(msg)

    def detect(self, watch: WatchConfig, ctx: StepRuntimeContext) -> DetectionResult:
        template = self._ensure_template_loaded(ctx)
        image = self.capture(watch, ctx)
        capture_array = _to_cv(image, grayscale=self.grayscale)
        compared = cv2.matchTemplate(capture_array, template, self.method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(compared)
        min_location = (int(min_loc[0]), int(min_loc[1]))
        max_location = (int(max_loc[0]), int(max_loc[1]))
        score, top_left = self._select_best(
            min_val,
            max_val,
            min_location,
            max_location,
        )
        negative_mode = self.method in _NEGATIVE_METHODS
        matched = (
            score >= self.threshold if not negative_mode else score <= self.threshold
        )
        region = ctx.resolve_watch_region(watch)
        h, w = template.shape[:2]
        result_region = None
        data: dict[str, Any] | None = None
        if matched:
            abs_left = region.left + top_left[0]
            abs_top = region.top + top_left[1]
            abs_right = abs_left + w
            abs_bottom = abs_top + h
            result_region = Region(
                left=abs_left,
                top=abs_top,
                right=abs_right,
                bottom=abs_bottom,
            )
            center_x = abs_left + w / 2
            center_y = abs_top + h / 2
            rel_x, rel_y = ctx.region.to_relative(center_x, center_y)
            data = {
                "top_left": (abs_left, abs_top),
                "bottom_right": (abs_right, abs_bottom),
                "relative_center": (rel_x, rel_y),
                "score": score,
            }
        else:
            data = {"score": score}
        normalized_score = score if not negative_mode else max(0.0, 1.0 - score)
        return DetectionResult(
            matched=matched,
            score=normalized_score,
            data=data,
            region=result_region,
        )

    def _select_best(
        self,
        min_val: float,
        max_val: float,
        min_loc: tuple[int, int],
        max_loc: tuple[int, int],
    ) -> tuple[float, tuple[int, int]]:
        if self.method in _NEGATIVE_METHODS:
            return min_val, min_loc
        return max_val, max_loc

    def _ensure_template_loaded(self, ctx: StepRuntimeContext) -> np.ndarray:
        if self._template is not None:
            return self._template
        search_paths = [
            Path(self.template_path),
        ]
        base_dir = ctx.config.metadata.get("__base_dir__")
        if isinstance(base_dir, str):
            search_paths.append(Path(base_dir) / self.template_path)
        for candidate in search_paths:
            if candidate.exists():
                self._template = _load_template(str(candidate), self.grayscale)
                return self._template
        msg = f"テンプレート画像が見つかりません: {self.template_path}"
        raise ConfigurationError(msg)


_NEGATIVE_METHODS: set[int] = {cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED}


def _to_cv(image: Image.Image, *, grayscale: bool) -> np.ndarray:
    array = np.array(image)
    if grayscale:
        if len(array.shape) == 2:
            return array
        return cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)
    if len(array.shape) == 2:
        return cv2.cvtColor(array, cv2.COLOR_GRAY2BGR)
    return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
