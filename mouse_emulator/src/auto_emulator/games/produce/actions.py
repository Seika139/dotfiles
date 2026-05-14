"""プロデュース UI の固定クリックポイント (fractional 座標) 定数。

`TurnDecision.action_kind` ごとに、画面のどこをタップすればよいかをここに集約する。
`StatsRegions` などと同様に画像サイズに対する 0.0-1.0 比率で持つので、
解像度が変わっても calibration なしで追従できる。

Phase 5 でこれらを参照する `ProduceActions` 実行クラスを実装する予定。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from auto_emulator.games.produce.state import FractionalRegion


class Point(BaseModel):
    """クリック対象の fractional 座標 (中心点)。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    description: str = Field(description="この点が指す UI 要素の説明")


class ScheduleActionPoints(BaseModel):
    """スケジュール選択画面で使う固定クリックポイント。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lesson_tab: Point = Point(x=0.060, y=0.180, description="左タブ: レッスン&お仕事")
    audition_tab: Point = Point(x=0.060, y=0.350, description="左タブ: オーディション")
    confirm_button: Point = Point(x=0.847, y=0.928, description="右下: 決定")
    back_button: Point = Point(x=0.038, y=0.928, description="左下: 戻る")
    reflection_button: Point = Point(x=0.553, y=0.928, description="下中央: 振り返り")


class HomeActionPoints(BaseModel):
    """ホーム画面の 4 つのカードに対応するクリックポイント。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    produce_card: Point = Point(x=0.137, y=0.770, description="左下カード: プロデュース")
    rest_card: Point = Point(x=0.367, y=0.860, description="中央下カード: 休む")
    reflection_card: Point = Point(
        x=0.597,
        y=0.860,
        description="中央右下カード: 振り返り",
    )
    trend_card: Point = Point(x=0.827, y=0.860, description="右下カード: 流行確認")
    rest_confirm: Point = Point(x=0.598, y=0.553, description="休む確認ダイアログの OK")


class AuditionBattlePoints(BaseModel):
    """オーディション戦闘画面で使う固定クリックポイント。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    auto_toggle: Point = Point(x=0.782, y=0.062, description="右上: AUTO ON/OFF")
    speed_toggle: Point = Point(x=0.861, y=0.062, description="右上: 倍速 ON/OFF")
    pause_button: Point = Point(x=0.940, y=0.062, description="右上: 一時停止")


class DialogPoints(BaseModel):
    """会話パートで使うポイント。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fast_forward_toggle: Point = Point(
        x=0.833,
        y=0.944,
        description="右下: 早送り x4 ON/OFF",
    )
    choice_yellow: Point = Point(
        x=0.747,
        y=0.248,
        description="3 択ダイアログの黄色 (M11/M16 によりデフォルト)",
    )
    advance_safe: Point = Point(
        x=0.463,
        y=0.497,
        description="ダイアログ進行: 中央付近の安全な空きスペース",
    )


def audition_swipe_path() -> tuple[FractionalRegion, FractionalRegion]:
    """オーディションカードを次へスワイプするドラッグの (開始, 終端)。

    オーディションタブで複数枚のカードから目的のものを選ぶときに使う。
    M12 の知見: 右矢印クリックは不安定、スワイプの方が確実。

    Returns:
        (開始点を含む狭い領域, 終端点を含む狭い領域) のペア。
    """
    start = FractionalRegion(x=0.625, y=0.460, w=0.020, h=0.020)
    end = FractionalRegion(x=0.255, y=0.460, w=0.020, h=0.020)
    return start, end


# 階層的にまとめた既定アクションポイント。Engine 実装はこれを参照する。
HOME_POINTS = HomeActionPoints()
SCHEDULE_POINTS = ScheduleActionPoints()
AUDITION_BATTLE_POINTS = AuditionBattlePoints()
DIALOG_POINTS = DialogPoints()
