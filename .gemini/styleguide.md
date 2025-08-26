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

Commit messages should follow the Conventional Commits specification, as defined in the `.gitmessage` template.

- **Format**: `<type>(<scope>): <subject>`
- **Header**: The header line should not exceed 50 characters.
- **Body**: The body should be wrapped at 72 characters.
- **Example**:

  ```plain
  feat(brew): add new package to Brewfile

  This commit adds the 'ripgrep' package to the Brewfile to
  provide a faster search tool.
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
