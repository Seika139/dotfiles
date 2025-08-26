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

すべての操作は `mise` タスクとして実行します。プロファイルを指定しない場合、`mise.toml` で設定されたデフォルトプロファイルが使用されます。

```bash
# 利用可能なタスクを一覧表示
mise tasks

# デフォルトプロファイルの同期状態を確認 (簡易版)
mise run status_simple

# 特定のプロファイルの同期状態を確認 (詳細版)
mise run status --prof hm-m1-mac

# デフォルトプロファイルでパッケージを同期 (インストール・アップグレード)
mise run sync

# 特定のプロファイルでパッケージを同期
mise run sync --prof hm-m1-mac

# 現在の環境のパッケージを新しいプロファイルとして保存
mise run dump new-profile-name

# Brewfileにないパッケージの削除 (ドライラン)
mise run prune --prof hm-m1-mac

# Brewfileにないパッケージを実際に削除
mise run prune --prof hm-m1-mac --apply
```

## 利用可能なタスク

`mise run <task-name>` で以下のタスクを実行できます。

| Task            | Description                                                                                             |
| :-------------- | :------------------------------------------------------------------------------------------------------ |
| `status`        | Brewfile に基づき、未インストール/要アップデートのパッケージを一覧表示します。                          |
| `status_simple` | 現在の Brewfile と実際の PC の状態の差分を確認し、差分がある場合は sync を促します（status の簡易版）。 |
| `sync`          | Brewfile に基づいて `install` + `upgrade` を実行します（Brewfile に変更は加えません）。                 |
| `dump`          | 現在インストールされているパッケージをプロファイルに書き出します。 (例: `mise run dump <profile-name>`) |
| `prune`         | Brewfile に無いパッケージをリストアップします。                                                         |
| `prune --apply` | Brewfile に無いパッケージを削除します。**注意して使用してください。**                                   |
| `check`         | (内部用) 指定されたプロファイルが存在するか確認します。                                                 |

## プロファイル

プロファイル機能により、マシンや目的ごとに異なる Homebrew パッケージのセットを管理できます。各プロファイルは `profiles/` ディレクトリ内のサブディレクトリとして作成され、`Brewfile` を含みます。

デフォルトのプロファイルは `mise.toml` で指定されています。

### 新しいプロファイルの作成

現在の環境から新しいプロファイルを作成するには：

1. 新しいプロファイル名を指定して `dump` タスクを実行します。

   ```bash
   mise run dump my-new-mac
   ```

2. これにより、新しいディレクトリ (`profiles/my-new-mac/`) が作成され、その中に現在インストールされているすべての Homebrew パッケージを含む `Brewfile` が生成されます。

### プロファイルとの同期

特定のプロファイルからすべてのパッケージをインストールするには：

```bash
mise run sync --prof my-new-mac
```

## 設定

以下の環境変数は `mise.toml` の `[env]` セクションで設定できます：

- `PROFILES_DIR`: プロファイルを保存するディレクトリ（デフォルト: `"profiles"`）。
- `BREWFILE_NAME`: パッケージファイルの名前（デフォルト: `"Brewfile"`）。
- `DEFAULT_PROFILE`: プロファイルが指定されなかった場合に使用されるデフォルトのプロファイル名（デフォルト: `"hm-m1-mac"`）。

## 新しいマシンでのセットアップ

1. この dotfiles リポジトリをクローンします。
2. `mise` と `brew` がインストールされていることを確認します。
3. `mise run dump <new-machine-name>` を実行して、新しいマシン用のプロファイルを作成します。
4. または、既存のプロファイルを使用したい場合は、`mise run sync --prof <existing-profile-name>` を実行して、そのプロファイルで定義されているパッケージをインストールします。
