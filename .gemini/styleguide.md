# Style Guide

This document outlines the coding and contribution conventions for this dotfiles repository.

## Language

**Use Japanese** for code review and comments, except for commit messages which should be in English.

## General Principles

- **Encoding**: All text files should be UTF-8 encoded.
- **Line Endings**: Use LF (`\n`) for line endings.
- **Indentation**: Use spaces for indentation. Default to 2 spaces unless specified otherwise for a language.
- **Whitespace**: Trim trailing whitespace from the end of lines for all files except Markdown.
- **Final Newline**: Ensure files end with a single newline character.

These rules are enforced by the `.editorconfig` file.

## Commit Messages

- **言語**: 日本語で書く。定型的な操作（Add test, Fix phpdoc 等）のみ英語可。
- **Subject**: 50文字以内。変更内容を直接記述し、日本語は動詞で終える（〜を追加、〜を修正、〜に変更など）。
- **プレフィックス**: Conventional Commits (`feat:`, `fix:` 等) や gitmoji は**使わない**。
- **コード参照**: クラス名・設定キー等はバッククォートで囲む。
- **Body**: Subject と空行で分離。`-` の箇条書きで what/why を説明。72文字で折り返す。
- **例**:

  ```plain
  `Config\Database` で指定したリトライポリシーの適用漏れを修正

  * AbstractDriverManagerでDriverインスタンス作成時にconnectRetryPolicyを適用していなかった
  * issue #2075 の再現テストを追加
  ```

## Shell Scripts

- **Interpreter**: Start scripts with `#!/bin/bash`.
- **Error Handling**: Use `set -eu` to exit on error and undefined variables.
- **Variables**:
  - Quote all variable expansions (e.g., `"${VAR}"`).
  - Use `${VAR}` for clarity.
  - Use uppercase for environment and global variables (e.g., `DOT_DIRECTORY`).
- **Indentation**: Use 2 spaces for indentation.

## Python

ALL Python projects should adhere to the following standards:

- **Project Management**: Use `uv` for dependency management and packaging. (Old projects may use `poetry`.)
- **Formatting**: Use `ruff` with a line length of 88 characters. (Old projects may use `black` and `isort`.)
- **Linting**: Use `ruff` to check for errors. The configuration is in `pyproject.toml`.
  - `select = ["E", "F", "I"]` (pycodestyle errors, Pyflakes, isort)
- **Dependencies**: Add any new dependencies to `pyproject.toml` using `uv`. Never use `pip install` directly and create a `requirements.txt` file.

## Markdown

- **Headings**: Use ATX-style headings (`#`, `##`, etc.).
- **Whitespace**: Trailing whitespace is permitted in Markdown files for formatting purposes (e.g., hard line breaks).
