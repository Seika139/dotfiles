from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest
from PIL import Image, ImageDraw

from auto_emulator.config import (
    AutomationConfig,
    AutomationStep,
    ConditionNode,
    DetectorSpec,
    WatchConfig,
)
from auto_emulator.detectors.ocr import OCRDetector
from auto_emulator.detectors.template import TemplateMatchDetector
from auto_emulator.runtime.context import AutomationContext, StepRuntimeContext
from auto_emulator.services.capture import FileSequenceCaptureService
from mouse_core.pointer import PointerController
from mouse_core.region import Region


class DummyPointer:
    def click_relative(
        self,
        _region: Region,
        _relative: tuple[float, float],
        *,
        button: object | None = None,
        ensure_move: bool = True,
    ) -> None:
        del button, ensure_move

    def click_absolute(
        self,
        _x: int,
        _y: int,
        *,
        button: object | None = None,
        ensure_move: bool = True,
    ) -> None:
        del button, ensure_move

    def drag_relative(
        self,
        _region: Region,
        _start: tuple[float, float],
        _end: tuple[float, float],
        *,
        button: object | None = None,
        profile: tuple[int, float, float] | None = None,
    ) -> None:
        del button, profile


def _prepare_context(
    image: Image.Image,
    watch: WatchConfig,
    shared_state: dict[str, Any] | None = None,
) -> StepRuntimeContext:
    step = AutomationStep(
        id="step",
        watch=watch,
        conditions=ConditionNode(op="always"),
        actions=[],
    )
    config = AutomationConfig(version="1.0", steps=[step])
    config.metadata["__base_dir__"] = "."
    capture = FileSequenceCaptureService([image])
    context = AutomationContext(
        config=config,
        pointer=cast("PointerController", DummyPointer()),
        capture_service=capture,
        calibration_region=Region(
            left=0,
            top=0,
            right=image.width,
            bottom=image.height,
        ),
    )
    if shared_state:
        context.shared_state.update(shared_state)
    return StepRuntimeContext(context=context, step=step)


def test_template_detector_matches(tmp_path: Path) -> None:
    base_image = Image.new("RGB", (80, 80), color="white")
    draw = ImageDraw.Draw(base_image)
    draw.rectangle((20, 20, 40, 40), fill="red")
    draw.line((20, 20, 40, 40), fill="black", width=1)
    draw.line((20, 40, 40, 20), fill="black", width=1)

    template = base_image.crop((20, 20, 40, 40))
    template_path = tmp_path / "template.png"
    template.save(template_path)

    spec = DetectorSpec(
        type="template",
        options={
            "template_path": str(template_path),
            "threshold": 0.6,
            "grayscale": False,
        },
    )
    watch = WatchConfig(detector=spec)
    ctx = _prepare_context(base_image, watch)

    detector = TemplateMatchDetector(spec)
    result = detector.detect(watch, ctx)

    assert result.matched
    assert result.data is not None
    rel_center = cast("tuple[float, float]", result.data["relative_center"])
    assert pytest.approx(rel_center[0], abs=0.05) == 0.375
    assert pytest.approx(rel_center[1], abs=0.05) == 0.375


def test_ocr_detector_matches_pattern() -> None:
    base_image = Image.new("RGB", (100, 40), color="white")
    spec = DetectorSpec(
        type="ocr",
        options={"pattern": r"hello", "lang": "eng"},
    )
    watch = WatchConfig(detector=spec)
    ctx = _prepare_context(base_image, watch)

    with patch("pytesseract.image_to_string", return_value="Hello World"):
        detector = OCRDetector(spec)
        result = detector.detect(watch, ctx)

    assert result.matched
    assert result.data is not None
    assert result.data["text"] == "hello world"
