# VS Code Settings

mise を使用して、VS Code と Cursor の設定ファイルを同期し、管理するためのツールです。

`mise run dump` コマンドを使用して、現在のエディタの設定を新しいプロファイルとしてエクスポートします。
`mise run sync` コマンドを使用して、VS Code と Cursor の設定ファイルを本プロジェクトにある `profile` ディレクトリ内の設定から同期します。

## Dependencies

- `mise`: タスクランナー。インストール方法は、[mise の公式サイト](https://mise.jdx.dev/getting-started.html)を参照してください。
- `bash`: Unix シェル。通常は Linux や macOS にプリインストールされていますが、Windows では WSL（Windows Subsystem for Linux）や Git Bash などの Unix 互換環境を使用してください。

## Usage

`mise run` コマンドを使用して、設定ファイルの操作を行います。以下は主なタスクです。

### vars

設定ファイルの変数や、実行環境に関する情報を表示します。

```bash
mise run vars
```

### status

エディタの設定ファイルが正しく同期されているかを確認します。

```bash
mise run status
```

### dump

現在のエディタの設定を新しいプロファイルとしてエクスポートします。`editor` の引数が必要です。
editor は `vscode` または `cursor` を指定します。

```bash
mise run dump <vscode|cursor>
```

### sync

VS Code と Cursor の設定ファイルを本プロジェクトにある `profile` ディレクトリ内の設定から同期します。
どの設定が同期されるかは `mise run vars` コマンドで確認できます。

```bash
mise run sync
```

## External Variables

各種ターゲットを実行する際に `mise run <task> -- --prof=<profile-name>` のようにプロファイルを指定できます。
コマンドからプロファイルを指定することで、特定のプロファイルに対して操作を行うことができます。
引数を省略した場合は、デフォルトのプロファイルが使用されます。デフォルトのプロファイルは `.env` ファイルの `DEFAULT_PROFILE` で指定されています。
