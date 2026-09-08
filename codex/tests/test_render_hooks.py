import json
import os
import tempfile
import unittest
from pathlib import Path

from mise.scripts.render_hooks import render


class RenderHooksTest(unittest.TestCase):
    def render_with(self, base=None, local=None, target_content=None, target_is_symlink=False):
        with tempfile.TemporaryDirectory() as temp:
            profile_path = Path(temp) / "profile"
            profile_path.mkdir()
            if base is not None:
                (profile_path / "hooks.base.json").write_text(json.dumps(base), encoding="utf-8")
            if local is not None:
                (profile_path / "hooks.local.json").write_text(json.dumps(local), encoding="utf-8")

            target = Path(temp) / "hooks.json"
            if target_is_symlink:
                real = Path(temp) / "hooks.real.json"
                real.write_text(json.dumps(target_content or {"hooks": {}}), encoding="utf-8")
                os.symlink(real, target)
            elif target_content is not None:
                target.write_text(json.dumps(target_content), encoding="utf-8")

            return render(profile_path, target)

    def test_base_only(self):
        base = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo hi"}]}]}}
        result = self.render_with(base=base)
        self.assertEqual(result, base)

    def test_base_and_local_merge_in_order(self):
        base = {"hooks": {"Stop": [{"matcher": "base", "hooks": []}]}}
        local = {"hooks": {"Stop": [{"matcher": "local", "hooks": []}]}}
        result = self.render_with(base=base, local=local)
        self.assertEqual(
            result,
            {"hooks": {"Stop": [{"matcher": "base", "hooks": []}, {"matcher": "local", "hooks": []}]}},
        )

    def test_preserves_apm_source_entries_from_existing_target(self):
        base = {"hooks": {"Stop": [{"matcher": "base", "hooks": []}]}}
        target_content = {
            "hooks": {
                "Stop": [
                    {"matcher": "base", "hooks": []},
                    {"matcher": "apm", "hooks": [], "_apm_source": "some-package"},
                ]
            }
        }
        result = self.render_with(base=base, target_content=target_content)
        self.assertEqual(
            result,
            {
                "hooks": {
                    "Stop": [
                        {"matcher": "base", "hooks": []},
                        {"matcher": "apm", "hooks": [], "_apm_source": "some-package"},
                    ]
                }
            },
        )

    def test_skips_exact_duplicate_entries(self):
        base = {"hooks": {"Stop": [{"matcher": "dup", "hooks": []}]}}
        local = {"hooks": {"Stop": [{"matcher": "dup", "hooks": []}]}}
        result = self.render_with(base=base, local=local)
        self.assertEqual(result, {"hooks": {"Stop": [{"matcher": "dup", "hooks": []}]}})

    def test_symlink_target_preserves_apm_source(self):
        base = {"hooks": {"Stop": [{"matcher": "base", "hooks": []}]}}
        target_content = {
            "hooks": {
                "Stop": [{"matcher": "apm", "hooks": [], "_apm_source": "some-package"}],
            }
        }
        result = self.render_with(base=base, target_content=target_content, target_is_symlink=True)
        self.assertEqual(
            result,
            {
                "hooks": {
                    "Stop": [
                        {"matcher": "base", "hooks": []},
                        {"matcher": "apm", "hooks": [], "_apm_source": "some-package"},
                    ]
                }
            },
        )

    def test_base_event_value_object_raises(self):
        base = {"hooks": {"Stop": {"hooks": []}}}
        with self.assertRaises(ValueError):
            self.render_with(base=base)

    def test_local_event_value_string_raises(self):
        base = {"hooks": {"Stop": [{"matcher": "base", "hooks": []}]}}
        local = {"hooks": {"Stop": "not-a-list"}}
        with self.assertRaises(ValueError):
            self.render_with(base=base, local=local)

    def test_broken_symlink_target_is_treated_as_empty(self):
        base = {"hooks": {"Stop": [{"matcher": "base", "hooks": []}]}}
        with tempfile.TemporaryDirectory() as temp:
            profile_path = Path(temp) / "profile"
            profile_path.mkdir()
            (profile_path / "hooks.base.json").write_text(json.dumps(base), encoding="utf-8")

            target = Path(temp) / "hooks.json"
            os.symlink(Path(temp) / "does-not-exist.json", target)

            result = render(profile_path, target)
        self.assertEqual(result, base)


if __name__ == "__main__":
    unittest.main()
