import os
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "mise" / "scripts" / "sync_agents.sh"
MANIFEST_NAME = ".codex-dotfiles-native-agents.manifest"


def bash_path(path: Path) -> str:
    value = str(path)
    converter = shutil.which("cygpath") or shutil.which("wslpath")
    if not converter:
        probe = subprocess.run(
            ["bash", "-lc", "command -v cygpath || command -v wslpath"],
            check=False,
            capture_output=True,
            text=True,
        )
        converter = probe.stdout.strip() or None
    if converter:
        return subprocess.run(
            ["bash", "-lc", f"{shlex.quote(converter)} -u {shlex.quote(value)}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    return value.replace("\\", "/")


class NativeAgentSyncTest(unittest.TestCase):
    def run_sync(self, home: Path, *, source_root: Path = ROOT, env=None):
        command_env = os.environ.copy()
        if env:
            command_env.update(env)
        result = subprocess.run(
            ["bash", bash_path(SYNC), bash_path(source_root), bash_path(home)],
            check=False,
            env=command_env,
            capture_output=True,
        )
        result.stdout = result.stdout.decode("utf-8", errors="replace")
        result.stderr = result.stderr.decode("utf-8", errors="replace")
        return result

    def test_installs_regular_files_and_backs_up_first_collision(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            target = home / "agents"
            target.mkdir(parents=True)
            existing = target / "implementor.toml"
            existing.write_text("local = true\n", encoding="utf-8")

            result = self.run_sync(home)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(existing.is_file())
            self.assertFalse(existing.is_symlink())
            self.assertIn('name = "implementor"', existing.read_text(encoding="utf-8"))
            backups = list(target.glob("implementor.toml.backup.*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "local = true\n")
            self.assertIn("implementor.toml", (home / MANIFEST_NAME).read_text(encoding="utf-8"))

    def test_managed_update_replaces_without_new_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            first = self.run_sync(home)
            self.assertEqual(first.returncode, 0, first.stderr)
            target = home / "agents" / "implementor.toml"
            backups_before = list(target.parent.glob("implementor.toml.backup.*"))

            source = ROOT / "agents" / "implementor.toml"
            original = source.read_text(encoding="utf-8")
            try:
                source.write_text(original + "\n# test update\n", encoding="utf-8")
                second = self.run_sync(home)
            finally:
                source.write_text(original, encoding="utf-8")

            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("# test update", target.read_text(encoding="utf-8"))
            self.assertEqual(list(target.parent.glob("implementor.toml.backup.*")), backups_before)

    def test_removes_only_stale_managed_file_and_preserves_unmanaged(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            first = self.run_sync(home)
            self.assertEqual(first.returncode, 0, first.stderr)
            target = home / "agents"
            stale = target / "removed.toml"
            stale.write_text("stale = true\n", encoding="utf-8")
            unmanaged = target / "unmanaged.toml"
            unmanaged.write_text("name = 'other'\n", encoding="utf-8")
            manifest = home / MANIFEST_NAME
            manifest.write_text(
                manifest.read_text(encoding="utf-8") + "removed.toml\n",
                encoding="utf-8",
            )

            result = self.run_sync(home)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(stale.exists())
            self.assertTrue(unmanaged.exists())
            self.assertIn("stale managed agent", result.stdout)


if __name__ == "__main__":
    unittest.main()
