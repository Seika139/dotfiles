from __future__ import annotations

import time
from pathlib import Path

import typer
from pynput import mouse

from mouse_core import ColorPrinter, Colors, PointerController, run_calibration

from .config import AutomationConfig, load_config
from .exceptions import AutoEmulatorError, ConfigurationError
from .runtime.engine import AutomationEngine
from .runtime.termination import TerminationMonitor
from .services.capture import PILScreenCaptureService

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


def _should_calibrate(cli_flag: bool | None, config: AutomationConfig) -> bool:
    if cli_flag is not None:
        return cli_flag
    return config.runtime.calibration.enabled


def _calibration_color(config: AutomationConfig) -> str:
    color_key = config.runtime.calibration.color
    return COLOR_MAP.get(color_key, Colors.GREEN)


@app.command("run")
def run_automation(
    config_path: str = typer.Argument(..., help="自動化設定ファイル (YAML/JSON)"),
    calibrate: bool | None = typer.Option(
        None,
        "--calibrate/--no-calibrate",
        help="キャリブレーションを実行するか指定します (未指定の場合は設定値に従う)",
    ),
) -> None:
    try:
        path = _resolve_config_path(config_path)
        config = load_config(path)
        region = None
        if _should_calibrate(calibrate, config):
            printer = ColorPrinter(_calibration_color(config))
            region = run_calibration(printer)
        engine = AutomationEngine(
            config=config,
            pointer=PointerController(),
            region=region,
            capture_service=PILScreenCaptureService(),
        )
        with TerminationMonitor() as monitor:
            try:
                engine.run(stop_monitor=monitor)
            except KeyboardInterrupt:
                typer.echo("ユーザー操作により自動化を中断しました")
                raise typer.Exit(code=0) from None
    except AutoEmulatorError as exc:
        typer.echo(f"エラー: {exc}")
        raise typer.Exit(code=1) from None
    except FileNotFoundError:
        typer.echo("設定ファイルが見つかりませんでした")
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


@app.command("probe")
def probe_coordinates(
    interval: float = typer.Option(
        0.5,
        help="interval モード時の表示間隔(秒)",
    ),
    mode: str = typer.Option(
        "click", help="interval: 定期表示, click: クリック時のみ表示"
    ),
) -> None:
    """キャリブレーション後に現在のマウス座標(相対値)を表示する。"""
    try:
        printer = ColorPrinter(Colors.BLUE)
        region = run_calibration(printer)
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
                    try:
                        rel_x, rel_y = region.to_relative(x, y)
                        typer.echo(
                            f"click button={button.name} abs=({int(x)}, {int(y)}) "
                            f"rel=({rel_x:.3f}, {rel_y:.3f})",
                        )
                    except ValueError:
                        typer.echo(
                            f"click button={button.name} abs=({int(x)}, {int(y)}) "
                            "rel=領域外",
                        )

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
                    try:
                        rel_x, rel_y = region.to_relative(abs_x, abs_y)
                        typer.echo(
                            f"abs=({abs_x}, {abs_y}) rel=({rel_x:.3f}, {rel_y:.3f})",
                        )
                    except ValueError:
                        typer.echo(f"abs=({abs_x}, {abs_y}) rel=領域外")
                    time.sleep(max(0.05, interval))
    except KeyboardInterrupt:
        typer.echo("プローブを終了します")


if __name__ == "__main__":
    main()
