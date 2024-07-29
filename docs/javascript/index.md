# Volta で Node.js を管理する

## Volta とは

Volta は Node.js のバージョン管理とパッケージ管理を専門とするツール

## 比較対象だったツール asdf

複数のプログラミング言語やツールのバージョン管理を行うためのユニバーサルバージョンマネージャ。

### Volta にした理由

- Node.js の管理に特化していて操作がシンプル。
- Windows において、asdf よりセットアップが楽
- 動作が早い

## インストールする

参考

- [Windows で Node.js のバージョン管理 - VOLTA v1.1.1 ｜るらい](https://note.com/rurai/n/n47a3fb9c4508)
- [Node.js バージョン管理 Volta を Windows にインストールする](https://zenn.dev/longbridge/articles/30c70144c97d32)

1. 開発者モードをオンにする
2. インストーラーをダウンロード
3. インストーラを起動し Volta をインストールする

### VS Code のターミナルを利用している場合

VS Code が起動している状態で Volta をインストールしても、 volta コマンドが反応しないので、一旦 VS Code を再起動する。

```bash
$ volta
Volta 1.1.1
The JavaScript Launcher ⚡

    To install a tool in your toolchain, use `volta install`.
    To pin your project's runtime or package manager, use `volta pin`.

USAGE:
    volta [FLAGS] [SUBCOMMAND]

FLAGS:
        --verbose    Enables verbose diagnostics
        --quiet      Prevents unnecessary output
    -v, --version    Prints the current version of Volta
    -h, --help       Prints help information

SUBCOMMANDS:
    fetch          Fetches a tool to the local machine
    install        Installs a tool in your toolchain
    uninstall      Uninstalls a tool from your toolchain
    pin            Pins your project's runtime or package manager
    list           Displays the current toolchain
    completions    Generates Volta completions
    which          Locates the actual binary that will be called by Volta
    setup          Enables Volta for the current user / shell
    run            Run a command with custom Node, npm, pnpm, and/or Yarn versions
    help           Prints this message or the help of the given subcommand(s)
```

### Node.js をインストールする

```bash
$ volta install node
success: installed and set node@20.15.1 (with npm@10.7.0) as default
```
