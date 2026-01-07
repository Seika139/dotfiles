# Gemini Agent Context: Dotfiles Repository

## Project Overview

This repository is a comprehensive collection of "dotfiles" used to configure and synchronize a development environment across multiple machines, with a focus on macOS and Windows (using Git Bash or WSL).

The primary shell environment is `bash`. The setup is highly automated through shell scripts and the `mise` task runner.

The core philosophy is to maintain different configurations for various tools in "profiles" and then use `mise` to create symbolic links, effectively activating a chosen profile.

## Core Concepts

### 1. Installation & Setup

The initial setup is handled by the `install.sh` script.

- **Action**: It must be **sourced** (`source install.sh`), not executed directly.
- **Purpose**:
  - Installs Homebrew on macOS if not present.
  - Creates symbolic links from this repository to the user's home directory (`~`) for essential configuration files like `.bash_profile`, `.gitconfig`, and others.
  - Sets up user-specific configurations (e.g., `~/.gitconfig.local`).
  - Reloads the shell to apply the new settings.

### 2. Package Management

The repository manages system and development packages using platform-specific tools:

- **macOS**: Uses **Homebrew**. The packages are defined in `Brewfile`. You can install them by running `brew bundle` within the root directory.
- **Windows**: Uses a combination of **Winget** (`winget/`) and **Scoop** (`scoop/`) for package management.

### 3. Configuration Management with `mise`

**`mise`** is the task runner used to manage configurations for different tools. This is the most important concept in this repository.

- **Profiles**: For tools like Gemini (`gemini/`), Claude (`claude/`), and VS Code (`vscode-settings/`), configurations are stored in subdirectories within a `profiles/` directory (e.g., `gemini/profiles/personal`, `gemini/profiles/work`).
- **Activation**: `mise` tasks are used to switch between these profiles. The tasks typically work by:
  1. Reading a default profile name from a local `.toml` file (e.g., `gemini/mise.local.toml`).
  2. Creating symbolic links from the chosen profile directory (e.g., `gemini/profiles/work/commands`) to the tool's actual configuration location (e.g., `~/.gemini/commands`).
- **Local Settings**: Each tool-specific directory (like `gemini/`) contains a `mise.toml` defining the tasks and a `mise.local.toml` (which you may need to create) to specify which profile to use.

## Key Directories

- `bash/`: Contains the core `.bash_profile`, `.bashrc`, and other shell scripts.
- `brew/`: Homebrew configuration for macOS.
- `winget/` & `scoop/`: Winget and Scoop configurations for Windows.
- `git/`: Git-related configuration files.
- `ssh/`: SSH configuration management.
- `vscode-settings/`: Manages settings, keybindings, and extensions for VS Code and Cursor.
- `gemini/`, `claude/`, `codex/`: Configuration management for various AI assistant CLIs, using the `mise` profile system.
- `install.sh`: The main installation script.
- `unlink.sh`: Removes the symbolic links created by `install.sh`.

## Common Workflows

### Initial Environment Setup

To set up a new machine, clone the repository and run:

```bash
source install.sh
```

### Managing Tool Configurations (Example: Gemini CLI)

To interact with the configurations defined in this repository, you will use `mise` commands, specifying the target directory with the `-C` flag.

- **List available Gemini profiles:**

  ```bash
  mise -C gemini run list
  ```

- **Switch the active Gemini profile:**

  ```bash
  # This will update the symlinks in ~/.gemini
  mise -C gemini run switch <profile-name>
  ```

- **Check the status of the current Gemini configuration:**

  ```bash
  mise -C gemini run status
  ```

This same pattern applies to other tools like `claude` and `vscode-settings`.

### Installing/Updating Packages (macOS)

Navigate to the repository root and run:

```bash
# This will install all packages listed in the Brewfile
brew bundle
```
