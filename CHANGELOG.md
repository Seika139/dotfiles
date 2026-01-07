# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/Seika139/dotfiles/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Seika139/dotfiles/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Seika139/dotfiles/tree/v0.1.0
