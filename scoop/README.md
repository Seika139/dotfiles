# mise による Scoop パッケージ管理

このディレクトリは、`mise` を使用して異なる環境の Scoop パッケージを管理するための設定ファイルを含んでいます。

## ディレクトリ構成

```plain
scoop/
├── mise.toml    # miseタスクの定義
├── mise.local.toml # 環境変数設定
├── README.md    # このファイル
└── profiles/    # プロファイル用ディレクトリ
    ├── default-windows/ # デフォルトのプロファイル
    │   └── scoop-export.json
    └── another-profile/
        └── scoop-export.json
```

## 使い方

すべての操作は `mise` タスクとして実行します。プロファイルを指定しない場合、`mise.local.toml` で設定されたデフォルトプロファイルが使用されます。

```bash
# 利用可能なタスクを一覧表示
mise tasks

# デフォルトプロファイルの同期状態を確認
mise run status

# 特定のプロファイルの同期状態を確認
mise run status --prof other-profile

# デフォルトプロファイルでパッケージを同期 (インストール・アップグレード)
mise run sync

# 特定のプロファイルでパッケージを同期
mise run sync --prof other-profile

# 現在の環境のパッケージを新しいプロファイルとして保存
mise run dump new-profile-name

# プロファイルにないパッケージの削除 (ドライラン)
mise run prune

# プロファイルにないパッケージを実際に削除
mise run prune --apply
```

## 利用可能なタスク

`mise run <task-name>` で以下のタスクを実行できます。

| Task            | Description                                                                                             |
| :-------------- | :------------------------------------------------------------------------------------------------------ |
| `status`        | 未インストール/要アップデートのパッケージを一覧表示します。                                             |
| `sync`          | プロファイルに基づいてパッケージのインストールとアップグレードを実行します。                            |
| `dump`          | 現在インストールされているパッケージをプロファイルに書き出します。 (例: `mise run dump <profile-name>`) |
| `prune`         | プロファイルに無いパッケージをリストアップします。                                                      |
| `prune --apply` | プロファイルに無いパッケージを削除します。**注意して使用してください。**                                |

※ `status` は要対応時に終了コード `1` を返します。

## プロファイル

プロファイル機能により、マシンや目的ごとに異なる Scoop パッケージのセットを管理できます。各プロファイルは `profiles/` ディレクトリ内のサブディレクトリとして作成され、`scoop-export.json` を含みます。

デフォルトのプロファイルは `mise.local.toml` で指定されています。

### 新しいプロファイルの作成

現在の環境から新しいプロファイルを作成するには：

1. 新しいプロファイル名を指定して `dump` タスクを実行します。

   ```bash
   mise run dump my-new-windows
   ```

2. これにより、新しいディレクトリ (`profiles/my-new-windows/`) が作成され、その中に現在インストールされているすべての Scoop パッケージを含む `scoop-export.json` が生成されます。

### プロファイルとの同期

特定のプロファイルからすべてのパッケージをインストールするには：

```bash
mise run sync --prof my-new-windows
```

## 設定

以下の環境変数は `mise.local.toml` の `[env]` セクションで設定できます：

- `PROFILES_DIR`: プロファイルを保存するディレクトリ（デフォルト: `"profiles"`）。
- `EXPORT_FILENAME`: エクスポートファイルの名前（デフォルト: `"scoop-export.json"`）。
- `DEFAULT_PROFILE`: プロファイルが指定されなかった場合に使用されるデフォルトのプロファイル名。

## 新しいマシンでのセットアップ

1. この dotfiles リポジトリをクローンします。
2. `mise` と `scoop` がインストールされていることを確認します。
3. `mise run dump <new-machine-name>` を実行して、新しいマシン用のプロファイルを作成します。
4. または、既存のプロファイルを使用したい場合は、`mise run sync --prof <existing-profile-name>` を実行して、そのプロファイルで定義されているパッケージをインストールします。
