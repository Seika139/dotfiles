"""シャニマス プロデュースモード自動化エンジン。

Phase 1: state_reader を提供しゲーム画面から構造化された GameState を抽出する。
Phase 2+ で decision エンジンと action マクロを追加予定。
"""

from auto_emulator.games.produce.reader import (
    HeaderRegions,
    LessonRegions,
    ProduceStateReader,
    StatsRegions,
    StatusRegions,
)
from auto_emulator.games.produce.state import (
    FractionalRegion,
    GameState,
    LessonOption,
)
from auto_emulator.games.produce.strategy import SEASON_STRATEGY, SeasonPlan

__all__ = [
    "SEASON_STRATEGY",
    "FractionalRegion",
    "GameState",
    "HeaderRegions",
    "LessonOption",
    "LessonRegions",
    "ProduceStateReader",
    "SeasonPlan",
    "StatsRegions",
    "StatusRegions",
]
