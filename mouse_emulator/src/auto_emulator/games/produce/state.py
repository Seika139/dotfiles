"""プロデュース画面から抽出した状態を表す型。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ScreenKind = Literal[
    "home",
    "schedule_lesson",
    "schedule_audition",
    "reflection",
    "audition_battle",
    "wing_semifinal",
    "wing_final",
    "dialog",
    "unknown",
]


class FractionalRegion(BaseModel):
    """画像内の領域を 0.0-1.0 の比率で指定する。

    実画素サイズに対して `to_pixels` で絶対座標へ変換する。
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    w: float = Field(gt=0.0, le=1.0)
    h: float = Field(gt=0.0, le=1.0)

    @model_validator(mode="after")
    def _validate_bounds(self) -> FractionalRegion:
        if self.x + self.w > 1.0:
            msg = f"x+w が 1.0 を超えます: {self.x + self.w}"
            raise ValueError(msg)
        if self.y + self.h > 1.0:
            msg = f"y+h が 1.0 を超えます: {self.y + self.h}"
            raise ValueError(msg)
        return self

    def to_pixels(self, width: int, height: int) -> tuple[int, int, int, int]:
        left = int(width * self.x)
        upper = int(height * self.y)
        right = int(width * (self.x + self.w))
        lower = int(height * (self.y + self.h))
        return left, upper, right, lower


class LessonOption(BaseModel):
    """スケジュール画面下部の単一レッスン/お仕事カード情報。"""

    model_config = ConfigDict(extra="forbid")

    slot: int = Field(ge=0, le=5, description="左から 0-5 のカード位置")
    name: str = Field(description="OCR で取得したカード名 (例: ボーカルレッスン)")
    level: int = Field(ge=1, le=5, description="カードレベル Lv.")
    preview_fans: int | None = Field(
        default=None,
        ge=0,
        description="プレビュー +N (ファン獲得見込み)。--- なら None",
    )


class AuditionOption(BaseModel):
    """オーディションタブ内のスワイプ可能なカード 1 枚分の情報。"""

    model_config = ConfigDict(extra="forbid")

    slot: int = Field(
        ge=0,
        description="スワイプ順 (0 が最初に表示されるカード)",
    )
    name: str = Field(description="オーディション名 (例: 夕方ワイド アイドル一番)")
    difficulty: int = Field(ge=1, le=20, description="難易度")
    recommended_stats: dict[str, int] = Field(
        default_factory=dict,
        description="推奨能力値 (キー: Vo/Da/Vi 等)",
    )
    expected_fans: int | None = Field(
        default=None,
        ge=0,
        description="ファン獲得見込み (--- なら None)",
    )


class GameState(BaseModel):
    """1 ターンの観測状態。後段の決定エンジンが入力に取る。"""

    model_config = ConfigDict(extra="forbid")

    screen: ScreenKind = Field(default="unknown")
    season: int | None = Field(default=None, ge=1, le=4)
    week_remaining: int | None = Field(default=None, ge=0)
    fans_to_target: int | None = Field(default=None, ge=0)
    hp_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    trouble_pct: int | None = Field(default=None, ge=0, le=100)
    tension_lv: int | None = Field(default=None, ge=1)
    stats: dict[str, int] | None = Field(
        default=None,
        description="キー: Vo/Da/Vi/Me/SP/Fans",
    )
    audition_available: bool = Field(
        default=False,
        description="ホーム画面で「期間限定特別オーディション出演中」ラベルが見える",
    )
    available_auditions: list[AuditionOption] = Field(
        default_factory=list,
        description="オーディションタブで観測されたカード一覧 (左→右)",
    )
    lessons: list[LessonOption] = Field(default_factory=list)
    raw: dict[str, str] = Field(
        default_factory=dict,
        description="OCR 生テキスト (デバッグ用)。リーダーが任意で詰める",
    )
