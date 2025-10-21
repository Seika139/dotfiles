# uv の基本的な使い方

以前よく使っていた [Python](../../python/) 関連の情報は古くなってしまった。
最近は poetry の代わりに uv を使っているし、 uv と同じ会社が提供している ruff を black と isort の代わりに使っている。

uv は以下の点で高速なので、2025年現在非常に推奨される Python 環境管理ツールです。

- **依存関係の解決**: 並列処理による高速な依存関係解決
- **パッケージのインストール**: 効率的なキャッシュシステム
- **仮想環境の作成**: 最適化された環境構築
- **ロックファイル**: 再現可能なビルド

公式情報 : <https://docs.astral.sh/uv/getting-started/features/>

## Python 自体のインストールと管理

- `uv python install`: Python バージョンをインストールします。
- `uv python list`: 利用可能な Python バージョンを表示します。
- `uv python find`: インストールされている Python バージョンを見つけます。
- `uv python pin`: 特定の Python バージョンを使用するために現在のプロジェクトをピン留めします。
- `uv python uninstall`: Python バージョンをアンインストールします。

## スクリプト

スタンドアロンのスクリプトを実行します。

- `uv run`: スクリプトを実行します。
- `uv add --script`: スクリプトに依存関係を追加します。
- `uv remove --script`: スクリプトから依存関係を削除します。

`uv run` を頭につけることで、スクリプトを uv の管理する仮想環境内で実行します。

```bash
# uvの仮想環境内で main.py を実行
uv run python main.py

# uvの仮想環境内で main.py を実行 （.py拡張子がある場合はそれをPythonコマンドとして解釈）
uv run main.py

# 仮想環境で実行可能なコマンドを実行
uv run ruff format .

# 依存関係を自動でインストールして実行
uv run --with requests python main.py

# 特定のPythonバージョンで実行
uv run --python 3.11 python main.py

# コマンドライン引数を利用して実行
uv run python -c "import sys; print(sys.version)"

# 標準入力からの実行（echo の出力が python の標準入力に渡されてスクリプトとして解釈・実行される）
echo "import sys; print(sys.version)" | uv run -

# モジュールとしての実行（-m または --module フラグを利用）
uv run -m http.server 8880
```

※ 参考: [uv run 徹底解説](https://zenn.dev/tkithrta/articles/e89a79a9e91637)

## プロジェクトの管理

これらのコマンドは Python プロジェクトを uv で管理するために使用されます。コマンドの実行結果が `pyproject.toml` や `uv.lock` に反映されます。

- `uv init`: 新しい Python プロジェクトを作成します。
- `uv add`: プロジェクトに依存関係を追加します。
- `uv remove`: プロジェクトから依存関係を削除します。
- `uv sync`: プロジェクトの依存関係を環境と同期します。
- `uv lock`: プロジェクトの依存関係のロックファイルを作成します。
- `uv run`: プロジェクト環境でコマンドを実行します。
- `uv tree`: プロジェクトの依存関係ツリーを表示します。

※ `uv add` や `uv remove` では `--dev` や `--group <name>`, `--optional <name>` などのオプションを使って依存関係の種類を指定できます。依存関係の種類については [pyproject.toml で依存関係を管理する](04_managing_dependencies.md) を参照してください。

## ツール

Python パッケージインデックスに公開された CLI ツールを利用します。

- `uv tool run / uvx`: 一時環境で CLI ツールを実行します。これはツールをインストールせずに使用できます。 `uvx` は `uv tool run` のエイリアスです。
- `uv tool install`: CLI ツールをユーザー全体にインストールします。
- `uv tool uninstall`: CLI ツールをアンインストールします。
- `uv tool list`: インストールされている CLI ツールを表示します。
- `uv tool update-shell`: ツールの実行可能ファイルを含めるようにシェルを更新します。

## pip interface

環境とパッケージを手動で管理します。従来のワークフローや、高レベルのコマンドでは十分な制御ができない場合に使用することを目的としています。

### 仮想環境の作成（venv, virtualenv 相当）

- `uv venv`: 新しい仮想環境を作成します。詳細については、[仮想環境の使用に関するドキュメント](https://docs.astral.sh/uv/pip/environments/#using-a-virtual-environment) を参照してください。
- `uv venv --python <version>`: 特定の Python バージョンで仮想環境を作成します。

仮想環境の有効化と無効化は、通常の Python 仮想環境と同様に行います。

```bash
# 仮想環境の有効化 (Linux/Mac)
source .venv/bin/activate

# 仮想環境の有効化 (Windows)
.venv\Scripts\activate

# 仮想環境の無効化
deactivate
```

仮想環境を有効化すると、uv run を使用しなくても python が仮想環境内のものを指すようになります。

### 例（このディレクトリで実行可能です）

このディレクトリの `main.py` を実行して、実際に仮想環境の Python が使われていることを確認します。

仮想環境を有効化する前の状態では、`uv run` を使って仮想環境内でスクリプトを実行していることがわかります。

```bash
$ uv run main.py
Python Version: 3.9.1
Python Prefix : ~/dotfiles/docs/uv/.venv

$ py main.py
Python Version: 3.12.7
Python Prefix : ~/AppData/Local/Programs/Python/Python312

$ python main.py
Python Version: 3.12.7
Python Prefix : ~/AppData/Local/Programs/Python/Python312
```

仮想環境を有効化した後では、`uv run` を使わなくても仮想環境内でスクリプトを実行できるようになります。

```bash
$ uv venv # 仮想環境を作成
Using CPython 3.9.1 interpreter at: ~/AppData/Local/Programs/Python/Python39/python.exe
Creating virtual environment at: .venv
✔ A virtual environment already exists at `.venv`. Do you want to replace it? · yes
Activate with: source .venv/Scripts/activate

$ source .venv/Scripts/activate # 仮想環境を有効化

(uv) $ uv run main.py
Python Version: 3.9.1
Python Prefix : ~/dotfiles/docs/uv/.venv

(uv) $ py main.py
Python Version: 3.9.1
Python Prefix : ~/dotfiles/docs/uv/.venv

(uv) $ python main.py
Python Version: 3.9.1
Python Prefix : ~/dotfiles/docs/uv/.venv

(uv) $ deactivate # 仮想環境を無効化
```

### 仮想環境内のパッケージの管理 (pip, pipdeptree 相当)

- `uv pip install`: 現在の環境にパッケージをインストールします。
- `uv pip show`: インストールされたパッケージの詳細を表示します。
- `uv pip freeze`: インストールされているパッケージとそのバージョンを一覧表示します。
- `uv pip check`: 現在の環境に互換性のあるパッケージがあることを確認します。
- `uv pip list`: インストールされているパッケージを一覧表示します。
- `uv pip uninstall`: パッケージをアンインストールします。
- `uv pip tree`: 環境の依存関係ツリーを表示します。

詳細については、[パッケージの管理に関するドキュメント](https://docs.astral.sh/uv/pip/packages/#installing-packages-from-files) を参照してください。

## 開発ツールとの連携

```bash
# pre-commitフックの設定
uv add --dev pre-commit
```
