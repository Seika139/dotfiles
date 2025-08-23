# mise による Brew パッケージ管理

このディレクトリは、`mise` を使用して異なる環境の Homebrew パッケージを管理するための設定ファイルを含んでいます。

## ディレクトリ構成

```plain
brew/
├── mise.toml    # miseタスクの定義
├── README.md    # このファイル
└── profiles/    # プロファイル用ディレクトリ
    ├── hm-m1-mac/ # "hm-m1-mac"用のプロファイル
    │   └── Brewfile
    └── another-profile/
        └── Brewfile
```

## 使い方

すべての操作は `mise` タスクとして実行します。

```bash
# 利用可能なタスクを一覧表示
mise tasks

# 設定変数を表示
mise run vars

# デフォルトプロファイルの同期状態を確認
mise run status

# 特定のプロファイルの同期状態を確認
mise run status --profile hm-m1-mac

# デフォルトプロファイルでパッケージを同期
# Brewfileからパッケージをインストールし、手動でインストールされたパッケージをBrewfileに追記します。
mise run sync

# 特定のプロファイルでパッケージを同期
mise run sync --profile hm-m1-mac

# 現在の環境のパッケージを新しいプロファイルとして保存
mise run dump --profile new-profile-name
```

## プロファイル

プロファイル機能により、マシンや目的ごとに異なる Homebrew パッケージのセットを管理できます。各プロファイルは `profiles/` ディレクトリ内のサブディレクトリとして作成され、`Brewfile` を含みます。

デフォルトのプロファイルは `mise.toml` で指定されています。

### 新しいプロファイルの作成

現在の環境から新しいプロファイルを作成するには：

1. 新しいプロファイル名を指定して `dump` タスクを実行します。

   ```bash
   mise run dump --profile my-new-mac
   ```

2. これにより、新しいディレクトリ (`profiles/my-new-mac/`) が作成され、その中に現在インストールされているすべての Homebrew パッケージを含む `Brewfile` が生成されます。

### プロファイルとの同期

特定のプロファイルからすべてのパッケージをインストールするには：

```bash
mise run sync --profile my-new-mac
```

## 設定

以下の環境変数は `mise.toml` の `[env]` セクションで設定できます：

- `PROFILES_DIR`: プロファイルを保存するディレクトリ（デフォルト: `"profiles"`）。
- `BREWFILE_NAME`: パッケージファイルの名前（デフォルト: `"Brewfile"`）。
- `DEFAULT_PROFILE`: プロファイルが指定されなかった場合に使用されるデフォルトのプロファイル名（デフォルト: `"hm-m1-mac"`）。

## 新しいマシンでのセットアップ

1. この dotfiles リポジトリをクローンします。
2. `mise` と `brew` がインストールされていることを確認します。
3. `mise run dump --profile <new-machine-name>` を実行して、新しいマシン用のプロファイルを作成します。
4. または、既存のプロファイルを使用したい場合は、`mise run sync --profile <existing-profile-name>` を実行して、そのプロファイルで定義されているパッケージをインストールします。
