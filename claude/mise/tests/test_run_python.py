import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_python.sh"
BASH = shutil.which("bash") or "bash"


def write_executable(path: Path, source: str) -> None:
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)


def fake_python_source(name: str, version_ok: int) -> str:
    return f'''#!/bin/sh
if [ "$1" = "-3" ]; then shift; fi
if [ "$1" = "-I" ] && [ "$2" = "-c" ]; then
  case "$3" in
    *sys.platform*) printf '%s\\n' "${{MOCK_PLATFORM:-linux}}"; exit 0 ;;
    *) exit {version_ok} ;;
  esac
fi
printf 'selected={name}\\n'
printf 'arg:%s\\n' "$@"
'''


class RunPythonTest(unittest.TestCase):
    def run_wrapper(self, bin_dir: Path, script_path: str, *arguments: str, env=None):
        process_env = os.environ.copy()
        process_env["PATH"] = os.pathsep.join((str(bin_dir), "/usr/bin", "/bin"))
        if env:
            process_env.update(env)
        return subprocess.run(
            [BASH, str(RUNNER), script_path, *arguments],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=process_env,
            check=False,
        )

    def test_falls_back_from_python3_to_python(self):
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory)
            write_executable(bin_dir / "python3", fake_python_source("python3", 1))
            write_executable(bin_dir / "python", fake_python_source("python", 0))
            result = self.run_wrapper(
                bin_dir,
                "/tmp/normalizer.py",
                "--claude-dir",
                "/tmp/claude",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("selected=python", result.stdout)
            self.assertIn("arg:/tmp/normalizer.py", result.stdout)

    def test_uses_windows_launcher_and_converts_script_and_profile_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory)
            write_executable(bin_dir / "python3", fake_python_source("python3", 1))
            write_executable(bin_dir / "python", fake_python_source("python", 1))
            write_executable(bin_dir / "py", fake_python_source("py", 0))
            write_executable(
                bin_dir / "uname",
                "#!/bin/sh\nprintf 'MINGW64_NT\\n'\n",
            )
            write_executable(
                bin_dir / "cygpath",
                "#!/bin/sh\nprintf 'WINDOWS:%s\\n' \"$(basename \"$2\")\"\n",
            )
            result = self.run_wrapper(
                bin_dir,
                "relative/normalizer.py",
                "--cursor-dir",
                "relative/cursor",
                "--claude-dir",
                "/c/Users/example/.claude",
                "--verbose",
                "--mcp-source=/repo/mcp.json",
                env={"MOCK_PLATFORM": "win32", "MSYS2_ARG_CONV_EXCL": "*"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("selected=py", result.stdout)
            self.assertIn("arg:WINDOWS:normalizer.py", result.stdout)
            self.assertIn("arg:--cursor-dir", result.stdout)
            self.assertIn("arg:WINDOWS:cursor", result.stdout)
            self.assertIn("arg:--claude-dir", result.stdout)
            self.assertIn("arg:WINDOWS:.claude", result.stdout)
            self.assertIn("arg:--mcp-source=WINDOWS:mcp.json", result.stdout)
            self.assertIn("arg:--verbose", result.stdout)

    def test_reports_python_minimum_when_no_supported_interpreter_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory)
            write_executable(bin_dir / "python3", fake_python_source("python3", 1))
            write_executable(bin_dir / "python", fake_python_source("python", 1))
            result = self.run_wrapper(
                bin_dir,
                "/tmp/normalizer.py",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Python 3.6 or newer is required", result.stderr)


if __name__ == "__main__":
    unittest.main()
