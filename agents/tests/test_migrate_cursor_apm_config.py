import io
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT_DIR / "agents" / "mise" / "scripts" / "migrate_cursor_apm_config.py"
HELPER_PATH = ROOT_DIR / "agents" / "mise" / "scripts" / "cursor_home.sh"
SPEC = importlib.util.spec_from_file_location("migrate_cursor_apm_config", SCRIPT_PATH)
MIGRATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATOR)
BASH = shutil.which("bash") or "bash"


def bash_path(path):
    if os.name != "nt":
        return str(path)
    result = subprocess.run(
        [BASH, "-c", 'cygpath -u "$1"', "cygpath", str(path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return result.stdout.strip()


class MigrateCursorApmConfigTest(unittest.TestCase):
    def _write_json(self, path, value):
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_mcp_merge_adds_only_missing_servers_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cursor_dir = root / ".cursor"
            cursor_dir.mkdir()
            source_path = root / "source-mcp.json"
            target_path = cursor_dir / "mcp.json"
            self._write_json(
                source_path,
                {
                    "mcpServers": {
                        "serena": {"command": "uvx", "args": ["source"]},
                        "new-server": {"command": "new"},
                    }
                },
            )
            self._write_json(
                target_path,
                {
                    "customSetting": True,
                    "mcpServers": {
                        "serena": {"command": "user-edited"},
                        "atlassian": {"command": "user-configured"},
                    },
                },
            )
            target_path.chmod(0o640)

            self.assertTrue(MIGRATOR.merge_mcp_config(cursor_dir, source_path))
            merged = json.loads(target_path.read_text(encoding="utf-8"))
            self.assertTrue(merged["customSetting"])
            self.assertEqual(merged["mcpServers"]["serena"]["command"], "user-edited")
            self.assertEqual(merged["mcpServers"]["atlassian"]["command"], "user-configured")
            self.assertEqual(merged["mcpServers"]["new-server"]["command"], "new")
            if os.name == "posix":
                self.assertEqual(target_path.stat().st_mode & 0o777, 0o640)
            self.assertFalse(MIGRATOR.merge_mcp_config(cursor_dir, source_path))

    def test_mcp_rejects_symlink_and_invalid_documents_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cursor_dir = root / ".cursor"
            cursor_dir.mkdir()
            source_path = root / "source-mcp.json"
            elsewhere = root / "elsewhere.json"
            self._write_json(source_path, {"mcpServers": {"serena": {"command": "uvx"}}})
            self._write_json(elsewhere, {"mcpServers": {"keep": {"command": "unchanged"}}})
            target_path = cursor_dir / "mcp.json"
            target_path.symlink_to(elsewhere)

            with self.assertRaises(ValueError):
                MIGRATOR.merge_mcp_config(cursor_dir, source_path)
            self.assertEqual(json.loads(elsewhere.read_text(encoding="utf-8"))["mcpServers"].keys(), {"keep"})

            target_path.unlink()
            target_path.write_text('{"mcpServers": []}\n', encoding="utf-8")
            original = target_path.read_bytes()
            with self.assertRaises(ValueError):
                MIGRATOR.merge_mcp_config(cursor_dir, source_path)
            self.assertEqual(target_path.read_bytes(), original)

    def test_removes_only_exact_owned_legacy_events(self):
        with tempfile.TemporaryDirectory() as directory:
            cursor_dir = Path(directory) / ".cursor"
            cursor_dir.mkdir()
            hooks_path = cursor_dir / "hooks.json"
            sidecar_path = cursor_dir / "apm-hooks.json"
            old_prompt = {"matcher": "*", "hooks": [{"command": "old-ponytail-prompt"}]}
            old_tool = {"matcher": "Task", "hooks": [{"command": "old-ponytail-tool"}]}
            user_hook = {"matcher": "*", "hooks": [{"command": "user-hook"}]}
            edited_hook = {"matcher": "Task", "hooks": [{"command": "user-edited-command"}]}
            stale_owner = {"matcher": "Task", "hooks": [{"command": "previous-command"}]}
            unrelated_hook = {"matcher": "*", "hooks": [{"command": "other-plugin"}]}
            self._write_json(
                hooks_path,
                {
                    "hooks": {
                        "UserPromptSubmit": [old_prompt, user_hook],
                        "PreToolUse": [old_tool, edited_hook],
                        "SessionStart": [unrelated_hook],
                    }
                },
            )
            self._write_json(
                sidecar_path,
                {
                    "UserPromptSubmit": [
                        dict(old_prompt, _apm_source="ponytail"),
                        dict(edited_hook, _apm_source="dietrichgebert/ponytail"),
                        dict(unrelated_hook, _apm_source="other/package"),
                    ],
                    "PreToolUse": [
                        dict(old_tool, _apm_source="dietrichgebert/ponytail"),
                        dict(stale_owner, _apm_source="dietrichgebert/ponytail"),
                    ],
                    "SessionStart": [dict(unrelated_hook, _apm_source="other/package")],
                },
            )

            self.assertTrue(MIGRATOR.remove_legacy_hooks(cursor_dir))
            hooks = json.loads(hooks_path.read_text(encoding="utf-8"))["hooks"]
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            self.assertEqual(hooks["UserPromptSubmit"], [user_hook])
            self.assertEqual(hooks["PreToolUse"], [edited_hook])
            self.assertEqual(hooks["SessionStart"], [unrelated_hook])
            self.assertEqual(sidecar["UserPromptSubmit"][0]["_apm_source"], "dietrichgebert/ponytail")
            self.assertEqual(sidecar["UserPromptSubmit"][1]["_apm_source"], "other/package")
            self.assertEqual(sidecar["PreToolUse"][0]["hooks"], stale_owner["hooks"])
            self.assertEqual(sidecar["SessionStart"][0]["_apm_source"], "other/package")

    def test_preserves_missing_or_edited_owned_hook_and_handles_partial_file_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            cursor_dir = Path(directory) / ".cursor"
            cursor_dir.mkdir()
            hooks_path = cursor_dir / "hooks.json"
            sidecar_path = cursor_dir / "apm-hooks.json"
            owned = {"matcher": "*", "hooks": [{"command": "old-ponytail"}]}
            self._write_json(hooks_path, {"hooks": {"UserPromptSubmit": [{"hooks": [{"command": "edited"}]}]}})
            self._write_json(
                sidecar_path,
                {"UserPromptSubmit": [dict(owned, _apm_source="ponytail")]},
            )
            original_hooks = hooks_path.read_bytes()
            original_sidecar = sidecar_path.read_bytes()
            warning = io.StringIO()
            with redirect_stderr(warning):
                self.assertFalse(MIGRATOR.remove_legacy_hooks(cursor_dir))
                self.assertFalse(MIGRATOR.remove_legacy_hooks(cursor_dir))
            self.assertEqual(hooks_path.read_bytes(), original_hooks)
            self.assertEqual(sidecar_path.read_bytes(), original_sidecar)
            self.assertEqual(warning.getvalue().count("rerunning will not remove"), 2)

            self._write_json(hooks_path, {"hooks": {"UserPromptSubmit": [owned]}})
            self._write_json(sidecar_path, {"UserPromptSubmit": [dict(owned, _apm_source="ponytail")]})
            original_hooks = hooks_path.read_bytes()
            original_sidecar = sidecar_path.read_bytes()
            atomic_write = MIGRATOR._atomic_write
            calls = [0]

            def fail_second_write(path, data, mode):
                calls[0] += 1
                if calls[0] == 2:
                    raise OSError("simulated sidecar write failure")
                atomic_write(path, data, mode)

            with patch.object(MIGRATOR, "_atomic_write", side_effect=fail_second_write):
                with self.assertRaises(OSError):
                    MIGRATOR.remove_legacy_hooks(cursor_dir)
            self.assertEqual(hooks_path.read_bytes(), original_hooks)
            self.assertEqual(sidecar_path.read_bytes(), original_sidecar)
            self.assertEqual(sorted(path.name for path in cursor_dir.iterdir()), ["apm-hooks.json", "hooks.json"])

    def test_mcp_addition_survives_hook_validation_failure_without_touching_hooks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cursor_dir = root / ".cursor"
            cursor_dir.mkdir()
            source_path = root / "source-mcp.json"
            target_path = cursor_dir / "mcp.json"
            self._write_json(source_path, {"mcpServers": {"serena": {"command": "source"}}})
            self._write_json(target_path, {"mcpServers": {"atlassian": {"command": "user"}}})
            hooks_path = cursor_dir / "hooks.json"
            self._write_json(cursor_dir / "apm-hooks.json", {})
            hooks_path.write_text('{"hooks": []}\n', encoding="utf-8")
            original_hooks = hooks_path.read_bytes()

            with self.assertRaises(ValueError):
                MIGRATOR.migrate(cursor_dir, source_path)

            servers = json.loads(target_path.read_text(encoding="utf-8"))["mcpServers"]
            self.assertEqual(set(servers), {"atlassian", "serena"})
            self.assertEqual(hooks_path.read_bytes(), original_hooks)

    def test_shell_helper_migrates_legacy_cursor_link_with_noncanonical_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "dotfiles"
            root_alias = Path(directory) / "dotfiles-link"
            home = Path(directory) / "home"
            source_cursor = root / ".cursor"
            target_cursor = home / ".cursor"
            for path in (
                source_cursor,
                root / "agents" / "mise" / "scripts",
                root / "claude" / "mise" / "scripts",
            ):
                path.mkdir(parents=True, exist_ok=True)
            home.mkdir()
            subprocess.run(
                [BASH, "-c", 'ln -s "$1" "$2"', "link-dotfiles", bash_path(root), bash_path(root_alias)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            (root / "agents" / "mise" / "scripts" / "migrate_cursor_apm_config.py").symlink_to(SCRIPT_PATH)
            (root / "claude" / "mise" / "scripts" / "run_python.sh").symlink_to(
                ROOT_DIR / "claude" / "mise" / "scripts" / "run_python.sh"
            )
            self._write_json(source_cursor / "mcp.json", {"mcpServers": {"serena": {"command": "source"}}})
            subprocess.run(
                [BASH, "-c", 'ln -s "$1" "$2"', "link-cursor", bash_path(source_cursor), bash_path(target_cursor)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            command = [
                BASH,
                "-c",
                'source "$1"; ensure_dotfiles_cursor_home "$2/agents/.." "$3"',
                "test-cursor-home",
                bash_path(HELPER_PATH),
                bash_path(root_alias),
                bash_path(home),
            ]
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(
                result.returncode,
                0,
                "stdout:\n{}\nstderr:\n{}".format(result.stdout, result.stderr),
            )
            self.assertTrue(target_cursor.is_dir())
            self.assertFalse(target_cursor.is_symlink())
            self.assertEqual(
                json.loads((target_cursor / "mcp.json").read_text(encoding="utf-8"))["mcpServers"]["serena"]["command"],
                "source",
            )
            backups = list(home.glob(".cursor.legacy-link.*"))
            self.assertEqual(len(backups), 1)
            self.assertTrue(backups[0].is_symlink())

    def test_shell_helper_keeps_unrelated_cursor_symlink_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "dotfiles"
            home = Path(directory) / "home"
            elsewhere = Path(directory) / "other-cursor"
            source_cursor = root / ".cursor"
            target_cursor = home / ".cursor"
            source_cursor.mkdir(parents=True)
            home.mkdir()
            elsewhere.mkdir()
            subprocess.run(
                [BASH, "-c", 'ln -s "$1" "$2"', "link-cursor", bash_path(elsewhere), bash_path(target_cursor)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            original_target = os.readlink(target_cursor)

            result = subprocess.run(
                [
                    BASH,
                    "-c",
                    'source "$1"; ensure_dotfiles_cursor_home "$2" "$3"',
                    "test-cursor-home",
                    bash_path(HELPER_PATH),
                    bash_path(root),
                    bash_path(home),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 2)
            self.assertTrue(target_cursor.is_symlink())
            self.assertEqual(os.readlink(target_cursor), original_target)

    def test_shell_helper_migrates_relative_cursor_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "dotfiles"
            home = Path(directory) / "home"
            source_cursor = root / ".cursor"
            target_cursor = home / ".cursor"
            for path in (
                source_cursor,
                root / "agents" / "mise" / "scripts",
                root / "claude" / "mise" / "scripts",
            ):
                path.mkdir(parents=True, exist_ok=True)
            home.mkdir()
            (root / "agents" / "mise" / "scripts" / "migrate_cursor_apm_config.py").symlink_to(SCRIPT_PATH)
            (root / "claude" / "mise" / "scripts" / "run_python.sh").symlink_to(
                ROOT_DIR / "claude" / "mise" / "scripts" / "run_python.sh"
            )
            subprocess.run(
                [BASH, "-c", 'ln -s "$1" "$2"', "link-cursor", "../dotfiles/.cursor", bash_path(target_cursor)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            result = subprocess.run(
                [
                    BASH,
                    "-c",
                    'source "$1"; ensure_dotfiles_cursor_home "$2" "$3"',
                    "test-cursor-home",
                    bash_path(HELPER_PATH),
                    bash_path(root),
                    bash_path(home),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(
                result.returncode,
                0,
                "stdout:\n{}\nstderr:\n{}".format(result.stdout, result.stderr),
            )
            self.assertTrue(target_cursor.is_dir())
            self.assertFalse(target_cursor.is_symlink())

    def test_shell_helper_keeps_dangling_cursor_symlink_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "dotfiles"
            home = Path(directory) / "home"
            source_cursor = root / ".cursor"
            target_cursor = home / ".cursor"
            source_cursor.mkdir(parents=True)
            home.mkdir()
            subprocess.run(
                [BASH, "-c", 'ln -s "$1" "$2"', "link-cursor", "../missing-cursor", bash_path(target_cursor)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            original_target = os.readlink(target_cursor)

            result = subprocess.run(
                [
                    BASH,
                    "-c",
                    'source "$1"; ensure_dotfiles_cursor_home "$2" "$3"',
                    "test-cursor-home",
                    bash_path(HELPER_PATH),
                    bash_path(root),
                    bash_path(home),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            self.assertEqual(result.returncode, 2)
            self.assertTrue(target_cursor.is_symlink())
            self.assertFalse(target_cursor.exists())
            self.assertEqual(os.readlink(target_cursor), original_target)

    def test_shell_helper_materializes_legacy_mcp_link_and_runs_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "dotfiles"
            home = Path(directory) / "home"
            source_cursor = root / ".cursor"
            target_cursor = home / ".cursor"
            for path in (
                source_cursor,
                target_cursor,
                root / "agents" / "mise" / "scripts",
                root / "claude" / "mise" / "scripts",
            ):
                path.mkdir(parents=True, exist_ok=True)
            (root / "agents" / "mise" / "scripts" / "migrate_cursor_apm_config.py").symlink_to(SCRIPT_PATH)
            (root / "claude" / "mise" / "scripts" / "run_python.sh").symlink_to(
                ROOT_DIR / "claude" / "mise" / "scripts" / "run_python.sh"
            )
            source_mcp = source_cursor / "mcp.json"
            self._write_json(source_mcp, {"mcpServers": {"serena": {"command": "source"}}})
            self._write_json(
                target_cursor / "mcp.json",
                {"mcpServers": {"atlassian": {"command": "user"}}},
            )
            (target_cursor / "mcp.json").unlink()
            (target_cursor / "mcp.json").symlink_to(source_mcp)
            legacy = {"matcher": "*", "hooks": [{"command": "old-ponytail"}]}
            other = {"matcher": "*", "hooks": [{"command": "keep-me"}]}
            self._write_json(target_cursor / "hooks.json", {"hooks": {"UserPromptSubmit": [legacy, other]}})
            self._write_json(
                target_cursor / "apm-hooks.json",
                {"UserPromptSubmit": [dict(legacy, _apm_source="ponytail")]},
            )

            command = [
                BASH,
                "-c",
                'source "$1"; ensure_dotfiles_cursor_home "$2" "$3"',
                "test-cursor-home",
                bash_path(HELPER_PATH),
                bash_path(root),
                bash_path(home),
            ]
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                "stdout:\n{}\nstderr:\n{}".format(result.stdout, result.stderr),
            )

            self.assertFalse((target_cursor / "mcp.json").is_symlink())
            self.assertEqual(
                set(json.loads((target_cursor / "mcp.json").read_text(encoding="utf-8"))["mcpServers"]),
                {"serena"},
            )
            migrated_hooks = json.loads((target_cursor / "hooks.json").read_text(encoding="utf-8"))
            self.assertEqual(migrated_hooks["hooks"]["UserPromptSubmit"], [other])


if __name__ == "__main__":
    unittest.main()
