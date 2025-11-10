from __future__ import annotations

from pathlib import Path

import typer

from .emulate import EmulateOptions, emulate_from_profile
from .register import register_profile

app = typer.Typer(
    help="キーボードでマウス操作をエミュレートするツール",
    add_completion=False,
)

DEFAULT_PROFILE_DIR = Path("profiles/mouse_emulator")

CALIBRATE_OPTION = typer.Option(
    None,
    "--calibrate/--no-calibrate",
    help=(
        "キャリブレーションを実行するか指定します "
        "(未指定の場合はプロファイル設定に従う)"
    ),
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


@app.command()
def register(
    name: str = typer.Argument(..., help="保存するプロファイル名 (拡張子不要)"),
) -> None:
    try:
        register_profile(name, base_dir=DEFAULT_PROFILE_DIR)
    except KeyboardInterrupt:
        typer.echo("ユーザー操作により登録を中断しました")
        raise typer.Exit(code=1) from None
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"エラー: {exc}")
        raise typer.Exit(code=1) from None


@app.command()
def emulate(
    profile: str = typer.Argument(..., help="読み込むプロファイルのパスまたは名前"),
    *,
    calibrate: bool | None = CALIBRATE_OPTION,
    pause_key: str | None = PAUSE_KEY_OPTION,
    log_file: Path | None = LOG_FILE_OPTION,
    log_overwrite: bool = LOG_OVERWRITE_OPTION,
) -> None:
    try:
        options = EmulateOptions(
            calibrate=calibrate,
            pause_key=pause_key,
            log_file=log_file,
            log_overwrite=log_overwrite,
        )
        emulate_from_profile(
            Path(profile),
            base_dir=DEFAULT_PROFILE_DIR,
            options=options,
        )
    except FileNotFoundError:
        typer.echo("指定されたプロファイルが見つかりません")
        raise typer.Exit(code=1) from None
    except KeyboardInterrupt:
        typer.echo("ユーザー操作により終了しました")
        raise typer.Exit(code=1) from None
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"エラー: {exc}")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    app()
