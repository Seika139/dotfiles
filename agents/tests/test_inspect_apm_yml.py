from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "mise" / "scripts" / "inspect_apm_yml.py"


class InspectApmYmlTest(unittest.TestCase):
    def _run_inspector(self, base: str, overlay: str | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "base.yml"
            base_path.write_text(textwrap.dedent(base), encoding="utf-8")
            command = [sys.executable, str(SCRIPT_PATH), "--base", str(base_path)]
            if overlay is not None:
                overlay_path = Path(temp_dir) / "overlay.yml"
                overlay_path.write_text(textwrap.dedent(overlay), encoding="utf-8")
                command.extend(["--overlay", str(overlay_path)])

            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        return result.stdout.splitlines()

    def test_extracts_names_from_string_and_object_dependencies(self) -> None:
        output = self._run_inspector(
            """
            targets: [claude, codex]
            dependencies:
              apm:
                - Caromaf/agent-package-basic/packages/review-pr#main
                - git: Caromaf/agent-package-basic
                  path: packages/agent-team
                  ref: main
                  targets: [claude]
            """
        )

        self.assertEqual(
            output,
            [
                "target\tclaude",
                "target\tcodex",
                "apm-base\treview-pr",
                "apm-base\tagent-team",
                "apm-merged\treview-pr",
                "apm-merged\tagent-team",
            ],
        )

    def test_deduplicates_names_across_base_and_overlay_forms(self) -> None:
        output = self._run_inspector(
            """
            dependencies:
              apm:
                - git: Caromaf/agent-package-basic
                  path: packages/agent-team
                  ref: main
                  targets: [claude]
            """,
            """
            dependencies:
              apm:
                - Caromaf/agent-package-basic/packages/agent-team#main
                - example/tools/packages/private-tool#main
            """,
        )

        self.assertEqual(
            output,
            [
                "apm-base\tagent-team",
                "apm-overlay\tagent-team",
                "apm-overlay\tprivate-tool",
                "apm-merged\tagent-team",
                "apm-merged\tprivate-tool",
            ],
        )


if __name__ == "__main__":
    unittest.main()
