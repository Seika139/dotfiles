"""シャニマス プロデュースモード自動化エンジン。

Phase 1: state_reader を提供しゲーム画面から構造化された GameState を抽出する。
Phase 2+ で decision エンジンと action マクロを追加予定。
"""

from auto_emulator.games.produce.decision import (
    DEFAULT_DIALOG_RULES,
    WING_AUDITION_KEYWORDS,
    ActionKind,
    DialogChoiceRule,
    StrategyEngine,
    TurnDecision,
    choose_dialog_option,
    is_wing_audition,
)
from auto_emulator.games.produce.digit_matcher import (
    DigitMatcher,
    DigitTemplate,
    extract_template,
    load_digit_templates,
)
from auto_emulator.games.produce.reader import (
    HeaderRegions,
    LessonRegions,
    ProduceStateReader,
    StatsRegions,
    StatusRegions,
)
from auto_emulator.games.produce.state import (
    AuditionOption,
    FractionalRegion,
    GameState,
    LessonOption,
)
from auto_emulator.games.produce.strategy import SEASON_STRATEGY, SeasonPlan
from auto_emulator.games.produce.turn_log import JsonlTurnLogger, TurnLogEntry

__all__ = [
    "DEFAULT_DIALOG_RULES",
    "SEASON_STRATEGY",
    "WING_AUDITION_KEYWORDS",
    "ActionKind",
    "AuditionOption",
    "DialogChoiceRule",
    "DigitMatcher",
    "DigitTemplate",
    "FractionalRegion",
    "GameState",
    "HeaderRegions",
    "JsonlTurnLogger",
    "LessonOption",
    "LessonRegions",
    "ProduceStateReader",
    "SeasonPlan",
    "StatsRegions",
    "StatusRegions",
    "StrategyEngine",
    "TurnDecision",
    "TurnLogEntry",
    "choose_dialog_option",
    "extract_template",
    "is_wing_audition",
    "load_digit_templates",
]
