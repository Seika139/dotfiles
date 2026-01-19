# dotfiles

<div align="center">
  <a href="https://github.com/Seika139/dotfiles/releases/tag/v0.3.1">
    <img alt="version" src="https://img.shields.io/badge/version-v0.3.1-white.svg">
  </a>
  &nbsp;&nbsp;
  <a href="https://github.com/Seika139/dotfiles/actions/workflows/lint-markdown.yml">
    <img alt="Markdown Lint" src="https://github.com/Seika139/dotfiles/actions/workflows/lint-markdown.yml/badge.svg">
  </a>
</div>

## 動作環境

以下の環境で動作することを確認しています。（動作するように dotfiles を育てている）
shell は bash を使用してください。

- Mac 系: ターミナル、iTerm2、VS Code 内のターミナル
- Win 系: GitBash、VS Code 内のターミナル（Git Bash）

## install

このリポジトリをクローンします。

install.sh を実行してホームディレクトリにシンボリックリンクを作成します。

```bash
source install.sh
```

これによってシェルを起動した時に、 このプロジェクト内で設定した bash_profile や bashrc が読み込まれるようになります。

## uninstall

install.sh でホームディレクトリに作成したシンボリックリンクを unlink.sh で削除します。
シンボリックリンクを削除するだけで、元のファイルは削除されません。

```bash
source unlink.sh
```

## Change `__git_ps1`

Windows の GitBash が `__git_ps1` を読み込むのに時間をかけているので、ブランチ名だけを表示する簡易的な `__git_ps1` を作成した。
これにより、デフォルトでは Windows の GitBash では git によるファイル差分が表示されなくなっている。

以下のコマンドで表示を切り替えることができる。

```bash
lighten_ps1 # 軽くする(gitによるファイル差分を表示しない)
normalize_ps1 # 普通にする(gitによるファイル差分を表示する)
```

## dotfiles とは

ホームディレクトリに置いてあるドット `.` から始まる設定ファイル（`.bashrc` など）を管理しているリポジトリのこと。
先輩につくることを勧められたので私も制作して運用中。（2021 年~）

## Features

シェルの初期化以外にこのプロジェクトが実現する機能

### パッケージ管理

Mac では Homebrew を介したパッケージの管理を行う。 → `brew/` を参照。
Windows では `winget` と `scoop` の 2 つを使用してパッケージ管理を行う。
Windows PC の基本的なセットアップは `winget` で行い、`scoop` は開発ツールのインストールに使用するという使い分けを想定している。そのため、scoop 側でては全てのパッケージの面倒を見るが、winget では特定のパッケージのみを管理する。
タスクランナーに mise を利用しているので、詳細は各ディレクトリの `mise.toml` を参照。

### AI Coding 環境の管理

Codex CLI や Claude Code の設定を管理する。
タスクランナーとして `mise` を使用して、pc ごとに profile を設定し、ホームディレクトリの `.codex` / `.claude` 配下にシンボリックリンクを作成する。

### エディタの設定

VS Code と Cursor について

- settings.json
- keybindings.json
- task.json
- snippets
- vscode_extensions.txt / cursor_extensions.txt

を管理する。拡張機能以外は両方の設定が同期されるようになっている。

### Docker

ローカル PC の Docker 環境を管理する。

## 参考

### 特に参考になった

- [ようこそ dotfiles の世界へ](https://qiita.com/yutkat/items/c6c7584d9795799ee164)
- [【初心者版】必要最小限の dotfiles を運用する](https://qiita.com/ganyariya/items/d9adffc6535dfca6784b)

### これから見たい

- [dotfiles の育て方](https://qiita.com/reireias/items/b33b5c824a56dc89e1f7)

### その他

- [dotfiles を GitHub で管理](https://qiita.com/okamos/items/7f5461814e8ed8916870)
