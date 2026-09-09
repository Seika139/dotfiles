import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from mise.scripts.render_hooks import format_sources, render


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

    def list_sources_with(self, base=None, local=None, target_content=None):
        with tempfile.TemporaryDirectory() as temp:
            profile_path = Path(temp) / "profile"
            profile_path.mkdir()
            if base is not None:
                (profile_path / "hooks.base.json").write_text(json.dumps(base), encoding="utf-8")
            if local is not None:
                (profile_path / "hooks.local.json").write_text(json.dumps(local), encoding="utf-8")

            target = Path(temp) / "hooks.json"
            if target_content is not None:
                target.write_text(json.dumps(target_content), encoding="utf-8")

            return format_sources(profile_path, target)

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

    def test_preserves_tagged_external_entries_from_existing_target(self):
        # An `_apm_source` tag is incidental now: preservation doesn't look
        # for it, but a tagged group must still survive like any other.
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

    def test_preserves_untagged_external_entries_from_existing_target(self):
        # The real `apm install -g` (e.g. DietrichGebert/ponytail) writes
        # hooks straight into the deploy target without any `_apm_source`
        # tag. Preservation must work on content diff alone, not tag lookup.
        base = {"hooks": {"Stop": [{"matcher": "base", "hooks": []}]}}
        target_content = {
            "hooks": {
                "Stop": [
                    {"matcher": "base", "hooks": []},
                    {"matcher": "external", "hooks": []},
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
                        {"matcher": "external", "hooks": []},
                    ]
                }
            },
        )

    def test_removed_base_entry_still_in_target_is_preserved_as_external(self):
        # Known limitation, pinned by this test: render() preserves every
        # existing target entry unconditionally, so an entry dropped from
        # hooks.base.json/hooks.local.json survives as long as a stale
        # target still has it. Delete the target file before `mise run
        # link` to actually clear it.
        target_content = {"hooks": {"Stop": [{"matcher": "removed-from-base", "hooks": []}]}}
        result = self.render_with(base={"hooks": {}}, target_content=target_content)
        self.assertEqual(result, {"hooks": {"Stop": [{"matcher": "removed-from-base", "hooks": []}]}})

    def test_malformed_target_warns_and_falls_back_to_base(self):
        # A structurally invalid target (as opposed to a dangling symlink or
        # unparsable JSON) must not silently erase every externally-managed
        # hook it holds; it should warn and fall back to base/local only.
        base = {"hooks": {"Stop": [{"matcher": "base", "hooks": []}]}}
        target_content = {"hooks": {"Stop": "not-a-list"}}
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = self.render_with(base=base, target_content=target_content)
        self.assertEqual(result, base)
        self.assertIn("malformed", stderr.getvalue())

    def test_skips_exact_duplicate_entries(self):
        base = {"hooks": {"Stop": [{"matcher": "dup", "hooks": []}]}}
        local = {"hooks": {"Stop": [{"matcher": "dup", "hooks": []}]}}
        result = self.render_with(base=base, local=local)
        self.assertEqual(result, {"hooks": {"Stop": [{"matcher": "dup", "hooks": []}]}})

    def test_symlink_target_external_entries_are_harvested(self):
        # Legacy deployments point `target` at a symlink; entries must be
        # read by following it, not skipped because it isn't a plain file.
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

    def test_base_matcher_group_string_raises(self):
        base = {"hooks": {"Stop": ["not-a-group"]}}
        with self.assertRaises(ValueError):
            self.render_with(base=base)

    def test_base_group_hooks_key_object_raises(self):
        base = {"hooks": {"Stop": [{"matcher": "base", "hooks": {"type": "command"}}]}}
        with self.assertRaises(ValueError):
            self.render_with(base=base)

    def test_base_group_hooks_entry_string_raises(self):
        base = {"hooks": {"Stop": [{"matcher": "base", "hooks": ["not-a-hook"]}]}}
        with self.assertRaises(ValueError):
            self.render_with(base=base)

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

    def test_list_sources_all_present(self):
        base = {"hooks": {"Stop": [{"matcher": "base", "hooks": []}]}}
        local = {"hooks": {"Stop": [{"matcher": "local", "hooks": []}]}}
        target_content = {
            "hooks": {
                "Stop": [
                    {"matcher": "apm-a", "hooks": [], "_apm_source": "ponytail"},
                    {"matcher": "apm-b", "hooks": [], "_apm_source": "ponytail"},
                    {"matcher": "apm-c", "hooks": [], "_apm_source": "other-pkg"},
                ]
            }
        }
        lines = self.list_sources_with(base=base, local=local, target_content=target_content)
        self.assertEqual(
            lines,
            [
                "hooks.base.json: 1 entries",
                "hooks.local.json: 1 entries",
                "apm (_apm_source=other-pkg): 1 entries",
                "apm (_apm_source=ponytail): 2 entries",
            ],
        )

    def test_list_sources_labels_untagged_external_entries(self):
        base = {"hooks": {"Stop": [{"matcher": "base", "hooks": []}]}}
        target_content = {
            "hooks": {
                "Stop": [
                    {"matcher": "base", "hooks": []},
                    {"matcher": "external", "hooks": []},
                    {"matcher": "apm-a", "hooks": [], "_apm_source": "ponytail"},
                ]
            }
        }
        lines = self.list_sources_with(base=base, target_content=target_content)
        self.assertEqual(
            lines,
            [
                "hooks.base.json: 1 entries",
                "hooks.local.json: (not present)",
                "apm (_apm_source=ponytail): 1 entries",
                "apm (untracked by profile): 1 entries",
            ],
        )

    def test_list_sources_dedupes_entry_shared_by_base_and_local(self):
        base = {"hooks": {"Stop": [{"matcher": "dup", "hooks": []}]}}
        local = {"hooks": {"Stop": [{"matcher": "dup", "hooks": []}]}}
        lines = self.list_sources_with(base=base, local=local)
        self.assertEqual(
            lines,
            [
                "hooks.base.json: 1 entries",
                "hooks.local.json: 0 entries",
                "apm: (not present)",
            ],
        )

    def test_list_sources_dedupes_entry_duplicated_within_base(self):
        base = {
            "hooks": {
                "Stop": [
                    {"matcher": "dup", "hooks": []},
                    {"matcher": "dup", "hooks": []},
                ]
            }
        }
        lines = self.list_sources_with(base=base)
        self.assertEqual(
            lines,
            [
                "hooks.base.json: 1 entries",
                "hooks.local.json: (not present)",
                "apm: (not present)",
            ],
        )

    def test_list_sources_none_present(self):
        lines = self.list_sources_with()
        self.assertEqual(
            lines,
            [
                "hooks.base.json: (not present)",
                "hooks.local.json: (not present)",
                "apm: (not present)",
            ],
        )

    def test_list_sources_handles_non_string_apm_source(self):
        # `_apm_source` is written by external tooling and is not validated
        # to be a string; render_hooks.py must not raise TypeError from an
        # unhashable dict key or fail sorted() on mixed str/None values.
        target_content = {
            "hooks": {
                "Stop": [
                    {"matcher": "apm-a", "hooks": [], "_apm_source": ["pkg-a", "pkg-b"]},
                    {"matcher": "apm-b", "hooks": [], "_apm_source": None},
                    {"matcher": "apm-c", "hooks": [], "_apm_source": "ponytail"},
                ]
            }
        }
        lines = self.list_sources_with(target_content=target_content)
        self.assertEqual(
            lines,
            [
                "hooks.base.json: (not present)",
                "hooks.local.json: (not present)",
                'apm (_apm_source=["pkg-a", "pkg-b"]): 1 entries',
                "apm (_apm_source=null): 1 entries",
                "apm (_apm_source=ponytail): 1 entries",
            ],
        )

    def test_list_sources_normalizes_multiline_apm_source_string(self):
        # A crafted `_apm_source` string containing a newline must not be
        # allowed to split the "composed from" breakdown into extra lines
        # that could be mistaken for additional legitimate entries.
        target_content = {
            "hooks": {
                "Stop": [
                    {"matcher": "apm-a", "hooks": [], "_apm_source": "pkg\n   ❌ forged"},
                    {"matcher": "apm-b", "hooks": [], "_apm_source": "ponytail"},
                ]
            }
        }
        lines = self.list_sources_with(target_content=target_content)
        self.assertEqual(
            lines,
            [
                "hooks.base.json: (not present)",
                "hooks.local.json: (not present)",
                'apm (_apm_source="pkg\\n   ❌ forged"): 1 entries',
                "apm (_apm_source=ponytail): 1 entries",
            ],
        )


if __name__ == "__main__":
    unittest.main()
