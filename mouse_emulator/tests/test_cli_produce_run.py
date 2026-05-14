"""`auto-emulator produce-run` CLI の非対話エラーパステスト。

実機キャリブが必要な正常系は単体テストでは扱わず、template ディレクトリ
未存在等のエラー終了経路だけを覆う。
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from auto_emulator.cli import app

runner = CliRunner()


def test_command_registered() -> None:
    result = runner.invoke(app, ["produce-run", "--help"])
    assert result.exit_code == 0
    assert "produce" in result.stdout.lower()


def test_missing_templates_dir_exits_with_error(tmp_path: Path) -> None:
    missing = tmp_path / "no_such_dir"
    result = runner.invoke(
        app,
        ["produce-run", "--templates-dir", str(missing), "--no-calibrate"],
    )
    assert result.exit_code == 1
    assert "テンプレディレクトリが見つかりません" in result.stdout


def test_empty_templates_dir_exits_with_error(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = runner.invoke(
        app,
        ["produce-run", "--templates-dir", str(empty), "--no-calibrate"],
    )
    assert result.exit_code == 1
    assert "1 件もロードできませんでした" in result.stdout
