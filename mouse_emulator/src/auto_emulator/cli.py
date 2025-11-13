from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Annotated, Literal

import typer
from pynput import mouse

from mouse_core import ColorPrinter, Colors, PointerController, Region, run_calibration
from mouse_core.display import (
    NSScreen,
    ScreenLike,
    is_region_within_displays,
    to_nss_point,
)
from mouse_core.loggers import SessionLogger
from mouse_emulator.keys import parse_combo

from .config import AutomationConfig, load_config
from .exceptions import AutoEmulatorError, ConfigurationError
from .runtime.engine import AutomationEngine
from .runtime.termination import TerminationMonitor
from .services.capture import (
    PILScreenCaptureService,
    ScreenCaptureService,
)

app = typer.Typer(
    help="画像/OCR ベースの自動クリックエンジン",
    add_completion=False,
)

DEFAULT_CONFIG_DIR = Path("profiles/auto_emulator")

COLOR_MAP = {
    "default": Colors.DEFAULT,
    "green": Colors.GREEN,
    "blue": Colors.BLUE,
    "warning": Colors.WARNING,
    "fail": Colors.FAIL,
}

PAUSE_NOTICE = "⏸ 一時停止しました。再開するには指定したキーを押してください。"
RESUME_NOTICE = "▶️ 自動化を再開します。"

CALIBRATE_OPTION = typer.Option(
    None,
    "--calibrate/--no-calibrate",
    help="キャリブレーションを実行するか指定します (未指定の場合は設定値に従う)",
)

PAUSE_KEY_OPTION = typer.Option(
    None,
    "--pause-key",
    help="一時停止/再開をトグルするキーコンボ (例: 'ctrl+p', 'none' で無効化)",
)

LOG_FILE_OPTION = typer.Option(
    None,
    "--log-file",
    help="ログを書き出すファイルパス (指定がなければ標準出力のみ)",
)

LOG_OVERWRITE_OPTION = typer.Option(
    False,
    "--log-overwrite",
    help="ログファイルを上書きモードで開きます (指定がなければ追記)",
)

INTERVAL_OPTION = typer.Option(
    0.5,
    "--interval",
    help="interval モード時の表示間隔(秒)",
    show_default=True,
)

MODE_OPTION = typer.Option(
    "click",
    "--mode",
    help="interval: 定期表示, click: クリック時のみ表示",
    show_default=True,
)


def _normalize_pause_combo(raw: str | None) -> tuple[str, ...] | None:
    if raw is None:
        return None
    cleaned = raw.strip()
    if not cleaned or cleaned.lower() in {"none", "off", "disable"}:
        return None
    return parse_combo(cleaned)


def _resolve_log_path(value: str | None, base_dir: Path) -> Path | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    path = Path(cleaned).expanduser()
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def _resolve_config_path(value: str) -> Path:
    candidate = Path(value)
    if candidate.exists():
        return candidate
    if candidate.is_absolute():
        return candidate
    if not candidate.suffix:
        for suffix in (".yaml", ".yml", ".json"):
            enriched = candidate.with_suffix(suffix)
            if enriched.exists():
                return enriched
            candidate_in_dir = DEFAULT_CONFIG_DIR / enriched.name
            if candidate_in_dir.exists():
                return candidate_in_dir
    candidate_in_dir = DEFAULT_CONFIG_DIR / candidate
    if candidate_in_dir.exists():
        return candidate_in_dir
    return candidate


def _resolve_pause_combo_value(
    pause_key: str | None,
    config: AutomationConfig,
) -> tuple[str, ...] | None:
    pause_source = (
        pause_key if pause_key is not None else config.runtime.controls.pause_toggle
    )
    try:
        return _normalize_pause_combo(pause_source)
    except ValueError as exc:
        if pause_key is not None:
            raise typer.BadParameter(str(exc), param_hint="--pause-key") from exc
        msg = f"runtime.controls.pause_toggle の値が不正です: {exc}"
        raise ConfigurationError(msg) from exc


def _prepare_logging_settings(
    *,
    log_file: Path | None,
    log_overwrite: bool,
    config: AutomationConfig,
    base_dir: Path,
) -> tuple[Path | None, Literal["append", "overwrite"]]:
    log_mode: Literal["append", "overwrite"] = config.runtime.logging.mode
    log_path: Path | None = None
    if log_file is not None:
        log_path = log_file.expanduser()
        if not log_path.is_absolute():
            log_path = (base_dir / log_path).resolve()
        if log_overwrite:
            log_mode = "overwrite"
        return log_path, log_mode

    config_log_path = _resolve_log_path(config.runtime.logging.file, base_dir)
    if config_log_path is not None:
        log_path = config_log_path
        if log_overwrite:
            log_mode = "overwrite"
    elif log_overwrite:
        log_mode = "overwrite"
    return log_path, log_mode


def _validate_preset_region(
    region: Region,
    capture_service: ScreenCaptureService,
) -> tuple[bool, str | None]:
    if not is_region_within_displays(region):
        message = (
            "設定されたキャリブレーション座標が現在のディスプレイ領域と一致しません。"
        )
        return False, message
    try:
        image = capture_service.capture(region=region)
    except Exception as exc:  # noqa: BLE001
        message = (
            "設定されたキャリブレーション座標でのキャプチャに失敗しました。"
            f" 詳細: {exc}"
        )
        return False, message
    if image.width <= 0 or image.height <= 0:
        message = "設定されたキャリブレーション座標から取得した画像サイズが不正です。"
        return False, message
    return True, None


def _should_calibrate(cli_flag: bool | None, config: AutomationConfig) -> bool:
    if cli_flag is not None:
        return cli_flag
    return config.runtime.calibration.enabled


def _calibration_color(config: AutomationConfig) -> str:
    color_key = config.runtime.calibration.color
    return COLOR_MAP.get(color_key, Colors.GREEN)


def _resolve_region(
    config: AutomationConfig,
    calibrate_flag: bool | None,
    capture_service: ScreenCaptureService,
    emit: Callable[[str], None],
) -> Region:
    calibration_settings = config.runtime.calibration
    printer = ColorPrinter(_calibration_color(config))

    if _should_calibrate(calibrate_flag, config):
        return run_calibration(printer)

    if calibration_settings.preset is not None:
        preset_region = calibration_settings.preset.to_region()
        is_valid, error_message = _validate_preset_region(
            preset_region,
            capture_service,
        )
        if is_valid:
            emit("キャリブレーションをスキップし、設定済みの座標を使用します。")
            return preset_region
        if error_message:
            emit(error_message)
        emit("手動キャリブレーションを実行します。")
        return run_calibration(printer)

    emit(
        "キャリブレーション設定が見つからないため、手動キャリブレーションを実行します。",
    )
    return run_calibration(printer)


@app.command("run")
def run_automation(
    config_path: str = typer.Argument(..., help="自動化設定ファイル (YAML/JSON)"),
    *,
    calibrate: bool | None = CALIBRATE_OPTION,
    pause_key: str | None = PAUSE_KEY_OPTION,
    log_file: Path | None = LOG_FILE_OPTION,
    log_overwrite: bool = LOG_OVERWRITE_OPTION,
) -> None:
    path = _resolve_config_path(config_path)
    try:
        config = load_config(path)
    except AutoEmulatorError as exc:
        typer.echo(f"エラー: {exc}")
        raise typer.Exit(code=1) from None

    base_dir = Path(config.metadata.get("__base_dir__", "."))
    try:
        pause_combo = _resolve_pause_combo_value(pause_key, config)
    except typer.BadParameter:
        raise
    except ConfigurationError as exc:
        typer.echo(f"エラー: {exc}")
        raise typer.Exit(code=1) from None

    log_path, log_mode = _prepare_logging_settings(
        log_file=log_file,
        log_overwrite=log_overwrite,
        config=config,
        base_dir=base_dir,
    )

    with SessionLogger(log_path, mode=log_mode) as session_logger:

        def emit(message: str) -> None:
            typer.echo(message)
            session_logger.log(message)

        capture_service = PILScreenCaptureService()
        region = _resolve_region(config, calibrate, capture_service, emit)

        if log_path is not None:
            emit(f"ログファイル: {log_path}")
        if pause_combo is not None:
            combo_label = "+".join(pause_combo)
            emit(f"一時停止キー: {combo_label} (同じキーで再開)")

        engine = AutomationEngine(
            config=config,
            pointer=PointerController(),
            region=region,
            capture_service=capture_service,
            logger=emit,
        )
        try:
            with TerminationMonitor(
                pause_combo=pause_combo,
                on_pause=(lambda: emit(PAUSE_NOTICE)) if pause_combo else None,
                on_resume=(lambda: emit(RESUME_NOTICE)) if pause_combo else None,
            ) as monitor:
                engine.run(stop_monitor=monitor)
        except KeyboardInterrupt:
            emit("ユーザー操作により自動化を中断しました")
            raise typer.Exit(code=0) from None
        except AutoEmulatorError as exc:
            emit(f"エラー: {exc}")
            raise typer.Exit(code=1) from None


@app.command("validate")
def validate_config(
    config_path: str = typer.Argument(..., help="検証する設定ファイル"),
) -> None:
    try:
        path = _resolve_config_path(config_path)
        load_config(path)
        typer.echo("✅ 設定ファイルの検証に成功しました")
    except ConfigurationError as exc:
        typer.echo(f"❌ 設定ファイルに問題があります: {exc}")
        raise typer.Exit(code=1) from None


def main() -> None:
    app()


def find_screen_for_point(
    x: float,
    y: float,
) -> tuple[ScreenLike | None, float | None, float | None]:
    """pynputのグローバル座標から属するスクリーンと NSScreen 座標を返す。

    Returns:
        (screen, x_ns, y_ns): 所属スクリーンと NSScreen 座標。
        (None, None, None): スクリーンが見つからない場合。
    """
    if NSScreen is None:
        return None, None, None
    point = to_nss_point(x, y)
    if point is None:
        return None, None, None
    x_ns, y_ns = point
    screens: Sequence[ScreenLike] = NSScreen.screens() if NSScreen else []
    for screen in screens:
        frame = screen.frame()
        left = float(frame.origin.x)
        right = left + float(frame.size.width)
        bottom = float(frame.origin.y)
        top = bottom + float(frame.size.height)
        if left <= x_ns < right and bottom <= y_ns <= top:
            return screen, x_ns, y_ns
    return None, None, None


@app.command("probe")
def probe_coordinates(
    interval: float = INTERVAL_OPTION,
    mode: str = MODE_OPTION,
) -> None:
    """キャリブレーション後に現在のマウス座標(相対値)を表示する。"""
    try:
        printer = ColorPrinter(Colors.BLUE)
        region = run_calibration(printer)

        def convert_to_relative_in_screen(
            x: float,
            y: float,
        ) -> tuple[float, float, ScreenLike, float, float]:
            """pynput座標 → スクリーン相対座標 (0.0〜1.0)

            Returns:
                (rel_x, rel_y, screen, x_ns, y_ns)

            Raises:
                ValueError: スクリーン外の場合
            """
            screen, x_ns, y_ns = find_screen_for_point(x, y)
            if screen is None or x_ns is None or y_ns is None:
                raise ValueError("スクリーン外")

            frame = screen.frame()
            width = float(frame.size.width)
            height = float(frame.size.height)
            if width <= 0 or height <= 0:
                raise ValueError("スクリーンサイズが不正です")

            left = float(frame.origin.x)
            bottom = float(frame.origin.y)
            rel_x = (x_ns - left) / width
            rel_from_bottom = (y_ns - bottom) / height
            rel_y = 1.0 - rel_from_bottom

            # 端の微小な浮動小数点誤差を丸める
            rel_x = max(0.0, min(1.0, rel_x))
            rel_y = max(0.0, min(1.0, rel_y))
            return rel_x, rel_y, screen, float(x_ns), float(y_ns)

        def format_point(x: float, y: float) -> str:
            parts: list[str] = [f"abs(pynput)=({int(x)}, {int(y)})"]
            try:
                rel_rx, rel_ry = region.to_relative(x, y)
            except ValueError:
                parts.append("rel(region)=領域外")
            else:
                parts.append(f"rel(region)=({rel_rx:.3f}, {rel_ry:.3f})")

            try:
                rel_sx, rel_sy, screen, x_ns, y_ns = convert_to_relative_in_screen(x, y)
            except ValueError:
                parts.append("screen=不明")
            else:
                frame = screen.frame()
                parts.extend([
                    f"screen=({int(frame.origin.x)}, {int(frame.origin.y)}, "
                    f"{int(frame.size.width)}x{int(frame.size.height)})",
                    f"rel(screen)=({rel_sx:.3f}, {rel_sy:.3f})",
                    f"abs(nss)=({int(x_ns)}, {int(y_ns)})",
                ])
            return " ".join(parts)

        normalized_mode = mode.lower()
        pointer = PointerController()

        with TerminationMonitor() as monitor:
            if normalized_mode == "click":
                typer.echo(
                    "クリックするとカーソル位置(絶対 / 相対)を表示します。"
                    "Ctrl+C で終了。",
                )

                def on_click(
                    x: float,
                    y: float,
                    button: mouse.Button,
                    pressed: bool,
                ) -> None:
                    if monitor.stop_requested() or not pressed:
                        return
                    typer.echo(f"[{button.name}] {format_point(x, y)}")

                listener = mouse.Listener(on_click=on_click)
                listener.start()
                try:
                    while listener.is_alive() and not monitor.stop_requested():
                        time.sleep(0.1)
                finally:
                    listener.stop()
                    listener.join()

            else:
                typer.echo(
                    "現在のカーソル位置(絶対 / 相対)を表示します。Ctrl+C で終了。",
                )
                while not monitor.stop_requested():
                    abs_x, abs_y = pointer.position()
                    typer.echo(format_point(float(abs_x), float(abs_y)))
                    time.sleep(max(0.05, interval))
    except KeyboardInterrupt:
        typer.echo("プローブを終了します")


if __name__ == "__main__":
    main()
ConfigArgument = Annotated[
    str,
    typer.Argument(..., help="自動化設定ファイル (YAML/JSON)"),
]

CalibrateOption = Annotated[
    bool | None,
    typer.Option(
        None,
        "--calibrate/--no-calibrate",
        help="キャリブレーションを実行するか指定します (未指定の場合は設定値に従う)",
    ),
]

PauseKeyOption = Annotated[
    str | None,
    typer.Option(
        None,
        "--pause-key",
        help="一時停止/再開をトグルするキーコンボ (例: 'ctrl+p', 'none' で無効化)",
    ),
]

LogFileOption = Annotated[
    Path | None,
    typer.Option(
        None,
        "--log-file",
        help="ログを書き出すファイルパス (指定がなければ標準出力のみ)",
    ),
]

LogOverwriteOption = Annotated[
    bool,
    typer.Option(
        False,
        "--log-overwrite",
        help="ログファイルを上書きモードで開きます (指定がなければ追記)",
    ),
]

IntervalOption = Annotated[
    float,
    typer.Option(
        0.5,
        "--interval",
        help="interval モード時の表示間隔(秒)",
        show_default=True,
    ),
]

ModeOption = Annotated[
    str,
    typer.Option(
        "click",
        "--mode",
        help="interval: 定期表示, click: クリック時のみ表示",
        show_default=True,
    ),
]
