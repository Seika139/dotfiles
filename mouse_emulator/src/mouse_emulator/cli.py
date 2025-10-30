from __future__ import annotations

from pathlib import Path

import typer

from .emulate import emulate_from_profile
from .register import register_profile

app = typer.Typer(help="キーボードでマウス操作をエミュレートするツール", add_completion=False)

DEFAULT_PROFILE_DIR = Path("profiles")


@app.command()
def register(name: str = typer.Argument(..., help="保存するプロファイル名 (拡張子不要)")) -> None:
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
) -> None:
    try:
        emulate_from_profile(Path(profile), base_dir=DEFAULT_PROFILE_DIR)
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
