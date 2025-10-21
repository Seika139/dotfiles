# Project 内で uv を活用する

## プロジェクトの作成

- 新しいプロジェクトを uv で初期化するには、以下のコマンドを使用します：

```bash
# my-project という名前の新しいプロジェクトを作成（ディレクトリも作成されます）
uv init my-project
cd my-project

# 既存のプロジェクトで uv を使用開始する場合（カレントディレクトリに uv 管理ファイルを作成します）
uv init
```

このコマンドを実行すると以下のファイルが生成されます（存在する場合は上書きされません）

```plain
my-project/
├── .gitignore
├── .python-version
├── README.md
├── main.py
└── pyproject.toml
```

さらに、`uv run`, `uv sync`, `uv lock` などのプロジェクトに関するコマンドを初回実行すると

- `.venv/`（仮想環境ディレクトリ）
- `uv.lock`（依存関係ロックファイル）

が生成されます。

## pyproject.toml

プロジェクトのメタデータと依存関係を管理するためのファイルです。uv init 実行直後では以下のような情報が含まれます。

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "A sample project using uv"
readme = "README.md"
dependencies = []
```

readme フィールドはプロジェクトの説明を含むファイルを指定します。`README.md` が一般的です。
ここで指定したファイルが存在しないとビルド時にエラーになるので注意してください。

## .python-version

プロジェクトのデフォルトの Python バージョンを指定するためのファイルです。
プロジェクトの仮想環境を作成する際に uv はこのファイルを参照して仮想環境を作成します。

```plain
3.12
```

### requires-python の設定

`pyproject.toml` の `[project]` セクション内に `requires-python` フィールドを追加して Python バージョン要件を指定することもできますが、`.python-version` とは立ち位置が異なるため両方設定しておくことを推奨します。

```toml
[project]
requires-python = ">=3.12"
```

requires-python は **「このプロジェクトが動作可能な Python のバージョン範囲」**を、パッケージのメタデータとして宣言するもので、 pip や uv が依存関係の解決時に参照します。

例えば以下のような場合…

```toml
[project]
requires-python = ">=3.10,<3.13"
```

```plain
3.12.6
```

開発環境には 3.12.6 が使用されますが、パッケージは 3.10 から 3.12 までのバージョンで動作可能であることを示しています。

## uv.lock

プロジェクトの依存関係に関する正確な情報を含むクロスプラットフォームのロックファイルです。
uv sync や uv lock コマンドを実行すると自動的に生成・更新されます。手動で編集してはいけません。

### uv lock

- `uv lock` : `uv.lock` を明示的に生成・更新します。
- `uv lock --check` : 依存関係がロックファイルと一致しているか確認します。
- `uv lock --upgrade` : lock ファイルの依存関係を最新バージョンに更新します。
- `uv lock --upgrade-package <package>` : 指定したパッケージのみを最新バージョンに更新します。

#### Dockerfile などで世話になるオプション

- `--frozen` : 通常はロックファイルが最新でない場合に uv はエラーを発生させますが、このオプションを指定するとロックファイルが最新でない場合でもエラーを発生させずに処理を続行します。

### uv sync

- `uv sync` : プロジェクト環境を明示的に同期します。（ロックファイルに基づいて uv の仮想環境を更新します）
- `uv sync --dry-run` : 実際には変更を加えずに、同期によって行われる変更を表示します。
- `uv sync --inexact` : ロックファイルに存在しないパッケージを削除したくない場合に使用します。

※ `uv sync` で同期する依存関係の種類については [pyproject.toml で依存関係を管理する](04_managing_dependencies.md) を参照してください。

#### Dockerfile などで世話になるオプション

- `--frozen` : 通常はロックファイルが最新でない場合に uv はエラーを発生させますが、このオプションを指定するとロックファイルが最新でない場合でもエラーを発生させずに処理を続行します。
- `--no-install-project` : 現在のプロジェクトをインストールしないようにします。
