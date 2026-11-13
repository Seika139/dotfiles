import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MERGE_JQ = ROOT / "scripts" / "merge-settings.jq"
RECOVER = ROOT / "scripts" / "recover-settings.sh"
BASH = shutil.which("bash")
JQ = shutil.which("jq")


def hook(command: str) -> dict:
    return {"matcher": "", "hooks": [{"type": "command", "command": command}]}


def write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document), encoding="utf-8")


def merge_files(portable: Path, local: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [JQ, "-s", "-f", str(MERGE_JQ), str(portable), str(local)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="utf-8",
        check=False,
    )


@unittest.skipUnless(JQ, "jq is required")
class MergeSettingsTest(unittest.TestCase):
    def merge(self, portable: dict, local: dict) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as directory:
            portable_path = Path(directory) / "settings.json"
            local_path = Path(directory) / "settings.local.json"
            write_json(portable_path, portable)
            write_json(local_path, local)
            return merge_files(portable_path, local_path)

    def test_concatenates_shared_event_portable_first(self):
        result = self.merge(
            {"hooks": {"Stop": [hook("p")], "Notification": [hook("n")]}, "model": "a"},
            {"hooks": {"Stop": [hook("l")], "PreToolUse": [hook("x")]}, "model": "b"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "hooks": {
                    "Notification": [hook("n")],
                    "PreToolUse": [hook("x")],
                    "Stop": [hook("p"), hook("l")],
                },
                "model": "b",
            },
        )

    def test_drops_local_entries_equal_to_portable(self):
        result = self.merge(
            {"hooks": {"Stop": [hook("p")]}},
            {"hooks": {"Stop": [hook("p"), hook("l")]}},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"hooks": {"Stop": [hook("p"), hook("l")]}})

    def test_rejects_non_array_event(self):
        result = self.merge({"hooks": {"Stop": hook("p")}}, {})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hooks.Stop", result.stderr)

    def test_rejects_non_object_hooks(self):
        result = self.merge({}, {"hooks": []})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("settings.local.json", result.stderr)

    def test_omits_hooks_when_both_sides_lack_it(self):
        result = self.merge({"env": {"A": "1"}}, {"env": {"B": "2"}})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"env": {"A": "1", "B": "2"}})


@unittest.skipUnless(JQ and BASH, "jq and bash are required")
class RecoverSettingsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.home = base / "home"
        self.config_root = base / "root"
        self.profile = self.config_root / "profiles" / "test"
        self.target = self.home / ".claude" / "settings.json"
        self.link_marker = base / "link-called"
        stub = self.config_root / "mise" / "scripts" / "link.sh"
        stub.parent.mkdir(parents=True)
        # link.sh は本物の ~/.claude を触らないようスタブに差し替える
        stub.write_text(f'#!/bin/bash\ntouch "{self.link_marker.as_posix()}"\n', encoding="utf-8")
        self.profile.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def env(self) -> dict:
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(self.home),
                "MISE_CONFIG_ROOT": self.config_root.as_posix(),
                "IS_WSL": "false",
                "DEFAULT_CLAUDE_PROFILE": "test",
                "PROFILES_DIR": "profiles",
            }
        )
        return env

    def recover(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [BASH, str(RECOVER), "--prof", "test"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding="utf-8",
            env=self.env(),
            check=False,
        )

    def read(self, name: str) -> dict:
        return json.loads((self.profile / name).read_text(encoding="utf-8"))

    def test_splits_hooks_per_entry(self):
        write_json(self.profile / "settings.json", {"hooks": {"Stop": [hook("p")]}, "model": "a"})
        write_json(self.profile / "settings.local.json", {"hooks": {"Stop": [hook("old")]}})
        source = {
            "hooks": {"Stop": [hook("p"), hook("l")], "PreToolUse": [hook("x")]},
            "model": "a",
        }
        write_json(self.target, source)

        result = self.recover()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.link_marker.exists())
        self.assertEqual(self.read("settings.json"), {"hooks": {"Stop": [hook("p")]}, "model": "a"})
        self.assertEqual(
            self.read("settings.local.json"),
            {"hooks": {"PreToolUse": [hook("x")], "Stop": [hook("l")]}},
        )
        merged = merge_files(self.profile / "settings.json", self.profile / "settings.local.json")
        self.assertEqual(merged.returncode, 0, merged.stderr)
        self.assertEqual(json.loads(merged.stdout), source)

    def assert_aborted_without_writes(self, result: subprocess.CompletedProcess, message: str):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(message, result.stderr)
        self.assertFalse(self.link_marker.exists())

    def test_aborts_when_portable_entry_is_missing(self):
        portable = '{"hooks": {"Stop": [{"hooks": [{"command": "p", "type": "command"}], "matcher": ""}]}}'
        (self.profile / "settings.json").write_text(portable, encoding="utf-8")
        write_json(self.target, {"hooks": {"Stop": [hook("edited")]}})

        result = self.recover()

        self.assert_aborted_without_writes(result, "ガード C")
        self.assertIn("Stop", result.stderr)
        self.assertEqual((self.profile / "settings.json").read_text(encoding="utf-8"), portable)
        self.assertFalse((self.profile / "settings.local.json").exists())

    @unittest.skipUnless(shutil.which("cygpath"), "cygpath is required")
    def test_guard_a_detects_mixed_windows_home(self):
        mixed_home = subprocess.run(
            [BASH, "-c", 'cygpath -m "$HOME"'],
            stdout=subprocess.PIPE,
            universal_newlines=True,
            env=self.env(),
            check=True,
        ).stdout.strip()
        write_json(self.profile / "settings.json", {})
        write_json(self.target, {"statusLine": {"type": "command", "command": f"{mixed_home}/status.sh"}})

        result = self.recover()

        self.assert_aborted_without_writes(result, "ガード A")
        self.assertIn(mixed_home, result.stderr)
        self.assertEqual(self.read("settings.json"), {})


if __name__ == "__main__":
    unittest.main()
