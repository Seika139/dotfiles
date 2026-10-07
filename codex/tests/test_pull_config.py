import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mise.scripts.pull_config import split_runtime


class PullConfigTest(unittest.TestCase):
    def test_drops_base_entries_missing_from_runtime(self):
        new_base, new_local = split_runtime({}, {"setting": "value"})

        self.assertEqual(new_base, {})
        self.assertEqual(new_local, {})

    def test_main_succeeds_with_cp932_stdout(self):
        script = Path(__file__).parents[1] / "mise" / "scripts" / "pull_config.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runtime_path = root / "config.toml"
            profile_path = root / "profile"
            profile_path.mkdir()
            runtime_path.write_text('feature = "enabled"\n', encoding="utf-8")

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "cp932"
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--runtime",
                    str(runtime_path),
                    "--profile-path",
                    str(profile_path),
                ],
                env=env,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr.decode("cp932", errors="replace"))
            self.assertIn(b"Updated", result.stdout)


if __name__ == "__main__":
    unittest.main()
