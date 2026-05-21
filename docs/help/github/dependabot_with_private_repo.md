# プライベートなリポジトリに依存するプロジェクトで Dependabot を使用する

## 概要

ここではプライベートリポジトリのパッケージを依存関係に持つプロジェクトで Dependabot を使用する方法について説明する。

**目次**

- [プライベートなリポジトリに依存するプロジェクトで Dependabot を使用する](#プライベートなリポジトリに依存するプロジェクトで-dependabot-を使用する)
  - [概要](#概要)
  - [背景](#背景)
  - [GitHub Actions でプライベートリポジトリにアクセスする](#github-actions-でプライベートリポジトリにアクセスする)
    - [PAT を作成する](#pat-を作成する)
      - [最低限必要な権限](#最低限必要な権限)
    - [PAT をシークレットとしてリポジトリに登録する](#pat-をシークレットとしてリポジトリに登録する)
    - [ワークフローの設定例](#ワークフローの設定例)
  - [Dependabot のワークフローでの設定](#dependabot-のワークフローでの設定)
    - [PAT をシークレットとしてリポジトリに登録する](#pat-をシークレットとしてリポジトリに登録する-1)
    - [ワークフローの設定例](#ワークフローの設定例-1)
    - [x-access-token について](#x-access-token-について)

## 背景

Python / UV を使用したプロジェクトが 2 つあるとする。

- `main-project` : 依存関係にプライベートリポジトリ `private-repo` のパッケージ `private-package` を持つ
- `private-repo` : プライベートリポジトリ。パッケージ `private-package` を提供する

`private-repo` は GitHub Packages にパッケージを公開しておらず、`main-project` の `pyproject.toml` では以下のように `private-repo` から直接パッケージをインストールするように指定している。

```toml
[dependencies]
dependencies = [
  "private-package @ git+https://github.com/org-name/private-repo.git@main",
]
```

## GitHub Actions でプライベートリポジトリにアクセスする

ローカルでは `main-project` も `private-repo` も同じ GitHub アカウントでアクセスできるため問題なく依存関係の解決ができる。
しかし、GitHub Actions ワークフローで同様に `uv sync` を実行すると `private-repo` へのアクセスが拒否されてしまい、依存関係の解決に失敗する。
そこで、GitHub Actions のワークフローでは `private-repo` へアクセスするためのトークンを設定し、それをワークフロー内で使用するようにすることで解決する。

### PAT を作成する

まず、以下の手順でパーソナルアクセストークン (PAT) を作成する。

- GitHub で自身のアカウントの Settings を開く
- 左側のメニューの一番下にある Developer settings をクリックする
- 開いた画面の左側のメニューから Personal access tokens > Tokens (classic) を選択する
- Generate new token ボタンをクリックし、Generate new token (classic) を選択する
- するとトークンの設定画面が開くので、以下のように設定する
  - Note : `private-repo-access-token` (任意の名前)
  - Expiration : `No expiration`
  - 適切な権限を設定する。最低限必要な権限については後述。
- Generate token ボタンをクリックする
- 表示されているトークンをコピーする (この画面を閉じると再度表示できないので注意)

#### 最低限必要な権限

最低限必要な権限はリポジトリの内容を読み取るためのスコープである。
GitHub の PAT には Fine-grained token と Classic token の 2 種類があるので、それぞれの場合について説明する。

**Fine-grained token を利用する場合**

- Repository permissions のプルダウンをクリックして展開する
- その中にある `Contents` のアクセス権を `Read-only` に設定する

**Classic token を利用する場合**

- Scopes セクションで `repo` にチェックを入れる

### PAT をシークレットとしてリポジトリに登録する

次に、作成したトークンを `main-project` のリポジトリのシークレットとして登録する。

- `main-project` の GitHub リポジトリを開く
- 画面上部のメニューから Settings をクリックする
- 左側のメニューから Secrets and variables > Actions を選択する
- New repository secret ボタンをクリックする
- 以下のように設定して Add secret ボタンをクリックする
  - Name : `PRIVATE_REPO_ACCESS_TOKEN`（任意の名前）
  - Value : 先ほどコピーしたトークン

これで GitHub Actions ワークフローから `private-repo` へアクセスする準備が整った。

### ワークフローの設定例

以下は `main-project` の GitHub Actions ワークフローの例である。

```yaml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Configure git auth
        run: |
          git config --global url."https://${PRIVATE_REPO_ACCESS_TOKEN}:x-oauth-basic@github.com/".insteadOf "https://github.com/"
        env:
          PRIVATE_REPO_ACCESS_TOKEN: ${{ secrets.PRIVATE_REPO_ACCESS_TOKEN }}

      - name: Set up UV
        uses: astral-sh/setup-uv@v7
        with:
          version: "0.9.22" # UV のバージョンを指定
          python-version: ${{ inputs.python-version || '3.13' }} # Python のバージョンを指定

      - name: Sync dependencies
        if: steps.changed-files.outputs.any_changed == 'true'
        run: uv sync --frozen --all-extras

      - name: Run ruff check
        run: uv run ruff check . # Ruff を使用したコードチェック

      - name: Run tests
        run: uv run pytest tests/ # pytest を使用したテスト実行
```

Configure git auth ステップで `private-repo` へアクセスするための認証情報を設定している。
依存関係の解決をするよりも前に `git config` コマンドで `private-repo` へのアクセスにトークンを使用するように設定しているのがポイントだ。

以上のように設定することで、`main-project` のワークフロー内で `uv sync` を実行した際に `private-repo` へアクセスできるようになる。

## Dependabot のワークフローでの設定

`.github/dependabot.yml` による Dependabot version updates を有効化している場合、Dependabot のワークフローでも同様にプライベートリポジトリへアクセスするための設定が必要になる。

### PAT をシークレットとしてリポジトリに登録する

Dependabot のワークフローで使用するトークンは GitHub Actions ワークフローとは別で設定する必要がある。
トークンは先程作成した PAT を流用してもよいし、新たに作成してもよい。

`main-project` リポジトリにて以下の手順でトークンをシークレットとして登録する。

- `main-project` の GitHub リポジトリを開く
- 画面上部のメニューから Settings をクリックする
- 左側のメニューから Secrets and variables > Dependabot を選択する
- New repository secret ボタンをクリックする
- 以下のように設定して Add secret ボタンをクリックする
  - Name : `PRIVATE_REPO_ACCESS_TOKEN`（任意の名前）
  - Value : 先ほどコピーしたトークン

### ワークフローの設定例

以下は `main-project` の Dependabot version updates の設定例である。
この例では UV の依存関係を更新する設定をしている。

```yaml
version: 2

registries:
  github-private:
    type: git
    url: https://github.com
    username: x-access-token
    password: ${{secrets.PRIVATE_REPO_ACCESS_TOKEN}}

updates:
  - package-ecosystem: "uv"
    directory: "/"
    registries:
      - github-private
    schedule:
      interval: "daily"
      time: "13:30"
      timezone: "Asia/Tokyo"
    groups:
      all:
        patterns:
          - "*"
    cooldown:
      default-days: 7
```

`registries` セクションでプライベートリポジトリにアクセスするための認証情報を設定している。
`username` には `x-access-token` を指定し、`password` には先程登録したシークレットを指定しているのがポイントだ。

以上のように設定することで、Dependabot のワークフロー内で `uv` の依存関係を更新する際にプライベートリポジトリへアクセスできるようになる。

### x-access-token について

GitHub で HTTPS 経由でリポジトリにアクセスするには、ユーザー名とパスワード (またはトークン) を使用する必要がある。

```bash
git clone https://<USERNAME>:<PASSWORD>@github.com/org-name/private-repo.git # パスワードを使用する場合
git clone https://<USERNAME>:<TOKEN>@github.com/org-name/private-repo.git # トークンを使用する場合
```

ここで、トークンを使用する場合の `<USERNAME>` には `x-access-token` を指定するのが GitHub の慣例となっている。
実際の GitHub ユーザー名を使わないことで、トークンベースの認証であることが明確になり、ログや監査で識別しやすくなる。
