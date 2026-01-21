# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Tagged Releases

- [unreleased](https://github.com/Seika139/dotfiles/compare/v0.3.2...HEAD)
- [0.3.2](https://github.com/Seika139/dotfiles/compare/v0.3.1...v0.3.2)
- [0.3.1](https://github.com/Seika139/dotfiles/compare/v0.3.0...v0.3.1)
- [0.3.0](https://github.com/Seika139/dotfiles/compare/v0.2.0...v0.3.0)
- [0.2.0](https://github.com/Seika139/dotfiles/compare/v0.1.0...v0.2.0)
- [0.1.0](https://github.com/Seika139/dotfiles/tree/v0.1.0)

## [Unreleased]

### Added

- **Claude**
  - SKILL を追加した

### Changed

- **bash**
  - Dev Container で dotfiles をロードするときなど、非対話モードでシェルが起動しても install.sh が動作するように諸々の修正をした

## [0.3.2] - 2026-01-21

### Added

- **ShellCheck**
  - ローカルでは [bash/mise.toml](bash/mise.toml) が、CI では [.github/workflows/shellcheck.yml](.github/workflows/shellcheck.yml) がシェルスクリプトの静的解析をする機能を追加

### Changed

- **Bash (git alias):**
  - `gln` (authorごとの編集行数集計) を大幅に高速化し、Mac (BSD awk) と Linux (gawk) の両方で最適に動作するよう改善した。
- **Bash (DevContainer)**
  - Linux カーネルの DevContainer を起動した時に、自動でローカルの dotfiles をコンテナにコピーしてログインシェルを立ち上げるように設定した
  - その際に実際にエラーが出た箇所を修正して、エラーなく起動するようにした

## [0.3.1] - 2026-01-20

### Added

- **Bash (Daily Runner):**
  - 1日1回の実行判定にプロファイル管理 (`bash/daily/profile/`) を導入。環境変数 `DAILY_PROFILE` (`bash/daily/.env`) で切り替え可能に変更。
  - PIDベースのロック機構を実装し、複数のシェルを同時に起動した際の重複実行を防止。
  - 実行状況を把握するための詳細なログ出力 (`_bdotdir_daily_log_verbose`) を追加。
- **VS Code:**
  - `hm-m1-mac`, `win-15034` プロファイルの設定と拡張機能を更新。
  - `protobuf`, `grpc`, `buf` 関連の拡張機能および設定を追加。
  - 辞書ファイル (`cSpell`) への技術用語追加、`shellcheck` 用のカスタム引数を設定。
- **Docs**
  - dotenvx、 linux コマンド、 go、 dependabot に関するドキュメントを追加
- **AI Coding**
  - tmux で claude code から codex を起動する SKILL を追加

### Changed

- **VS Code:**
  - JSON/JSONC/JSONL のフォーマッタを `prettier.prettier-vscode` に統一し、JSONC での末尾カンマ問題を修正。
  - シェルスクリプトのデフォルトフォーマッタを `mads-hartmann.bash-ide-vscode` に変更。
  - Python 用のルーラー (`88`) を追加。

### Fixed

- **bash**
  - 1Password を利用している Mac が DevContainer を起動した際に ssh-agent が起動しない問題を修正。

## [0.3.0] - 2026-01-08

### Added

- **Bash:** 構成を大幅にリファクタリングし、環境変数やシークレットを動的に読み込む仕組み (`bash/envs/`, `bash/public/`) を導入
- **Antigravity:** `~/.gemini/` 配下の `GEMINI.md` および `global_workflows/` を `dotfiles` のプロファイル管理下に追加
- **GitHub Actions:** Markdown のリンター (`lint-markdown.yml`) およびバージョン更新の自動化 (`update-version.yml`) を追加
- **Workflows:** Antigravity で利用可能な `/changelog`, `/lint-markdown` ワークフローを定義
- **Editor:** プロジェクト全体のコードスタイルを統一するため `.editorconfig` を追加
- **Cursor:** Cursor CLI 用の設定ファイル (`cli-config.json`) を追加
- **Package Management:** Windows 用の `scoop-export.json` をプロファイルに追加

### Changed

- **Bash:** `szip` の管理を `make` から `mise` に移行し、エイリアスを `bash/public/51_szip.bash` に整理
- **Lint:** `markdownlint-cli2` の設定を更新し、ドキュメントの品質向上を図る
- **Git:** `.gitignore` に考え中フォルダ (`ideas/`) や退避フォルダ (`stashes/`) の指定を追加
-

## [0.2.0] - 2025-10-17

### Added

- **vscode**: Update keybindings and settings

### Docs

- Add guide on loose coupling and dependency injection
- **release**: Improve instructions for preparing changelogs
- **codex**: Add note on WSL file system performance

### Refactor

- **gemini**: Simplify release prepare command and add docs

## [0.1.0] - 2025-10-17

### Added

- `CHANGELOG.md` を作成
- **Codex:**
  - `cg-m2-mac` プロファイルの追加
  - スラッシュコマンドの追加
- **Gemini:**
  - CLI のプロファイル管理タスクを追加
  - CLI 用のプロンプトを追加
- **VSCode:** mac 用の設定を追加
- **Codex:**
  - Slash commands for enhanced functionality.
  - Profiles for `cg-m2-mac` and `win-15034`.
  - Documentation for Windows setup.
- **Platform Support:**
  - WSL/Ubuntu profile and refactored Windows configuration.
  - Initial support for `msys` (MinGW).
- **Package Management:**
  - `Brewfile` for easier package management on macOS.
  - `scoop` and `winget` configurations for Windows.
  - `mise` for managing tool versions.
  - `uv` for Python package management.
  - `Poetry` for Python dependency management.
- **VSCode:**
  - Settings and extensions for various environments (macOS, Windows).
  - Profile synchronization using `Makefile`.
  - `cSpell` for spell checking.
- **Chrome Extensions:**
  - `transparent_tab` for tab transparency.
  - `URL_INCREMENTER` to increment/decrement numbers in URLs.
  - `media_control` for media playback control.
- **Shell & Git:**
  - Numerous bash aliases and utility functions for git, file operations, etc.
  - `ssh-agent` management script.
  - `git worktree` documentation and aliases.
  - `.editorconfig` for consistent coding styles.
  - `.gitattributes` and `.gitignore_global` for better repository management.
- **Automation & Scripts:**
  - `automation` project using `Poetry`.
  - Auto-click script with dynamic interval and recording.
  - `ltsv_to_json` conversion script.
- **Documentation:**
  - Extensive documentation for `git`, `docker`, `python`, `javascript`, `linux`, `mac`, `windows`, `ai`, `dev_containers`, `github`, `makefile`,`mise`, `tailscale`, `unity`, `uv`.
  - `Gemini` style guide.

### Changed

- README を更新
- `mise dump`をオプションなしで実行可能に変更
- reaper を`--cask`でインストールするように変更
- スラッシュコマンドを修正
- `print` を `printf` に修正
- ファイルの場所を移動
- **Codex:**
  - `config.toml` を Git 管理から除外
  - リンクが外れた際の利便性を向上
- **Gemini:**
  - command 実行に toml を使用するように変更
  - commands を移動
  - CLI のインストール方法を npm から brew に変更
- 他の動作する commands に合わせて toml を修正
- **Shell & Git:**
  - Refactored bash scripts for better readability and maintainability.
  - Switched from `echo` to `printf` for more consistent output in scripts.
  - Improved `HOME` path fixing logic in bash.
  - Updated git aliases and configurations for better workflow.
  - Renamed `uninstall.sh` to `unlink.sh`.
- **Package Management:**
  - Improved `brew install` to automatically upgrade existing packages.
  - Migrated from `Makefile` to `mise` for `vscode-settings`.
- **VSCode:**
  - Updated various settings and extensions.
- **File Naming:**
  - Normalized ringtone filenames.

### Fixed

- 未定義変数を修正
- 権限拒否の問題を修正
- **Shell & Git:**
  - Handled spaces in `VSCODE_PATH` correctly.
  - Corrected `is_win` function to properly detect Windows environments.
  - Addressed an issue where `ssh/config` could be accidentally deleted.
- **Platform Support:**
  - Resolved issues with `codex` settings on WSL.
  - Fixed `auto_lick` script settings for Windows.
- **Tools:**
  - Corrected ringtone file matching and extended playback duration.
  - Addressed a color issue in multi-line list outputs.

### Removed

- **Configuration:**
  - Removed `config.toml` from git management in favor of split configuration files.
- **Tools:**
  - Removed `asdf` as it is no longer in use.
  - Deleted unnecessary files and deprecated `GREP_OPTIONS`.
