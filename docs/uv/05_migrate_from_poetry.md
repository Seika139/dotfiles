# poetry から uv への移行

既存の poetry プロジェクトから uv への移行：

- 作業前に `pyproject.toml` と `poetry.lock` のバックアップを推奨します。
- Poetry 特有のバージョン指定（`^3.12.0` など）は PEP 440 準拠表記（`~=3.12.0` 等）に書き換えておくと安全です。

```bash
# 既存の Poetry プロジェクトを uv 形式へマイグレート
uvx migrate-to-uv

# 依存関係を同期して仮想環境を再作成
uv sync
```
