"""プロデュース state リーダーの開発者向けデバッグ CLI。

スクリーンショット (PNG) を受け取り、抽出された `GameState` と
`StrategyEngine.decide` の判定結果を表示する。実機を動かさずに
リージョン座標とロジックを検証するためのツール。

使い方:
    .venv/bin/python -m auto_emulator.games.produce.cli \
        tests/fixtures/produce/schedule_s2_w8_fans6225.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

from auto_emulator.games.produce.decision import StrategyEngine
from auto_emulator.games.produce.reader import ProduceStateReader


def inspect(path: Path, tesseract_cmd: str | None = None) -> int:
    if not path.exists():
        sys.stderr.write(f"file not found: {path}\n")
        return 2
    reader = ProduceStateReader(tesseract_cmd=tesseract_cmd)
    with Image.open(path) as img:
        state = reader.read(img)
        lessons = reader.lessons_from_schedule(img)
    state = state.model_copy(update={"lessons": lessons})

    engine = StrategyEngine()
    decision = engine.decide(state)

    payload = {
        "state": state.model_dump(),
        "decision": decision.model_dump(),
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        sys.stderr.write(
            "usage: python -m auto_emulator.games.produce.cli "
            "<screenshot.png> [--tesseract-cmd PATH]\n",
        )
        return 2
    path = Path(args[0])
    tesseract_cmd: str | None = None
    if "--tesseract-cmd" in args:
        idx = args.index("--tesseract-cmd")
        if idx + 1 < len(args):
            tesseract_cmd = args[idx + 1]
    return inspect(path, tesseract_cmd=tesseract_cmd)


if __name__ == "__main__":
    raise SystemExit(main())
