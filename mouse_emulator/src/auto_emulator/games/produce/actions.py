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
    # Phase 3: 実機 canvas (`schedule_preview_vocal.png` 1x /
    # `real_schedule_canvas.png` 2x) で赤紫「決定」ボタン中心を実測。
    # 旧 (0.847,0.928) は x が ~107px 左にズレ、サポートスキルと決定の
    # 隙間を押していた (レッスン未確定 → stuck:no_progress の原因)。
    confirm_button: Point = Point(x=0.920, y=0.932, description="右下: 決定")
    back_button: Point = Point(x=0.038, y=0.928, description="左下: 戻る")
    reflection_button: Point = Point(x=0.553, y=0.928, description="下中央: 振り返り")


class HomeActionPoints(BaseModel):
    """ホーム画面の 4 つのカードに対応するクリックポイント。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    produce_card: Point = Point(
        x=0.137,
        y=0.770,
        description="左下カード: プロデュース",
    )
    rest_card: Point = Point(x=0.367, y=0.860, description="中央下カード: 休む")
    reflection_card: Point = Point(
        x=0.597,
        y=0.860,
        description="中央右下カード: 振り返り",
    )
    trend_card: Point = Point(x=0.827, y=0.860, description="右下カード: 流行確認")
    rest_confirm: Point = Point(x=0.598, y=0.553, description="休む確認ダイアログの OK")
    item_tab: Point = Point(
        x=0.050,
        y=0.490,
        description="左サイドバー: アイテム (バッグアイコン)",
    )


class ItemActionPoints(BaseModel):
    """アイテム使用画面のクリックポイント。

    アイテム使用は 2 段階: ①一覧で対象枠の `使う` ボタン → ②使用確認
    ダイアログの `使う` で確定。枠の横位置 (x) は `ItemScreenRegions`
    の `card_centers_x` を単一の真実源とし、ここでは `使う` ボタンの
    y (`use_button_y`) と確認/閉じるの固定点だけ持つ。実機 2x キャプチャ
    (`produce_item_screen.png` / `produce_item_confirm.png`) で実測。
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    # 一覧の各枠 `使う` ボタンの y。x は枠中心 (reader 側 card_centers_x)。
    use_button_y: float = Field(
        default=0.69,
        ge=0.0,
        le=1.0,
        description="アイテム一覧の各枠 `使う` ボタンの y 中心 (実測 0.669-0.713)",
    )
    confirm_use: Point = Point(
        x=0.580,
        y=0.805,
        description="使用確認ダイアログの `使う` (確定、実測 y 0.766-0.844)",
    )
    close_button: Point = Point(
        x=0.500,
        y=0.820,
        description="アイテム一覧の `閉じる`",
    )
    back_button: Point = Point(
        x=0.038,
        y=0.928,
        description="アイテム画面から戻る (左下)",
    )

    def use_button(self, card_center_x: float) -> Point:
        """指定枠中心 x の `使う` ボタン位置を返す。

        Args:
            card_center_x: 対象枠の中心 x (reader の card_centers_x[slot])。

        Returns:
            その枠の `使う` ボタンをタップする `Point`。
        """
        return Point(
            x=card_center_x,
            y=self.use_button_y,
            description="アイテム一覧の対象枠 `使う`",
        )


class AuditionBattlePoints(BaseModel):
    """オーディション戦闘画面で使う固定クリックポイント。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    auto_toggle: Point = Point(x=0.782, y=0.062, description="右上: AUTO ON/OFF")
    speed_toggle: Point = Point(x=0.861, y=0.062, description="右上: 倍速 ON/OFF")
    pause_button: Point = Point(x=0.940, y=0.062, description="右上: 一時停止")


class ModalDismissPoints(BaseModel):
    """想定外モーダル (お知らせ / イベント告知 / 通信エラー等) の閉じる候補。

    優先度順に並べる: 早期に試した候補がヒットしやすい位置。
    実機での出現頻度が分かったら `tools/calibrate_produce.py` で
    座標を確認しつつ並び替える。
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    close_top_right: Point = Point(
        x=0.965,
        y=0.050,
        description="右上の close アイコン (お知らせ/イベント告知の典型)",
    )
    ok_center: Point = Point(
        x=0.500,
        y=0.680,
        description="中央下の OK ボタン (確認モーダル)",
    )
    cancel_left_bottom: Point = Point(
        x=0.155,
        y=0.825,
        description="左下の戻る/キャンセル",
    )
    retry_center: Point = Point(
        x=0.500,
        y=0.560,
        description="通信エラー時のリトライ位置",
    )


class DialogPoints(BaseModel):
    """会話パートで使うポイント。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fast_forward_toggle: Point = Point(
        x=0.833,
        y=0.944,
        description="右下: 早送り x4 ON/OFF",
    )
    choice_pink: Point = Point(
        x=0.183,
        y=0.218,
        description="3 択ダイアログの左 (ピンク)",
    )
    choice_green: Point = Point(
        x=0.463,
        y=0.108,
        description="3 択ダイアログの中央 (緑、いいよ等)",
    )
    choice_yellow: Point = Point(
        x=0.747,
        y=0.248,
        description="3 択ダイアログの右 (黄色、M11/M16 のデフォルト)",
    )
    checkmark_choice: Point = Point(
        x=0.500,
        y=0.330,
        description=(
            "3 択が表示されず単一カードにチェックマーク (✓) が付いているときの"
            "フォールバック確定タップ位置 (旧 sample2.yml の option_check 相当)"
        ),
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
MODAL_DISMISS_POINTS = ModalDismissPoints()
ITEM_POINTS = ItemActionPoints()


def modal_dismiss_sequence(points: ModalDismissPoints) -> tuple[Point, ...]:
    """モーダル閉じるボタンの試行順序を返す。

    優先度: 右上 close -> 中央 OK -> リトライ -> 左下キャンセル。

    Returns:
        試行順に並んだ候補ポイントのタプル。
    """
    return (
        points.close_top_right,
        points.ok_center,
        points.retry_center,
        points.cancel_left_bottom,
    )
