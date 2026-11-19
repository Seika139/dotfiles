import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
AGENTS_DIR = ROOT_DIR / "agents"
BASH = shutil.which("bash") or "bash"


class InstallLockDriftTest(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "installer integration fixture targets Unix shells")
    def test_lock_drift_retries_without_frozen_and_preserves_force(self):
        result, events, profile_lock, backups = self._run_install("drift", force=True)

        self.assertEqual(result.returncode, 0, "stdout:\n{}\nstderr:\n{}".format(result.stdout, result.stderr))
        self.assertEqual(events, [
            "install -g --frozen --dry-run --force",
            "install -g --force",
        ])
        self.assertEqual(profile_lock, "updated lock\n")
        self.assertEqual(len(backups), 3)
        self.assertEqual(set(backups), {
            "old lock\n",
            "existing global lock\n",
            "pre-existing stale backup\n",
        })

    @unittest.skipIf(os.name == "nt", "installer integration fixture targets Unix shells")
    def test_other_frozen_preflight_failures_do_not_retry(self):
        result, events, _, backups = self._run_install("policy", force=False)

        self.assertEqual(result.returncode, 23, "stdout:\n{}\nstderr:\n{}".format(result.stdout, result.stderr))
        self.assertEqual(events, ["install -g --frozen --dry-run"])
        self.assertEqual(backups, [])

    def _run_install(self, behavior, force):
        with tempfile.TemporaryDirectory(prefix=".install-lock-drift-", dir=str(AGENTS_DIR / "profiles")) as directory:
            profile = Path(directory)
            (profile / "apm.yml").write_text("name: fixture\nversion: 0.1.0\n", encoding="utf-8")
            source_lock = profile / "apm.lock.yaml"
            source_lock.write_text("old lock\n", encoding="utf-8")

            home = profile / "home"
            fake_bin = profile / "bin"
            home.mkdir()
            fake_bin.mkdir()
            if behavior == "drift":
                apm_home = home / ".apm"
                apm_home.mkdir()
                (apm_home / "apm.lock.yaml").write_text("existing global lock\n", encoding="utf-8")
                (apm_home / "apm.lock.yaml.backup.20260101_000000.stale").write_text(
                    "pre-existing stale backup\n", encoding="utf-8"
                )
            event_log = profile / "apm-events.log"
            fake_apm = fake_bin / "apm"
            fake_apm.write_text(
                "#!/usr/bin/env bash\n"
                "set -eu\n"
                "printf '%s\\n' \"$*\" >>\"$EVENT_LOG\"\n"
                "if [[ \" $* \" == *\" --dry-run \"* ]]; then\n"
                "  if [[ \"$FAKE_APM_BEHAVIOR\" == drift ]]; then\n"
                "    printf '%s\\n' 'Error: --frozen: apm.lock.yaml is out of sync with apm.yml.' >&2\n"
                "    exit 1\n"
                "  fi\n"
                "  printf '%s\\n' 'Error: security policy blocked install.' >&2\n"
                "  exit 23\n"
                "fi\n"
                "if [[ \" $* \" == *\" --frozen \"* ]]; then exit 90; fi\n"
                "printf '%s\\n' 'updated lock' >\"$HOME/.apm/apm.lock.yaml\"\n",
                encoding="utf-8",
            )
            fake_apm.chmod(0o755)
            fake_date = fake_bin / "date"
            fake_date.write_text("#!/usr/bin/env bash\nprintf '%s\\n' 20260101_000000\n", encoding="utf-8")
            fake_date.chmod(0o755)

            env = {
                **os.environ,
                "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
                "HOME": str(home),
                "PROFILES_DIR": "profiles",
                "DEFAULT_AGENTS_PROFILE": profile.name,
                "EVENT_LOG": str(event_log),
                "FAKE_APM_BEHAVIOR": behavior,
                "usage_force": "true" if force else "false",
            }
            result = subprocess.run(
                [BASH, str(AGENTS_DIR / "mise/tasks/install.sh")],
                cwd=str(ROOT_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            events = event_log.read_text(encoding="utf-8").splitlines()
            backups = [path.read_text(encoding="utf-8") for path in (home / ".apm").glob("apm.lock.yaml.backup.*")]
            return result, events, source_lock.read_text(encoding="utf-8"), backups


if __name__ == "__main__":
    unittest.main()
