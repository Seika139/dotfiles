from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Self

import pytest

from mouse_core.region import Region
from mouse_emulator import emulate
from mouse_emulator.profile import (
    CalibrationPreset,
    CalibrationSettings,
    ClickPosition,
    Profile,
    ProfileEntry,
    ProfileStore,
)


class _DummyEmulator:
    last_instance: _DummyEmulator | None = None

    def __init__(
        self,
        *,
        profile: Profile,
        region: Region,
        monitor: object,
        log: object,
    ) -> None:
        type(self).last_instance = self
        self.profile = profile
        self.region = region
        self.monitor = monitor
        self.log = log

    def run(self) -> None:  # pragma: no cover - 動作なし
        return


def _build_profile(*, enabled: bool, preset: CalibrationPreset | None) -> Profile:
    entry = ProfileEntry(
        description="test",
        click_position=ClickPosition(x=0.5, y=0.5),
        keys=["space"],
    )
    return Profile(
        actions=[entry],
        calibration=CalibrationSettings(enabled=enabled, preset=preset),
    )


@dataclass(slots=True)
class _DummyImage:
    width: int
    height: int


class _DummyCaptureService:
    def __init__(
        self,
        *,
        should_raise: bool = False,
        width: int = 100,
        height: int = 100,
    ) -> None:
        self.should_raise = should_raise
        self.width = width
        self.height = height

    def capture(self, region: Region | None = None) -> _DummyImage:
        del region
        if self.should_raise:
            msg = "capture failed"
            raise RuntimeError(msg)
        return _DummyImage(self.width, self.height)


def _create_dummy_monitor(*_: object, **__: object) -> _DummyMonitor:
    return _DummyMonitor()


def test_emulate_uses_preset_when_valid(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store = ProfileStore(base_dir=tmp_path)
    profile = _build_profile(
        enabled=False,
        preset=CalibrationPreset(left=10, top=20, right=110, bottom=220),
    )
    target = store.resolve_path("preset")
    store.save(target, profile)

    monkeypatch.setattr(emulate, "Emulator", _DummyEmulator)
    monkeypatch.setattr(
        emulate,
        "TerminationMonitor",
        _create_dummy_monitor,
    )
    monkeypatch.setattr(emulate, "PILScreenCaptureService", _DummyCaptureService)
    run_calls: list[None] = []

    def fake_run_calibration(_printer: object) -> Region:
        run_calls.append(None)
        return Region(left=0, top=0, right=1, bottom=1)

    monkeypatch.setattr(emulate, "run_calibration", fake_run_calibration)
    monkeypatch.setattr(emulate, "is_region_within_displays", lambda _: True)

    emulate.emulate_from_profile(Path("preset"), base_dir=tmp_path)

    assert not run_calls
    assert _DummyEmulator.last_instance is not None
    region = _DummyEmulator.last_instance.region
    assert (region.left, region.top, region.right, region.bottom) == (10, 20, 110, 220)
    captured = capsys.readouterr()
    assert "設定済みの座標を使用します" in captured.out


def test_emulate_fallbacks_when_preset_invalid(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store = ProfileStore(base_dir=tmp_path)
    profile = _build_profile(
        enabled=False,
        preset=CalibrationPreset(left=10, top=20, right=110, bottom=220),
    )
    target = store.resolve_path("preset")
    store.save(target, profile)

    monkeypatch.setattr(emulate, "Emulator", _DummyEmulator)
    monkeypatch.setattr(
        emulate,
        "TerminationMonitor",
        _create_dummy_monitor,
    )
    monkeypatch.setattr(emulate, "PILScreenCaptureService", _DummyCaptureService)
    run_calls: list[None] = []

    def fake_run_calibration(_printer: object) -> Region:
        run_calls.append(None)
        return Region(left=1, top=2, right=3, bottom=4)

    monkeypatch.setattr(emulate, "run_calibration", fake_run_calibration)
    monkeypatch.setattr(emulate, "is_region_within_displays", lambda _: False)

    emulate.emulate_from_profile(Path("preset"), base_dir=tmp_path)

    assert run_calls, "フォールバック時には run_calibration が呼び出されるはず"
    assert _DummyEmulator.last_instance is not None
    region = _DummyEmulator.last_instance.region
    assert (region.left, region.top, region.right, region.bottom) == (1, 2, 3, 4)
    captured = capsys.readouterr()
    assert "一致しません" in captured.out


def test_emulate_runs_calibration_when_preset_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = ProfileStore(base_dir=tmp_path)
    profile = _build_profile(enabled=False, preset=None)
    target = store.resolve_path("preset")
    store.save(target, profile)

    monkeypatch.setattr(emulate, "Emulator", _DummyEmulator)
    monkeypatch.setattr(
        emulate,
        "TerminationMonitor",
        _create_dummy_monitor,
    )
    monkeypatch.setattr(emulate, "PILScreenCaptureService", _DummyCaptureService)
    run_calls: list[None] = []

    def fake_run_calibration(_printer: object) -> Region:
        run_calls.append(None)
        return Region(left=5, top=6, right=7, bottom=8)

    monkeypatch.setattr(emulate, "run_calibration", fake_run_calibration)
    monkeypatch.setattr(emulate, "is_region_within_displays", lambda _: True)

    emulate.emulate_from_profile(Path("preset"), base_dir=tmp_path)

    assert run_calls
    assert _DummyEmulator.last_instance is not None
    region = _DummyEmulator.last_instance.region
    assert (region.left, region.top, region.right, region.bottom) == (5, 6, 7, 8)


def test_emulate_fallbacks_when_capture_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = ProfileStore(base_dir=tmp_path)
    profile = _build_profile(
        enabled=False,
        preset=CalibrationPreset(left=10, top=20, right=110, bottom=220),
    )
    target = store.resolve_path("preset")
    store.save(target, profile)

    monkeypatch.setattr(emulate, "Emulator", _DummyEmulator)
    monkeypatch.setattr(
        emulate,
        "TerminationMonitor",
        _create_dummy_monitor,
    )
    monkeypatch.setattr(
        emulate,
        "PILScreenCaptureService",
        partial(_DummyCaptureService, should_raise=True),
    )

    run_calls: list[None] = []

    def fake_run_calibration(_printer: object) -> Region:
        run_calls.append(None)
        return Region(left=3, top=4, right=5, bottom=6)

    monkeypatch.setattr(emulate, "run_calibration", fake_run_calibration)
    monkeypatch.setattr(emulate, "is_region_within_displays", lambda _: True)

    emulate.emulate_from_profile(Path("preset"), base_dir=tmp_path)

    assert run_calls
    assert _DummyEmulator.last_instance is not None
    region = _DummyEmulator.last_instance.region
    assert (region.left, region.top, region.right, region.bottom) == (3, 4, 5, 6)


class _DummyMonitor:
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        return None

    def stop_requested(self) -> bool:
        return False

    def wait_if_paused(self, _interval: float = 0.1) -> None:
        return None
