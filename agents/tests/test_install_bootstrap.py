import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
BASH = shutil.which("bash") or "bash"


class InstallBootstrapTest(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "root installer integration fixture targets Unix shells")
    def test_python_setup_runs_after_mise_install_and_environment_load(self):
        with tempfile.TemporaryDirectory(prefix="dotfiles bootstrap ") as directory:
            fixture = self._create_fixture(Path(directory), fail_install=False)
            result = self._run_installer(fixture)

            self.assertEqual(
                result.returncode,
                0,
                "stdout:\n{}\nstderr:\n{}".format(result.stdout, result.stderr),
            )
            events = fixture["event_log"].read_text(encoding="utf-8").splitlines()
            install_index = events.index("mise-install")
            env_index = events.index("mise-env")
            first_python_index = events.index("python")
            link_index = events.index("mise-run-link")
            self.assertLess(install_index, env_index)
            self.assertLess(env_index, first_python_index)
            self.assertLess(first_python_index, link_index)

            cursor_home = fixture["home"] / ".cursor"
            self.assertTrue(cursor_home.is_dir())
            self.assertFalse(cursor_home.is_symlink())
            self.assertEqual(len(list(fixture["home"].glob(".cursor.legacy-link.*"))), 1)

    @unittest.skipIf(os.name == "nt", "root installer integration fixture targets Unix shells")
    def test_mise_install_failure_leaves_legacy_cursor_link_untouched(self):
        with tempfile.TemporaryDirectory(prefix="dotfiles bootstrap ") as directory:
            fixture = self._create_fixture(Path(directory), fail_install=True)
            original_target = os.readlink(fixture["home"] / ".cursor")
            result = self._run_installer(fixture)

            self.assertEqual(result.returncode, 47, "stdout:\n{}\nstderr:\n{}".format(result.stdout, result.stderr))
            cursor_home = fixture["home"] / ".cursor"
            self.assertTrue(cursor_home.is_symlink())
            self.assertEqual(os.readlink(cursor_home), original_target)
            self.assertEqual(fixture["event_log"].read_text(encoding="utf-8").splitlines(), ["mise-install"])

    def test_windows_shell_loads_cygpath_shims_without_evaluating_mise_env(self):
        with tempfile.TemporaryDirectory(prefix="mise shims fixture ") as directory:
            root = Path(directory)
            home = root / "home"
            fake_bin = root / "bin"
            shims = root / "local app data" / "mise" / "shims"
            event_log = root / "events.log"
            home.mkdir()
            fake_bin.mkdir()
            shims.parent.mkdir(parents=True)
            helper = root / "load_mise_environment.sh"
            shutil.copy2(
                str(ROOT_DIR / "agents/mise/scripts/load_mise_environment.sh"),
                str(helper),
            )

            self._write_executable(
                fake_bin / "cygpath",
                "#!/usr/bin/env bash\nprintf '%s\\n' \"$TEST_MISE_SHIMS_POSIX\"\n",
            )
            self._write_executable(
                fake_bin / "mise",
                "#!/usr/bin/env bash\n"
                "case \"${1:-}\" in\n"
                "  reshim) mkdir -p \"$TEST_MISE_SHIMS_POSIX\"; printf '%s\\n' mise-reshim >>\"$EVENT_LOG\" ;;\n"
                "  env) printf '%s\\n' mise-env-called >>\"$EVENT_LOG\"; printf 'exit 99\\n' ;;\n"
                "  *) exit 2 ;;\n"
                "esac\n",
            )
            env = {
                **os.environ,
                "TEST_MISE_FAKE_BIN": self._bash_path(fake_bin),
                "TEST_MISE_SHIMS_POSIX": self._bash_path(shims),
                "EVENT_LOG": self._bash_path(event_log),
            }
            command = [
                BASH,
                "-c",
                'export PATH="$TEST_MISE_FAKE_BIN:$PATH"; source "$1"; dotfiles_load_mise_environment "$2" msys; printf "%s\\n" "$PATH"',
                "test-mise-environment",
                self._bash_path(helper),
                self._bash_path(home),
            ]
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=env,
            )

            self.assertEqual(
                result.returncode,
                0,
                "stdout:\n{}\nstderr:\n{}".format(result.stdout, result.stderr),
            )
            self.assertTrue(shims.is_dir())
            self.assertTrue(result.stdout.splitlines()[0].startswith(self._bash_path(shims)))
            self.assertEqual(event_log.read_text(encoding="utf-8").splitlines(), ["mise-reshim"])

    def _create_fixture(self, directory, fail_install):
        root = directory / "dotfiles"
        home = directory / "home"
        fake_bin = directory / "bin"
        mise_shims = directory / "mise shims"
        event_log = directory / "events.log"
        root.mkdir()
        home.mkdir()
        fake_bin.mkdir()
        mise_shims.mkdir()

        for command in (
            "bash",
            "cat",
            "chmod",
            "cp",
            "cut",
            "date",
            "diff",
            "dirname",
            "find",
            "grep",
            "ln",
            "mkdir",
            "mktemp",
            "mv",
            "readlink",
            "rm",
            "sed",
            "touch",
        ):
            source = shutil.which(command)
            if source:
                (fake_bin / command).symlink_to(source)

        self._write_executable(
            fake_bin / "uname",
            "#!/usr/bin/env bash\nprintf '%s\\n' Darwin\n",
        )
        self._write_executable(
            fake_bin / "brew",
            "#!/usr/bin/env bash\nexit 0\n",
        )
        self._write_executable(
            fake_bin / "git",
            "#!/usr/bin/env bash\n"
            "if [[ \"$1\" == config && \"$#\" -eq 3 && \"$3\" == init.templatedir ]]; then exit 1; fi\n"
            "if [[ \"$1\" == config && \"$#\" -eq 2 ]]; then exit 1; fi\n"
            "exit 0\n",
        )
        self._write_executable(
            fake_bin / "mise",
            "#!/usr/bin/env bash\n"
            "set -eu\n"
            "case \"${1:-}\" in\n"
            "  install)\n"
            "    printf '%s\\n' mise-install >>\"$EVENT_LOG\"\n"
            f"    if [[ \"${{FAIL_MISE_INSTALL:-0}}\" == 1 ]]; then exit 47; fi\n"
            "    command -v python3 >/dev/null 2>&1 && exit 96\n"
            "    mkdir -p \"$TEST_MISE_SHIMS\"\n"
            "    cat >\"$TEST_MISE_SHIMS/python3\" <<'PYTHON_SHIM'\n"
            "#!/usr/bin/env bash\n"
            "printf '%s\\n' python >>\"$EVENT_LOG\"\n"
            "exec \"$FIXTURE_REAL_PYTHON\" \"$@\"\n"
            "PYTHON_SHIM\n"
            "    chmod +x \"$TEST_MISE_SHIMS/python3\"\n"
            "    ;;\n"
            "  env)\n"
            "    printf '%s\\n' mise-env >>\"$EVENT_LOG\"\n"
            "    printf 'export PATH=%q:$PATH\\n' \"$TEST_MISE_SHIMS\"\n"
            "    ;;\n"
            "  trust) exit 0 ;;\n"
            "  run)\n"
            "    printf 'mise-run-%s\\n' \"$2\" >>\"$EVENT_LOG\"\n"
            "    if [[ \"$2\" == link ]]; then\n"
            "      command -v python3 >/dev/null 2>&1 || exit 98\n"
            "      bash \"$DOTFILES_ROOT/claude/mise/scripts/run_python.sh\" \\\n"
            "        \"$DOTFILES_ROOT/claude/mise/scripts/normalize_ponytail_hooks.py\" \\\n"
            "        --claude-dir \"$HOME/.claude\"\n"
            "    fi\n"
            "    ;;\n"
            "  *) exit 2 ;;\n"
            "esac\n",
        )

        self._copy(root / "install.sh", ROOT_DIR / "install.sh")
        self._copy(root / "agents/mise/scripts/cursor_home.sh", ROOT_DIR / "agents/mise/scripts/cursor_home.sh")
        self._copy(
            root / "agents/mise/scripts/migrate_cursor_apm_config.py",
            ROOT_DIR / "agents/mise/scripts/migrate_cursor_apm_config.py",
        )
        self._copy(root / "claude/mise/scripts/run_python.sh", ROOT_DIR / "claude/mise/scripts/run_python.sh")
        self._copy(
            root / "claude/mise/scripts/normalize_ponytail_hooks.py",
            ROOT_DIR / "claude/mise/scripts/normalize_ponytail_hooks.py",
        )
        self._copy(
            root / "agents/mise/scripts/load_mise_environment.sh",
            ROOT_DIR / "agents/mise/scripts/load_mise_environment.sh",
        )

        (root / "mise/profiles").mkdir(parents=True)
        (root / "mise/profiles/default.toml").write_text("[tools]\n", encoding="utf-8")
        (root / "mise/global.toml").write_text("", encoding="utf-8")
        (root / "bash/daily").mkdir(parents=True)
        (root / ".bash_profile").write_text(
            'info() { :; }\nerror() { printf "%s\\n" "$*" >&2; }\n',
            encoding="utf-8",
        )
        (root / ".active-profile").write_text("default\n", encoding="utf-8")
        (root / ".cursor").mkdir()
        (root / ".cursor/mcp.json").write_text(
            json.dumps({"mcpServers": {"fixture": {"command": "fixture"}}}) + "\n",
            encoding="utf-8",
        )
        (root / ".ssh").mkdir()
        (root / ".ssh/config").write_text("", encoding="utf-8")
        (home / ".ssh").mkdir()
        (home / ".claude").mkdir()
        (home / ".claude/settings.json").write_text("{}\n", encoding="utf-8")
        (home / ".cursor").symlink_to(root / ".cursor", target_is_directory=True)

        env = {
            **os.environ,
            "PATH": str(fake_bin),
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "GIT_CONFIG_GLOBAL": str(directory / "gitconfig"),
            "NONINTERACTIVE": "true",
            "DOTFILES_ROOT": str(root),
            "TEST_MISE_SHIMS": str(mise_shims),
            "FIXTURE_REAL_PYTHON": sys.executable,
            "EVENT_LOG": str(event_log),
            "FAIL_MISE_INSTALL": "1" if fail_install else "0",
        }
        for variable in ("GIT_USER_NAME", "GIT_USER_EMAIL", "GIT_USER_SIGNINGKEY"):
            env.pop(variable, None)
        return {
            "root": root,
            "home": home,
            "env": env,
            "event_log": event_log,
        }

    def _run_installer(self, fixture):
        return subprocess.run(
            [BASH, str(fixture["root"] / "install.sh")],
            cwd=str(fixture["root"]),
            env=fixture["env"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

    def _copy(self, destination, source):
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(destination))

    def _write_executable(self, path, content):
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    def _bash_path(self, path):
        if os.name != "nt":
            return str(path)
        cygpath = shutil.which("cygpath")
        if not cygpath:
            self.skipTest("cygpath is required by the Windows Bash fixture")
        result = subprocess.run(
            [cygpath, "-u", str(path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        return result.stdout.strip()


if __name__ == "__main__":
    unittest.main()
