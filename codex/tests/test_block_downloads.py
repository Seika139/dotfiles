import io
import json
import ntpath
import unittest
from pathlib import Path
from unittest.mock import patch

from mise.scripts import block_downloads


class BlockDownloadsTest(unittest.TestCase):
    def test_downloads_itself_and_descendants_match_but_prefix_siblings_do_not(self):
        downloads = Path("/home/user/Downloads")
        self.assertTrue(block_downloads.is_in_downloads("/home/user/Downloads", downloads))
        self.assertTrue(block_downloads.is_in_downloads("/home/user/Downloads/nested", downloads))
        self.assertFalse(block_downloads._is_within("/home/user/Downloads-old", str(downloads), windows=False))

    def test_resolved_paths_match_symlink_aliases(self):
        with patch.object(Path, "resolve", side_effect=[Path("C:/Users/me/Downloads/nested"), Path("C:/Users/me/Downloads")]):
            self.assertTrue(
                block_downloads.is_in_downloads(
                    "C:/Users/me/alias/nested",
                    Path("C:/Users/me/Downloads"),
                    windows=True,
                )
            )

    def test_windows_and_wsl_drvfs_paths_are_case_insensitive_and_component_aware(self):
        self.assertTrue(
            block_downloads._is_within(
                r"C:\Users\Example\DOWNLOADS\Nested",
                r"c:\users\example\Downloads",
                windows=True,
            )
        )
        self.assertTrue(
            block_downloads._is_within(
                "/mnt/d/user/DOWNLOADS/nested",
                "/mnt/d/User/Downloads",
                windows=True,
            )
        )
        self.assertFalse(
            block_downloads._is_within(
                r"C:\Users\Example\Downloads-old",
                r"C:\Users\Example\Downloads",
                windows=True,
            )
        )

    def test_xdg_download_path_expands_home_and_supports_spaces(self):
        home = Path("/home/example")
        config = Path("/tmp/xdg")
        with patch.object(Path, "read_text", return_value='XDG_DOWNLOAD_DIR="$HOME/Received Files"\n'):
            result = block_downloads.linux_downloads_dir(home, {"XDG_CONFIG_HOME": str(config)})
        self.assertEqual(result, home / "Received Files")

    def test_xdg_download_dir_pointing_to_home_fails_closed(self):
        home = Path("/home/example")
        with patch.object(Path, "read_text", return_value='XDG_DOWNLOAD_DIR="$HOME"\n'):
            with self.assertRaisesRegex(RuntimeError, "points to HOME"):
                block_downloads.linux_downloads_dir(home, {"XDG_CONFIG_HOME": "/tmp/xdg"})

    def test_xdg_config_is_not_executed_and_invalid_values_fail_closed(self):
        home = Path("/home/example")
        with patch.object(Path, "read_text", return_value='XDG_DOWNLOAD_DIR="$HOME/$(touch marker)"\n'):
            with self.assertRaises(RuntimeError):
                block_downloads.linux_downloads_dir(home, {"XDG_CONFIG_HOME": "/tmp/xdg"})

    def test_missing_xdg_config_uses_default_downloads_directory(self):
        home = Path("/home/example")
        with patch.object(Path, "read_text", side_effect=FileNotFoundError):
            result = block_downloads.linux_downloads_dir(home, {"XDG_CONFIG_HOME": "/tmp/xdg"})
        self.assertEqual(result, home / "Downloads")

    def test_wsl_windows_download_path_is_translated(self):
        completed = [
            type("Result", (), {"stdout": "D:\\User\\Saved Files\\Downloads\n"})(),
            type("Result", (), {"stdout": "/mnt/d/User/Saved Files/Downloads\n"})(),
        ]
        with (
            patch.object(block_downloads, "_is_wsl", return_value=True),
            patch.object(block_downloads.shutil, "which", side_effect=["powershell.exe", "wslpath"]),
            patch.object(block_downloads.subprocess, "run", side_effect=completed) as run,
        ):
            result = block_downloads.wsl_windows_downloads_dir()
        self.assertEqual(result, Path("/mnt/d/User/Saved Files/Downloads"))
        self.assertIn("374DE290-123F-4565-9164-39C4925E467B", run.call_args_list[0].args[0][-1])
        self.assertEqual(run.call_args_list[1].args[0][-1], r"D:\User\Saved Files\Downloads")

    def test_wsl_without_interop_tools_fails_closed(self):
        with (
            patch.object(block_downloads, "_is_wsl", return_value=True),
            patch.object(block_downloads.shutil, "which", return_value=None),
        ):
            with self.assertRaisesRegex(RuntimeError, "cannot verify Windows Downloads"):
                block_downloads.wsl_windows_downloads_dir()

    def test_mac_download_location_uses_home_downloads(self):
        with patch.object(Path, "home", return_value=Path("/Users/example")):
            self.assertEqual(block_downloads.downloads_dirs("darwin"), [Path("/Users/example/Downloads")])

    def test_prompt_is_blocked_in_downloads_and_allowed_elsewhere(self):
        downloads = Path("C:/Users/example/Downloads")
        with (
            patch.object(block_downloads, "downloads_dirs", return_value=[downloads]),
            patch.object(block_downloads, "is_in_downloads", side_effect=[True, False]),
        ):
            blocked_stderr = io.StringIO()
            blocked = block_downloads.main(
                io.StringIO(json.dumps({"cwd": "C:/Users/example/Downloads"})),
                blocked_stderr,
                system="win32",
            )
            allowed = block_downloads.main(
                io.StringIO(json.dumps({"cwd": "C:/Users/example/project"})),
                io.StringIO(),
                system="win32",
            )
        self.assertEqual(blocked, 2)
        self.assertIn("Downloads", blocked_stderr.getvalue())
        self.assertEqual(allowed, 0)

    def test_windows_absolute_cwd_is_validated_with_windows_path_rules(self):
        with patch.object(block_downloads, "downloads_dirs", return_value=[Path("C:/Users/example/Downloads")]):
            with patch.object(block_downloads, "is_in_downloads", return_value=False):
                result = block_downloads.main(
                    io.StringIO(json.dumps({"cwd": "C:/Users/example/project"})),
                    io.StringIO(),
                    system="win32",
                )
        self.assertTrue(ntpath.isabs("C:/Users/example/project"))
        self.assertEqual(result, 0)

    def test_malformed_or_missing_cwd_fails_closed(self):
        with patch.object(block_downloads, "downloads_dirs") as get_dirs:
            stderr = io.StringIO()
            result = block_downloads.main(io.StringIO('{"cwd": null}'), stderr, system="linux")
        self.assertEqual(result, 2)
        self.assertIn("could not verify", stderr.getvalue())
        get_dirs.assert_not_called()

    def test_unresolvable_paths_fail_closed(self):
        with (
            patch.object(block_downloads, "downloads_dirs", return_value=[Path("C:/Users/example/Downloads")]),
            patch.object(block_downloads, "is_in_downloads", side_effect=RuntimeError("cannot resolve")),
        ):
            stderr = io.StringIO()
            result = block_downloads.main(
                io.StringIO(json.dumps({"cwd": "C:/Users/example/project"})),
                stderr,
                system="win32",
            )
        self.assertEqual(result, 2)
        self.assertIn("could not verify", stderr.getvalue())

    def test_every_codex_profile_has_the_global_guard_hook(self):
        profiles = Path(__file__).parents[1] / "profiles"
        for profile in profiles.iterdir():
            with self.subTest(profile=profile.name):
                hooks = json.loads((profile / "hooks.base.json").read_text(encoding="utf-8"))["hooks"]
                handlers = [
                    hook
                    for group in hooks["UserPromptSubmit"]
                    for hook in group["hooks"]
                    if hook.get("type") == "command"
                ]
                if profile.name == "win-15034":
                    self.assertTrue(
                        any("block_downloads.py" in hook.get("commandWindows", "") for hook in handlers),
                        f"{profile.name} has no Windows Downloads guard",
                    )
                else:
                    self.assertTrue(
                        any("block_downloads.sh" in hook.get("command", "") for hook in handlers),
                        f"{profile.name} has no Unix Downloads guard",
                    )

    def test_existing_profile_hooks_are_preserved(self):
        profiles = Path(__file__).parents[1] / "profiles"
        hm_hooks = json.loads((profiles / "hm-m1-mac/hooks.base.json").read_text(encoding="utf-8"))["hooks"]
        hm_commands = [
            hook["command"]
            for group in hm_hooks["UserPromptSubmit"]
            for hook in group["hooks"]
            if hook.get("type") == "command"
        ]
        self.assertTrue(any("ponytail-mode-tracker.js" in command for command in hm_commands))

        windows_hooks = json.loads((profiles / "win-15034/hooks.base.json").read_text(encoding="utf-8"))["hooks"]
        self.assertIn("Stop", windows_hooks)


if __name__ == "__main__":
    unittest.main()
