import unittest

from mise.scripts.pull_config import split_runtime


class PullConfigTest(unittest.TestCase):
    def test_drops_base_entries_missing_from_runtime(self):
        new_base, new_local = split_runtime({}, {"setting": "value"})

        self.assertEqual(new_base, {})
        self.assertEqual(new_local, {})


if __name__ == "__main__":
    unittest.main()
