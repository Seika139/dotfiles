# AGENTS.md

This profile is optimized for development within Windows Subsystem for Linux (Ubuntu). It provides access to both Windows and Linux environments.
This profile is applied to user's global setting.
Use Japanese for communication.
Ask questions if the instructions are unclear.

## Basic Information

- OS: Linux (WSL2 Ubuntu)
- Shell: bash
- Code Editor: Visual Studio Code

## Preferred Tools and Libraries

Consider using the following tools and libraries for your project:

- Docker, Docker Compose, DevContainers
- mise (task runner and environment manager)
- Python: uv, ruff
- JavaScript: eslint, prettier
- Linux related tools: grep, sed, awk, find
- WSL related tools: wslpath, wsl.exe

## Code Style Guidelines

Lint and Format codes while editing. Select appropriate tools and libraries for the project.

User's preferred tools include:

- Python: uv, ruff
- JavaScript: eslint, prettier

## Environment-Specific Notes

- WSL環境では/mnt/c/でWindowsファイルシステムにアクセス可能
- Dockerを使用する場合はWSL2を使用することを推奨
- パス区切り文字はLinux形式（/）を使用
- Windows側のPowerShellコマンドを利用する場合は `pwsh.exe` で実行可能

## Restrictions

- No sensitive data should be hardcoded in the source code.
- Follow the principle of least privilege when accessing resources.
- WSL環境固有のセキュリティ制限を考慮する
