# uv

以前よく使っていた [Python](../../python/) 関連の情報は古くなってしまった。
最近は poetry の代わりに uv を使っているし、 uv と同じ会社が提供している ruff を black と isort の代わりに使っている。

## インストール方法

```bash
# Mac
curl -LsSf https://astral.sh/uv/install.sh | sh
# その後 ~/.local/bin が PATH に入っていることを確認する

# Devcontainer
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

## 基本的な使い方

### プロジェクトの作成

```bash
# 新しいプロジェクトを作成
uv init my-project
cd my-project

# 既存のプロジェクトでuvを使用開始
uv init --existing
```

### 依存関係の管理

--dev は実質 --group dev のショートカットで、dev グループは特別扱い（デフォルトで sync 対象）されます。
fastapi は実行時依存なのでフラグ不要、pytest は開発依存なので基本は --dev、
テスト専用に分けたいなら --group test を使い分ける、というのが公式推奨です。

• 実行時依存（runtime）: フラグなし
• 開発依存（dev）: --dev（≒--group dev）
• 特定用途グループ: --group <name>

```bash
# パッケージの追加
uv add requests
uv add fastapi --dev
uv add pytest --group test

# パッケージの削除
uv remove requests

# 依存関係のインストール
uv sync

# 依存関係の更新
uv update
```

### 仮想環境の管理

```bash
# 仮想環境の作成とアクティベート
uv venv
source .venv/bin/activate  # Linux/Mac
# Windows: .venv\Scripts\activate

# 特定のPythonバージョンで仮想環境を作成
uv venv --python 3.11
# 併せて pyproject.toml の [project] に Python 要件を明示しておくと良い:
# requires-python = ">=3.11"
```

### スクリプトの実行

```bash
# 仮想環境内でスクリプトを実行
uv run python script.py

# 依存関係を自動でインストールして実行
uv run --with requests python script.py

# 特定のPythonバージョンで実行
uv run --python 3.11 python script.py
```

### パッケージのインストール

`uv pip install --system` はシステム環境を汚しやすいから、CLI ツールは `uv tool` / 一発実行は `uvx` を推したい

```bash
# グローバルにパッケージをインストール
uv pip install --system requests

# 特定のバージョンをインストール
uv pip install --system requests==2.31.0

# パッケージのアンインストール
uv pip uninstall --system requests

# CLIツールのインストール（グローバル）
uv tool install ruff
# 一時実行（インストール不要）
uvx ruff --version
# ライブラリを使ったワンライナー実行例（from指定）
uvx --from requests python -c "import requests,sys;print(requests.__version__)"
```

### プロジェクトの設定

`pyproject.toml`ファイルでプロジェクトの設定を行います：

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "A sample project"
dependencies = [
    "requests>=2.31.0",
    "fastapi>=0.100.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "ruff>=0.5.0",
]
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 開発ツールとの連携

```bash
# pre-commitフックの設定
uv add --dev pre-commit

# 開発用依存関係のインストール
uv sync --group dev

# テスト用依存関係のインストール
uv sync --group test
```

### パフォーマンスの利点

uv は以下の点で高速です：

- **依存関係の解決**: 並列処理による高速な依存関係解決
- **パッケージのインストール**: 効率的なキャッシュシステム
- **仮想環境の作成**: 最適化された環境構築
- **ロックファイル**: 再現可能なビルド

### よく使うコマンド一覧

```bash
# プロジェクト管理
uv init [project-name]     # プロジェクトの初期化
uv sync                    # 依存関係の同期
uv lock                    # ロックファイルの生成

# パッケージ管理
uv add <package>           # パッケージの追加
uv remove <package>        # パッケージの削除
uv update                  # 依存関係の更新

# 仮想環境
uv venv                    # 仮想環境の作成
uv run <command>           # 仮想環境内でコマンド実行

# パッケージインストール
uv pip install <package>   # パッケージのインストール
uv pip uninstall <package> # パッケージのアンインストール

# ヘルプ
uv --help                  # 全体的なヘルプ
uv <command> --help        # 特定コマンドのヘルプ
```

## poetry からの移行

既存の poetry プロジェクトから uv への移行：

- 作業前に `pyproject.toml` と `poetry.lock` のバックアップを推奨します。
- Poetry 特有のバージョン指定（`^3.12.0` など）は PEP 440 準拠表記（`~=3.12.0` 等）に書き換えておくと安全です。

```bash
# 既存の Poetry プロジェクトを uv 形式へマイグレート
uvx migrate-to-uv

# 依存関係を同期して仮想環境を再作成
uv sync
```

## 参考リンク

- [公式ドキュメント](https://docs.astral.sh/uv/)
- [GitHub リポジトリ](https://github.com/astral-sh/uv)
- [Python パッケージ管理の新時代 - uv](https://zenn.dev/ryo_kawamata/articles/python-package-management-uv)
