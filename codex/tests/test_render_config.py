import unittest

from mise.scripts.render_config import config_diff_lines


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


if __name__ == "__main__":
    unittest.main()
