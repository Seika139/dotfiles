import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "normalize_ponytail_hooks.py"
BASH = shutil.which("bash") or "bash"
SPEC = importlib.util.spec_from_file_location("normalize_ponytail_hooks", SCRIPT)
NORMALIZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NORMALIZER)


class NormalizePonytailHooksTest(unittest.TestCase):
    def test_normalizes_xsv_linux_hook_commands(self):
        raw = (
            "node -e \"require(require('node:path').join(process.env.CLAUDE_PLUGIN_ROOT"
            ".replaceAll(String.fromCharCode(92), '/'), 'hooks/ponytail-activate.js'))\""
        )
        with tempfile.TemporaryDirectory() as directory:
            claude_dir = Path(directory) / ".claude"
            claude_dir.mkdir()
            settings_path = claude_dir / "settings.json"
            sidecar_path = claude_dir / "apm-hooks.json"
            entry = {"hooks": [{"command": raw, "type": "command"}]}
            settings_path.write_text(
                json.dumps({"hooks": {"SessionStart": [entry]}}), encoding="utf-8"
            )
            sidecar_path.write_text(
                json.dumps({"SessionStart": [{**entry, "_apm_source": NORMALIZER.OWNER}]}),
                encoding="utf-8",
            )

            self.assertEqual(NORMALIZER.normalize(settings_path, sidecar_path), 2)
            updated = json.loads(settings_path.read_text(encoding="utf-8"))
            self.assertEqual(
                updated["hooks"]["SessionStart"][0]["hooks"][0]["command"],
                NORMALIZER.canonical_command(NORMALIZER._raw_command("ponytail-activate.js")),
            )

    def test_scopes_root_to_owned_hooks_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            claude_dir = Path(directory) / ".claude"
            claude_dir.mkdir()
            settings_path = claude_dir / "settings.json"
            sidecar_path = claude_dir / "apm-hooks.json"
            raw = (
                "node -e \"require(require('path').join(process.env.CLAUDE_PLUGIN_ROOT"
                ".split(String.fromCharCode(92)).join('/'), 'hooks/ponytail-activate.js'))\""
            )
            legacy = "node PONYTAIL_DIR/hooks/ponytail-subagent.js"
            settings = {
                "hooks": {
                    "SessionStart": [{"matcher": "*", "hooks": [{"command": raw, "type": "command"}]}],
                    "PreToolUse": [{"matcher": "Task", "hooks": [{"command": legacy, "type": "command"}]}],
                    "Stop": [{"matcher": "*", "hooks": [{"command": "other-plugin", "type": "command"}]}],
                }
            }
            sidecar = {
                "SessionStart": [
                    {"matcher": "*", "hooks": [{"command": raw, "type": "command"}], "_apm_source": NORMALIZER.OWNER}
                ],
                "PreToolUse": [
                    {"matcher": "Task", "hooks": [{"command": legacy, "type": "command"}], "_apm_source": NORMALIZER.LEGACY_OWNER}
                ],
                "Stop": [
                    {"matcher": "*", "hooks": [{"command": "other-plugin", "type": "command"}], "_apm_source": "other/package"}
                ],
            }
            settings_path.write_text(json.dumps(settings), encoding="utf-8")
            sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")

            self.assertEqual(NORMALIZER.normalize(settings_path, sidecar_path), 2)
            actual = json.loads(settings_path.read_text(encoding="utf-8"))
            owners = json.loads(sidecar_path.read_text(encoding="utf-8"))
            command = actual["hooks"]["SessionStart"][0]["hooks"][0]["command"]
            self.assertEqual(command, NORMALIZER.canonical_command(raw))
            self.assertNotIn("PreToolUse", actual["hooks"])
            self.assertNotIn("PreToolUse", owners)
            self.assertEqual(actual["hooks"]["Stop"][0]["hooks"][0]["command"], "other-plugin")
            self.assertEqual(owners["Stop"][0]["_apm_source"], "other/package")
            self.assertEqual(NORMALIZER.normalize(settings_path, sidecar_path), 0)

            package_hooks = Path(directory) / ".apm/apm_modules/DietrichGebert/ponytail/hooks"
            package_hooks.mkdir(parents=True)
            hook = package_hooks / "ponytail-activate.js"
            hook.write_text("process.stdout.write(process.env.CLAUDE_PLUGIN_ROOT)", encoding="utf-8")
            env = os.environ.copy()
            env["HOME"] = directory
            env["USERPROFILE"] = directory
            env["CLAUDE_PLUGIN_ROOT"] = "/wrong/plugin/root"
            result = subprocess.run(
                [BASH, "-c", command],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=True,
            )
            self.assertEqual(result.stdout, str(package_hooks.parent))

    def test_keeps_user_edited_hook_and_sidecar_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            claude_dir = Path(directory) / ".claude"
            claude_dir.mkdir()
            settings_path = claude_dir / "settings.json"
            sidecar_path = claude_dir / "apm-hooks.json"
            raw = (
                "node -e \"require(require('path').join(process.env.CLAUDE_PLUGIN_ROOT"
                ".split(String.fromCharCode(92)).join('/'), 'hooks/ponytail-activate.js'))\""
            )
            settings = {"hooks": {"SessionStart": [{"hooks": [{"command": "user-edited command"}]}]}}
            sidecar = {
                "SessionStart": [{"hooks": [{"command": raw}], "_apm_source": NORMALIZER.OWNER}]
            }
            settings_path.write_text(json.dumps(settings), encoding="utf-8")
            sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")

            self.assertEqual(NORMALIZER.normalize(settings_path, sidecar_path), 0)
            self.assertEqual(json.loads(settings_path.read_text(encoding="utf-8")), settings)
            self.assertEqual(json.loads(sidecar_path.read_text(encoding="utf-8")), sidecar)

    def test_repairs_a_crash_between_settings_and_sidecar_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            claude_dir = Path(directory) / ".claude"
            claude_dir.mkdir()
            settings_path = claude_dir / "settings.json"
            sidecar_path = claude_dir / "apm-hooks.json"
            raw = (
                "node -e \"require(require('path').join(process.env.CLAUDE_PLUGIN_ROOT"
                ".split(String.fromCharCode(92)).join('/'), 'hooks/ponytail-activate.js'))\""
            )
            canonical = NORMALIZER.canonical_command(raw)
            entry = {"hooks": [{"command": canonical, "type": "command"}]}
            settings_path.write_text(json.dumps({"hooks": {"SessionStart": [entry]}}), encoding="utf-8")
            sidecar_path.write_text(
                json.dumps({"SessionStart": [{"hooks": [{"command": raw, "type": "command"}], "_apm_source": NORMALIZER.OWNER}]}),
                encoding="utf-8",
            )

            self.assertEqual(NORMALIZER.normalize(settings_path, sidecar_path), 1)
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            self.assertEqual(sidecar["SessionStart"][0]["hooks"][0]["command"], canonical)

    def test_rolls_back_settings_and_sidecar_if_second_write_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            claude_dir = Path(directory) / ".claude"
            claude_dir.mkdir()
            settings_path = claude_dir / "settings.json"
            sidecar_path = claude_dir / "apm-hooks.json"
            raw = (
                "node -e \"require(require('path').join(process.env.CLAUDE_PLUGIN_ROOT"
                ".split(String.fromCharCode(92)).join('/'), 'hooks/ponytail-activate.js'))\""
            )
            entry = {"hooks": [{"command": raw, "type": "command"}]}
            settings_path.write_text(json.dumps({"hooks": {"SessionStart": [entry]}}), encoding="utf-8")
            sidecar_path.write_text(
                json.dumps({"SessionStart": [{**entry, "_apm_source": NORMALIZER.OWNER}]}), encoding="utf-8"
            )
            settings_path.chmod(0o600)
            sidecar_path.chmod(0o640)
            original_settings = settings_path.read_bytes()
            original_sidecar = sidecar_path.read_bytes()
            write = NORMALIZER._atomic_json_write
            calls = 0

            def fail_second_write(path, document):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated second-file write failure")
                write(path, document)

            with patch.object(NORMALIZER, "_atomic_json_write", side_effect=fail_second_write):
                with self.assertRaises(OSError):
                    NORMALIZER.normalize(settings_path, sidecar_path)

            self.assertEqual(settings_path.read_bytes(), original_settings)
            self.assertEqual(sidecar_path.read_bytes(), original_sidecar)
            if os.name == "posix":
                self.assertEqual(settings_path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(sidecar_path.stat().st_mode & 0o777, 0o640)
            self.assertEqual(sorted(path.name for path in claude_dir.iterdir()), ["apm-hooks.json", "settings.json"])


if __name__ == "__main__":
    unittest.main()
