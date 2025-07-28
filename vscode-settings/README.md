# VS Code Settings

Makefileを使用して、VS CodeとCursorの設定ファイルを同期し、管理するためのツールです。

`make export-profile` コマンドを使用して、現在のエディタの設定を新しいプロファイルとしてエクスポートします。
`make sync` コマンドを使用して、VS CodeとCursorの設定ファイルを本プロジェクトにある `profile` ディレクトリ内の設定から同期します。

## Dependencies

- `jq`: JSONを操作するためのコマンドラインツール。インストール方法は、[jqの公式サイト](https://stedolan.github.io/jq/download/)を参照してください。
- `make`: Makefileを実行するためのツール。通常はLinuxやmacOSにプリインストールされていますが、Windowsでは[Make for Windows](https://www.gnu.org/software/make/)をインストールする必要があります。

※ Windows環境で実行する場合は、WSL（Windows Subsystem for Linux）や Git BashなどのUnix互換環境を使用してください。

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

### export-profile

現在のエディタの設定を新しいプロファイルとしてエクスポートします。`profile` と `editor` の引数が必要です。

```bash
make export-profile profile=<new-profile-name> editor=<vscode|cursor>
```

### sync

VS Code と Cursor の設定ファイルを本プロジェクトにある `profile` ディレクトリ内の設定から同期します。
どの設定が同期されるかは `make vars` コマンドで確認できます。

```bash
make sync
```

## External Variables

以下の環境変数を設定することで、Makefileの動作をカスタマイズできます。

各種ターゲットを実行する際に `make <command> profile=<profile-name>` のようにプロファイルを指定できます。
コマンドからプロファイルを指定することで、特定のプロファイルに対して操作を行うことができます。
引数を省略した場合は、デフォルトのプロファイルが使用されます。デフォルトのプロファイルは [config.json](config.json) の `default_profile` で指定されています。
