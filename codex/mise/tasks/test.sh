#!/usr/bin/env bash

#MISE description="codex/tests/ の Python テストを実行する"

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

python3 -m unittest discover -s tests -p "test_*.py" -v
