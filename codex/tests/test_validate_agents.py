import tempfile
import unittest
from pathlib import Path

from mise.scripts.validate_agents import validate


VALID = """
name = "example"
description = "An example agent"
model = "gpt-5.6"
model_reasoning_effort = "medium"
developer_instructions = "Review without changing files."
sandbox_mode = "workspace-write"
"""


class ValidateAgentsTest(unittest.TestCase):
    def validate_text(self, text: str, filename: str = "example.toml"):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / filename
            path.write_text(text, encoding="utf-8")
            return validate(path.parent)

    def test_accepts_valid_definition(self):
        self.assertEqual(self.validate_text(VALID), [])

    def test_rejects_empty_required_strings(self):
        errors = self.validate_text(VALID.replace('description = "An example agent"', 'description = ""'))
        self.assertTrue(any("description" in error for error in errors))

    def test_rejects_invalid_reasoning_effort_and_sandbox(self):
        errors = self.validate_text(VALID.replace('"medium"', '"extreme"').replace('"workspace-write"', '"invalid"'))
        self.assertTrue(any("model_reasoning_effort" in error for error in errors))
        self.assertTrue(any("sandbox_mode" in error for error in errors))

    def test_rejects_non_string_reasoning_effort_and_sandbox(self):
        text = VALID.replace('"medium"', '["medium"]').replace('"workspace-write"', '["workspace-write"]')
        errors = self.validate_text(text)
        self.assertTrue(any("model_reasoning_effort" in error for error in errors))
        self.assertTrue(any("sandbox_mode" in error for error in errors))

    def test_reviewers_require_read_only_sandbox(self):
        text = VALID.replace('name = "example"', 'name = "code-reviewer"')
        errors = self.validate_text(text, "code-reviewer.toml")
        self.assertTrue(any("read-only" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
