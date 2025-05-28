# Dev Containers を使って Python 開発環境を構築する方法

Dev Containers を使うと、Docker コンテナ内で Python 開発環境を簡単にセットアップできます。
poetry と Python が用意された Dev Container を使います。
Dev Container 自体のセットアップ方法は [dev_containers.md](dev_containers.md) を参照してください。

## 元々あると良いファイル

```plain
.devcontainer/
├── devcontainer.json
└── Dockerfile
.github/
└── copilot-instructions.md
src/
.editorconfig
.gitattributes
.gitignore
CHANGELOG.md
DEVELOPMENT.md
LICENSE
Makefile
README.md
```

## poetry プロジェクトを作成する

### pyproject.toml を作成する

Dev Container 内でターミナルを開きます。

```bash
# プロジェクトのルートディレクトリに移動します。
cd /workspaces/my_project

# poetry プロジェクトを初期化します。
poetry init
```

### すでにあるプロジェクトを使う場合

すでに `pyproject.toml` がある場合は、以下のコマンドで依存関係をインストールします。

```bash
# プロジェクトのルートディレクトリに移動します。
cd /workspaces/my_project
# 依存関係をインストールします。
poetry install
```

## src レイアウトの使用

src レイアウトは、プロジェクトのソースコードを src ディレクトリの下に配置するパターンです。この方法には以下のメリットがあります：

- テストコードとソースコードを明確に分離できる
- パッケージのインポート時に意図しないローカルディレクトリからのインポートを防げる
- パッケージを開発中にもインストール時と同じようにインポートできる

### ディレクトリ構造

```plain
my_project/
├── src/
│   └── my_package/
│       ├── __init__.py
│       ├── core.py
│       └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   └── test_utils.py
├── pyproject.toml
└── README.md
```

### pyproject.toml の設定

src レイアウトを使用する場合、`pyproject.toml` に以下のように `packages` を設定します：

```toml
[project]
name = "プロジェクト名"
version = "0.1.0"

[tool.poetry]
packages = [{include = "my_package", from = "src"}]

[tool.poetry.dependencies]
python = "^3.11"
# その他の依存関係
```

この設定により、`src/my_package` がパッケージとして認識され、`poetry install` 実行時に適切にインストールされます。
