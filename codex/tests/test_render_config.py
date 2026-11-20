import tempfile
import tomllib
import unittest
from pathlib import Path

from mise.scripts.render_config import config_diff_lines, render


class RenderConfigTest(unittest.TestCase):
    def test_reports_only_semantically_changed_keys(self):
        actual = {
            "model": "gpt-5",
            "skills": {"config": [{"path": r"C:\Users\S13316\.codex\skills\hatch-pet\SKILL.md", "enabled": False}]},
        }
        expected = {
            "model": "gpt-5",
            "skills": {"config": [{"path": r"C:\Users\S13316\.codex\skills\hatch-pet\SKILL.md", "enabled": True}]},
        }

        self.assertEqual(
            config_diff_lines(actual, expected),
            ["~ skills.config[0].enabled: false -> true"],
        )

    def test_ignores_mapping_order(self):
        self.assertEqual(
            config_diff_lines({"a": 1, "b": 2}, {"b": 2, "a": 1}),
            [],
        )

    def test_render_preserves_runtime_plugins_and_marketplaces(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / "profile"
            profile.mkdir()
            profile_config = profile / "config.base.toml"
            profile_config.write_text(
                '[plugins.ponytail]\nenabled = true\n'
                '[marketplaces.ponytail]\nsource = "profile"\n',
                encoding="utf-8",
            )
            runtime_config = root / "config.toml"
            runtime_config.write_text(
                '[plugins.ponytail]\nenabled = false\nchannel = "stable"\n'
                '[plugins.private-plugin]\nenabled = true\n'
                '[marketplaces.ponytail]\nsource = "runtime"\n'
                '[marketplaces.private]\nsource = "local"\n',
                encoding="utf-8",
            )

            content, _sources = render(profile, runtime_config)

        rendered = tomllib.loads(content)
        self.assertEqual(
            rendered["plugins"],
            {
                "ponytail": {"enabled": True, "channel": "stable"},
                "private-plugin": {"enabled": True},
            },
        )
        self.assertEqual(
            rendered["marketplaces"],
            {
                "ponytail": {"source": "profile"},
                "private": {"source": "local"},
            },
        )


if __name__ == "__main__":
    unittest.main()
