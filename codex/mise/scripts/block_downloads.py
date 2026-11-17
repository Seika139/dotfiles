#!/usr/bin/env python3
"""Block Codex prompts when the session cwd is the user's Downloads folder."""

from __future__ import annotations

import ctypes
import json
import ntpath
import os
import posixpath
import re
import shlex
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import TextIO


DOWNLOADS_FOLDER_ID = "374DE290-123F-4565-9164-39C4925E467B"
WINDOWS_USER_DIRS_KEY = r"HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"


def windows_downloads_dir() -> Path:
    """Resolve Downloads through Windows Known Folders, including redirects."""
    if os.name != "nt":
        raise RuntimeError("Windows Known Folder lookup is only available on Windows")

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_uint32),
            ("Data2", ctypes.c_uint16),
            ("Data3", ctypes.c_uint16),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    folder_id = GUID.from_buffer_copy(uuid.UUID(DOWNLOADS_FOLDER_ID).bytes_le)
    path_pointer = ctypes.c_void_p()
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    ole32 = ctypes.WinDLL("ole32", use_last_error=True)
    shell32.SHGetKnownFolderPath.argtypes = [
        ctypes.POINTER(GUID), ctypes.c_uint32, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)
    ]
    shell32.SHGetKnownFolderPath.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    ole32.CoTaskMemFree.restype = None

    result = shell32.SHGetKnownFolderPath(ctypes.byref(folder_id), 0, None, ctypes.byref(path_pointer))
    if result != 0:
        raise OSError(result, "SHGetKnownFolderPath failed for Downloads")
    try:
        value = ctypes.wstring_at(path_pointer)
    finally:
        ole32.CoTaskMemFree(path_pointer)
    if not value:
        raise RuntimeError("Windows returned an empty Downloads path")
    return Path(value)


def linux_downloads_dir(home: Path | None = None, environ: dict[str, str] | None = None) -> Path:
    """Read XDG's user directory config without evaluating it as shell code."""
    env = os.environ if environ is None else environ
    home = Path.home() if home is None else home
    config_home = Path(env.get("XDG_CONFIG_HOME", str(home / ".config"))).expanduser()
    if not config_home.is_absolute():
        raise RuntimeError("XDG_CONFIG_HOME must be an absolute path")

    config_file = config_home / "user-dirs.dirs"
    try:
        contents = config_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return home / "Downloads"
    except OSError as error:
        raise RuntimeError(f"cannot read {config_file}: {error}") from error

    for line in contents.splitlines():
        match = re.match(r"\s*XDG_DOWNLOAD_DIR\s*=\s*(.*?)\s*$", line)
        if not match:
            continue
        try:
            parts = shlex.split(match.group(1), comments=False, posix=True)
        except ValueError as error:
            raise RuntimeError(f"invalid XDG_DOWNLOAD_DIR in {config_file}") from error
        if len(parts) != 1:
            raise RuntimeError(f"invalid XDG_DOWNLOAD_DIR in {config_file}")

        value = parts[0]
        home_text = str(home)
        value = value.replace("$" + "{HOME}", home_text).replace("$HOME", home_text)
        # A home-level download path makes every descendant a potential Downloads cwd.
        if value.rstrip("/") == home_text.rstrip("/"):
            raise RuntimeError("XDG_DOWNLOAD_DIR points to HOME; cannot safely verify the Downloads location")
        if "$" in value or not Path(value).is_absolute():
            raise RuntimeError(f"unsupported or non-absolute XDG_DOWNLOAD_DIR in {config_file}")
        return Path(value)

    return home / "Downloads"


def _is_wsl() -> bool:
    if os.environ.get("WSL_INTEROP"):
        return True
    try:
        return "microsoft" in Path("/proc/sys/kernel/osrelease").read_text(encoding="utf-8").lower()
    except OSError:
        return False


def wsl_windows_downloads_dir() -> Path | None:
    """Resolve and translate the Windows Downloads path when WSL interop exists."""
    if not _is_wsl():
        return None
    powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
    wslpath = shutil.which("wslpath")
    if not powershell or not wslpath:
        raise RuntimeError("WSL cannot verify Windows Downloads because PowerShell or wslpath is unavailable")

    value_property = "'{" + DOWNLOADS_FOLDER_ID + "}'"
    command = (
        "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false); "
        "$ErrorActionPreference='Stop'; "
        f"$value=(Get-ItemProperty -LiteralPath '{WINDOWS_USER_DIRS_KEY}').{value_property}; "
        "if (-not $value) { exit 1 }; [Environment]::ExpandEnvironmentVariables($value)"
    )
    try:
        result = subprocess.run(
            [powershell, "-NoProfile", "-NonInteractive", "-Command", command],
            check=True,
            capture_output=True,
            encoding="utf-8",
            text=True,
            timeout=3,
        )
        windows_path = result.stdout.strip()
        if not windows_path:
            raise RuntimeError("PowerShell returned an empty Windows Downloads path")
        translated = subprocess.run(
            [wslpath, "-u", windows_path],
            check=True,
            capture_output=True,
            encoding="utf-8",
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(f"cannot resolve Windows Downloads through WSL interop: {error}") from error
    value = translated.stdout.strip()
    if not value or not posixpath.isabs(value):
        raise RuntimeError("wslpath returned an invalid Windows Downloads path")
    return Path(value)


def downloads_dirs(system: str | None = None) -> list[Path]:
    """Return the Downloads locations applicable to the current runtime."""
    system = sys.platform if system is None else system
    if system == "win32":
        return [windows_downloads_dir()]
    if system == "darwin":
        return [Path.home() / "Downloads"]
    if system.startswith("linux"):
        result = [linux_downloads_dir()]
        windows_path = wsl_windows_downloads_dir()
        if windows_path is not None:
            result.append(windows_path)
        return result
    raise RuntimeError(f"unsupported operating system: {system}")


def _is_within(path: str, root: str, *, windows: bool) -> bool:
    path_module = ntpath if windows else posixpath
    path = path_module.normpath(path_module.normcase(path) if windows else path)
    root = path_module.normpath(path_module.normcase(root) if windows else root)
    try:
        return path_module.commonpath((path, root)) == root
    except ValueError:
        return False


def is_in_downloads(cwd: str, downloads: Path, *, windows: bool | None = None) -> bool:
    """Match Downloads lexically, by filesystem identity, and after symlink resolution."""
    windows = os.name == "nt" if windows is None else windows
    if _is_within(cwd, str(downloads), windows=windows):
        return True

    try:
        try:
            downloads_stat = downloads.stat()
        except FileNotFoundError:
            downloads_stat = None
        current = Path(cwd)
        while downloads_stat is not None:
            try:
                if os.path.samestat(current.stat(), downloads_stat):
                    return True
            except FileNotFoundError:
                pass
            if current.parent == current:
                break
            current = current.parent
    except OSError as error:
        raise RuntimeError(f"cannot inspect session or Downloads path: {error}") from error

    try:
        resolved_cwd = str(Path(cwd).resolve())
        resolved_downloads = str(downloads.resolve())
    except OSError as error:
        raise RuntimeError(f"cannot resolve session or Downloads path: {error}") from error
    return _is_within(resolved_cwd, resolved_downloads, windows=windows)


def read_hook_payload(stdin: TextIO) -> object:
    """Read Codex's UTF-8 JSON input while preserving text-stream test doubles."""
    stream = getattr(stdin, "buffer", stdin)
    payload = stream.read()
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    if not isinstance(payload, str):
        raise RuntimeError("Codex hook input was not text")
    return json.loads(payload)


def main(stdin: TextIO = sys.stdin, stderr: TextIO = sys.stderr, *, system: str | None = None) -> int:
    try:
        payload = read_hook_payload(stdin)
        cwd = payload.get("cwd") if isinstance(payload, dict) else None
        if not isinstance(cwd, str) or not cwd:
            raise RuntimeError("Codex did not provide an absolute session cwd")
        resolved_system = sys.platform if system is None else system
        windows = os.name == "nt" or resolved_system == "win32"
        is_absolute = ntpath.isabs(cwd) if resolved_system == "win32" else posixpath.isabs(cwd)
        if not is_absolute:
            raise RuntimeError("Codex did not provide an absolute session cwd")
        wsl_download_index = 1 if resolved_system.startswith("linux") and _is_wsl() else -1
        for index, downloads in enumerate(downloads_dirs(system)):
            if is_in_downloads(
                cwd,
                downloads,
                windows=windows or index == wsl_download_index,
            ):
                print(
                    f"Codex prompt blocked: the session is in Downloads ({downloads}). "
                    "Move to a trusted project directory and start a new Codex session.",
                    file=stderr,
                )
                return 2
    except (json.JSONDecodeError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"Codex prompt blocked: Downloads guard could not verify this session ({error}).", file=stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
