from __future__ import annotations

from pathlib import Path

import typer

from mouse_core import ColorPrinter, Colors, PointerController, run_calibration

from .config import AutomationConfig, load_config
from .exceptions import AutoEmulatorError, ConfigurationError
from .runtime.engine import AutomationEngine
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
        engine.run()
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


if __name__ == "__main__":
    main()
