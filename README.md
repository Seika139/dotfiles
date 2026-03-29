# dotfiles

<div align="center">
  <a href="https://github.com/Seika139/dotfiles/releases/tag/v0.9.0">
    <img alt="version" src="https://img.shields.io/badge/version-v0.9.0-white.svg">
  </a>
  &nbsp;&nbsp;
  <a href="https://github.com/Seika139/dotfiles/actions/workflows/lint-markdown.yml">
    <img alt="Markdown Lint" src="https://github.com/Seika139/dotfiles/actions/workflows/lint-markdown.yml/badge.svg">
  </a>
  &nbsp;&nbsp;
  <a href="https://github.com/Seika139/dotfiles/actions/workflows/lint-yaml.yml">
    <img alt="YAML Lint" src="https://github.com/Seika139/dotfiles/actions/workflows/lint-yaml.yml/badge.svg">
  </a>
  &nbsp;&nbsp;
  <a href="https://github.com/Seika139/dotfiles/actions/workflows/shellcheck.yml">
    <img alt="ShellCheck" src="https://github.com/Seika139/dotfiles/actions/workflows/shellcheck.yml/badge.svg">
  </a>
</div>

## 動作環境

以下の環境で動作することを確認しています。（動作するように dotfiles を育てている）
shell は bash を使用してください。

- Mac 系: ターミナル、iTerm2、VS Code 内のターミナル
- Win 系: GitBash、VS Code 内のターミナル（Git Bash）
- Linux 系: Ubuntu (on WSL), DevContainer

## install

このリポジトリをクローンします。

install.sh を実行してホームディレクトリにシンボリックリンクを作成します。

```bash
source install.sh
# または
bash install.sh
```

これによってシェルを起動した時に、 このプロジェクト内で設定した bash_profile や bashrc が読み込まれるようになります。

## uninstall

install.sh でホームディレクトリに作成したシンボリックリンクを unlink.sh で削除します。
シンボリックリンクを削除するだけで、元のファイルは削除されません。

```bash
source unlink.sh
# または
bash unlink.sh
```

## Change `__git_ps1`

Windows の GitBash が `__git_ps1` を読み込むのに時間をかけているので、ブランチ名だけを表示する簡易的な `__git_ps1` を作成した。
これにより、デフォルトでは Windows の GitBash では git によるファイル差分が表示されなくなっている。

以下のコマンドで表示を切り替えることができる。

```bash
lighten_ps1 # 軽くする(gitによるファイル差分を表示しない)
normalize_ps1 # 普通にする(gitによるファイル差分を表示する)
```

## ディレクトリ構成

| ディレクトリ | 概要 | 対象 OS |
| --- | --- | --- |
| `bash/` | シェル初期化・環境変数・関数定義 | All |
| `brew/` | Homebrew パッケージ管理（mise 経由） | macOS |
| `claude/` | Claude Code 設定（プロファイル別） | All |
| `codex/` | Codex CLI 設定（プロファイル別） | All |
| `gemini/` | Gemini CLI カスタムスラッシュコマンド | All |
| `vscode-settings/` | VS Code / Cursor の設定・拡張機能管理 | All |
| `scoop/` | Scoop パッケージ管理 | Windows |
| `winget/` | winget パッケージ管理 | Windows |
| `docker/` | Docker 環境管理 | All |
| `devcontainer-example/` | DevContainer の設定例 | All |
| `automation/` | Python 自動化スクリプト | All |
| `mouse_emulator/` | キーボードによるマウスエミュレーション | macOS |
| `chrome_extensions/` | 自作 Chrome 拡張機能 | All |
| `docs/` | 各種技術ドキュメント | — |
| `go/` | Go 学習用コード | — |
| `gtts_sample/` | Google Text-to-Speech サンプル | — |
| `python/` | Python ユーティリティ・セットアップ | — |

### ルート直下の主要ファイル

| ファイル | 概要 |
| --- | --- |
| `install.sh` | シンボリックリンク作成・環境セットアップ |
| `unlink.sh` | install.sh で作成したリンクの削除 |
| `.gitconfig` | Git グローバル設定 |
| `.gitignore_global` | Git グローバル除外パターン |
| `.gitmessage` | Git コミットメッセージテンプレート |
| `.tmux.conf` | tmux 設定 |
| `.editorconfig` | エディタ共通フォーマット設定 |

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
