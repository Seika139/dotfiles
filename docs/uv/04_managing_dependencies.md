# pyproject.toml で依存関係を管理する

`pyproject.toml` はプロジェクトのメタデータと依存関係を管理するためのファイルです。
ここでは依存関係について説明します。

- 公式ページ: <https://docs.astral.sh/uv/concepts/projects/dependencies/>

## 依存関係の種類

プロジェクトの依存関係はいくつかのフィールドで定義されます。

- `project.dependencies`: パッケージとして公開する際に必要な依存関係。
- `project.optional-dependencies`: パッケージとして公開した際にオプションでインストール可能な依存関係グループ。
- `dependency-groups`: 開発用のローカル依存関係。
- `tool.uv.sources`: pip などからインストールできない依存関係（自作のパッケージや、プロジェクト内のモジュールなど）。

後述のオプションを使用してフィールドを指定します。

### project.dependencies

何も指定しない場合、依存関係は `project.dependencies` に追加・削除されます。

```bash
$ uv add numpy
$ uv remove numpy
$ uv sync
```

### project.optional-dependencies

`optional-dependencies` に依存関係を追加・削除するには、 `--optional` フラグを使用します。

```toml
[project.optional-dependencies]
data = [
    "inherit-docstring",
]
```

```bash
$ uv add --optional data inherit-docstring
$ uv remove --optional data inherit-docstring
$ uv sync --extra data # optional-dependencies.data を追加で同期します
$ uv sync --all-extras # すべての optional-dependencies グループを同期します
```

### dependency-groups

dependency-groups は PEP-735 で提案された比較的新しいフィールドで、 uv 以外のツールではサポートされていない場合があります。
このフィールドはパッケージのメタデータとして公開しない、開発用の依存関係グループを定義します。

```toml
[dependency-groups]
ci = [
    "pytest",
]
```

```bash
$ uv add --group ci pytest
$ uv remove --group ci pytest
$ uv sync --group ci # project.dependencies と dependency-groups.ci を同期します
$ uv sync --only-group ci # dependency-groups.ci のみを同期します
$ uv sync --no-group ci # dependency-groups.ci を除外して同期します
```

### dependency-groups.dev

`dev` は特別なグループ名で、 uv のデフォルト設定では常に同期されます。

```toml
[dependency-groups]
dev = [
    "pytest",
]
```

```bash
$ uv add --dev pytest # --group dev と同義
$ uv remove --dev pytest # --group dev と同義
$ uv sync # dev グループはデフォルトで同期されます
$ uv sync --only-dev # dev グループのみを同期します
$ uv sync --no-dev # dev グループを除外して同期します
```

#### 依存関係のネスト

以下ののように、dependency-groups 内で他のグループを参照することも可能です。

```toml
[dependency-groups]
dev = [
  {include-group = "lint"},
  {include-group = "test"}
]
lint = [
  "ruff"
]
test = [
  "pytest"
]
```

#### デフォルトで同期するグループの設定

以下のように `tool.uv.default-groups` セクションでデフォルトグループを変更することも可能です。

```toml
[tool.uv]
default-groups = ["dev", "foo"]
```

すべての依存関係をデフォルトで有効にする場合は配列にしないで以下のように指定します

```toml
[tool.uv]
default-groups = "all"
```

#### Legacy な dev-dependencies との互換性

`dependency-groups` が標準化される前、uv は `tool.uv.dev-dependencies` フィールドを使用して開発の依存関係を指定していました。
このフィールドは現在もサポートされていますが、将来的には削除される予定です。

### tool.uv.sources

このフィールドは pip などからインストールできない依存関係（自作のパッケージや、プロジェクト内のモジュールなど）を指定するために使用します。

以下で紹介するような指定が可能です。

詳細は: <https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-sources>

```toml
[tool.uv.sources]
my_package = {path = "./my_package"} # ローカルの my_package ディレクトリを参照
httpx = { git = "https://github.com/encode/httpx" } # GitHub リポジトリを参照
httpx = { git = "https://github.com/encode/httpx", branch = "main" } # 特定のブランチを参照
httpx = { git = "https://github.com/encode/httpx", tag = "0.27.0" } # 特定のタグを参照
httpx = { git = "https://github.com/encode/httpx", rev = "326b9431c761e1ef1e00b9f760d1f654c8db48c6" } # 特定のコミットを参照
httpx = { url = "https://files.pythonhosted.org/packages/5c/2d/3da5bdf4408b8b2800061c339f240c1802f2e82d55e50bd39c5a881f47f0/httpx-0.27.0.tar.gz" } # 直接 URL を参照（.whl や .tar.gz または .zip などで終わる URL）
```

```bash
$ uv add /example/foo-0.1.0-py3-none-any.whl # ローカルのファイルを追加
$ uv add git+https://github.com/encode/httpx # GitHub リポジトリを追加
$ uv add git+https://github.com/encode/httpx --branch main # 特定のブランチを追加
$ uv add git+https://github.com/encode/httpx --tag 0.27.0 # 特定のタグを追加
$ uv add git+https://github.com/encode/httpx --rev 326b9431c761e1ef1e00b9f760d1f654c8db48c6 # 特定のコミットを追加
uv add "https://files.pythonhosted.org/packages/5c/2d/3da5bdf4408b8b2800061c339f240c1802f2e82d55e50bd39c5a881f47f0/httpx-0.27.0.tar.gz" # 直接 URL を追加
```

## 依存関係指定子

uv は　[PEP-508](https://peps.python.org/pep-0508/) に準拠した依存関係指定子をサポートしています。

例

```toml
[project]
dependencies = [
    "pandas==1.3.5",         # 固定バージョン
    "numpy>=1.21.0,<2.0.0",  # バージョン範囲指定
    "numpy~=1.21",           # 明示されている最後の桁が変わらない範囲(1.21.x)
    "numpy~=1",              # 明示されている最後の桁が変わらない範囲（1.x.x）
    "requests==2.25.*",      # ワイルドカード指定（2.25.x の任意のバージョン）
]
