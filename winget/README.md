# mise による Winget パッケージ管理

このディレクトリは、`mise` を使用して異なる環境の Winget パッケージを管理するための設定ファイルを含んでいます。

## ディレクトリ構成

```plain
winget/
├── mise.toml    # miseタスクの定義
├── mise.local.toml # 環境変数設定
├── README.md    # このファイル
└── profiles/    # プロファイル用ディレクトリ
    ├── default-windows/ # デフォルトのプロファイル
    │   ├── package-ids.txt     # アップデート対象のパッケージID一覧
    │   └── winget-export.json  # エクスポートされたパッケージ一覧
    └── another-profile/
        ├── package-ids.txt
        └── winget-export.json
```

## 注意点

`../scoop` や `../brew` ではすべてのインストール済みパッケージをプロファイルに保存していましたが、Winget ではそれを行いません。
Winget で管理しているパッケージには Windows 標準アプリや Microsoft Store アプリも含まれるため、すべてをプロファイルに保存すると膨大な数になってしまうからです。
開発で用いる CLI ツールは優先的に scoop でインストールするようにして、Winget では GUI アプリケーションを中心に管理するようにしています。（一部例外あり）
そこで `package-ids.txt` というファイルを用意し、そこに記載されているパッケージIDのみを `mise update` でアップデートするようにしています。
`winget export` でエクスポートされる `winget-export.json` はあくまでバックアップ用です。 update タスクでは使用しません。

## 使い方

すべての操作は `mise` タスクとして実行します。プロファイルを指定しない場合、`mise.local.toml` で設定されたデフォルトプロファイルが使用されます。

```bash
# 利用可能なタスクを一覧表示
mise tasks

# winget update を実行して、アップデート可能なパッケージを表示
mise run show_update

# デフォルトプロファイルでパッケージをアップデート
mise run update

# 特定のプロファイルでパッケージをアップデート
mise run update --prof other-profile

# 現在の環境のパッケージを新しいプロファイルとして保存
mise run dump new-profile-name
```

## 利用可能なタスク

`mise run <task-name>` で以下のタスクを実行できます。

| Task          | Description                                                                                        |
| :------------ | :------------------------------------------------------------------------------------------------- |
| `show_update` | `winget update` を実行して、アップグレード可能なパッケージを一覧表示します。                       |
| `update`      | プロファイルの `package-ids.txt` に記載されているパッケージをアップデートします。                  |
| `dump`        | 現在インストールされているパッケージをプロファイルに書き出します。 (例: `mise run dump <profile-name>`) |

## プロファイル

プロファイル機能により、マシンや目的ごとに異なる Winget パッケージのセットを管理できます。各プロファイルは `profiles/` ディレクトリ内のサブディレクトリとして作成され、`winget-export.json` と `package-ids.txt` を含みます。

デフォルトのプロファイルは `mise.local.toml` で指定されています。

### 新しいプロファイルの作成

現在の環境から新しいプロファイルを作成するには：

1. 新しいプロファイル名を指定して `dump` タスクを実行します。

   ```bash
   mise run dump my-new-windows
   ```

2. これにより、新しいディレクトリ (`profiles/my-new-windows/`) が作成され、その中に現在インストールされているすべての Winget パッケージを含む `winget-export.json` が生成されます。

3. 必要に応じて `package-ids.txt` を編集し、`mise update` によるアップデート対象としたいパッケージIDを一行ずつ記載します。

### プロファイルでのアップデート

特定のプロファイルからパッケージをアップデートするには：

```bash
mise run update --prof my-new-windows
```

## 設定

以下の環境変数は `mise.local.toml` の `[env]` セクションで設定できます：

- `PROFILES_DIR`: プロファイルを保存するディレクトリ（デフォルト: `"profiles"`）。
- `PACKAGE_IDS`: アップデート対象のパッケージID一覧ファイル名（デフォルト: `"package-ids.txt"`）。
- `EXPORT_JSON`: エクスポートファイルの名前（デフォルト: `"winget-export.json"`）。
- `DEFAULT_PROFILE`: プロファイルが指定されなかった場合に使用されるデフォルトのプロファイル名。

## 新しいマシンでのセットアップ

1. この dotfiles リポジトリをクローンします。
2. `mise` と `winget` がインストールされていることを確認します。
3. `mise run dump <new-machine-name>` を実行して、新しいマシン用のプロファイルを作成します。
4. または、既存のプロファイルを使用したい場合は、`package-ids.txt` に必要なパッケージを記載し、`mise run update --prof <existing-profile-name>` を実行してパッケージをインストールします。
