# VS Code Settings

Makefile を使用して、VS Code と Cursor の設定ファイルを同期し、管理するためのツールです。

`make export-profile` コマンドを使用して、現在のエディタの設定を新しいプロファイルとしてエクスポートします。
`make sync` コマンドを使用して、VS Code と Cursor の設定ファイルを本プロジェクトにある `profile` ディレクトリ内の設定から同期します。

## Dependencies

- `jq`: JSON を操作するためのコマンドラインツール。インストール方法は、[jq の公式サイト](https://stedolan.github.io/jq/download/)を参照してください。
- `make`: Makefile を実行するためのツール。通常は Linux や macOS にプリインストールされていますが、Windows では[Make for Windows](https://www.gnu.org/software/make/)をインストールする必要があります。

※ Windows 環境で実行する場合は、WSL（Windows Subsystem for Linux）や Git Bash などの Unix 互換環境を使用してください。

## Usage

make コマンドを使用して、設定ファイルの操作を行います。以下は主なターゲットです。

### vars

設定ファイルの変数や、実行環境に関する情報を表示します。

```bash
make show-vars
make vars
```

### check-paths

VS Code と Cursor のパスが正しいかをチェックします。

```bash
make check-paths
```

### status

エディタの設定ファイルが正しく同期されているかを確認します。

```bash
make status
```

### dump

現在のエディタの設定を新しいプロファイルとしてエクスポートします。`profile` と `editor` の引数が必要です。
profile は新しいプロファイルの名前、editor は `vscode` または `cursor` を指定します。

```bash
make dump profile=<new-profile-name> editor=<vscode|cursor>
```

### sync

VS Code と Cursor の設定ファイルを本プロジェクトにある `profile` ディレクトリ内の設定から同期します。
どの設定が同期されるかは `make vars` コマンドで確認できます。

```bash
make sync
```

## External Variables

以下の環境変数を設定することで、Makefile の動作をカスタマイズできます。

各種ターゲットを実行する際に `make <command> profile=<profile-name>` のようにプロファイルを指定できます。
コマンドからプロファイルを指定することで、特定のプロファイルに対して操作を行うことができます。
引数を省略した場合は、デフォルトのプロファイルが使用されます。デフォルトのプロファイルは [config.json](config.json) の `default_profile` で指定されています。
