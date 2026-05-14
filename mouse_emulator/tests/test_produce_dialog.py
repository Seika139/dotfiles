"""`choose_dialog_option` の文脈判定テスト。"""

from __future__ import annotations

import pytest

from auto_emulator.games.produce import (
    DEFAULT_DIALOG_RULES,
    DialogChoiceRule,
    choose_dialog_option,
)


class TestChooseDialogOption:
    def test_relax_context_picks_usual_self(self) -> None:
        # 緊張を解く文脈 -> "いつも通り" を選ぶ
        idx = choose_dialog_option(
            "千雪の緊張を解いてあげなきゃな",
            ("にらめっこでも しよう", "いつも通りの 千雪で行こう", "経験を 思い出そう"),
        )
        assert idx == 1

    def test_practice_context_picks_zenryoku(self) -> None:
        idx = choose_dialog_option(
            "ここは練習で上達を狙おう",
            ("適度に", "本気で頑張る", "様子見"),
        )
        assert idx == 1

    def test_rest_context_picks_yukkuri(self) -> None:
        idx = choose_dialog_option(
            "今日は気分転換が必要そうだ",
            ("もっと頑張る", "ゆっくり休もう", "勉強する"),
        )
        assert idx == 1

    def test_fallback_to_yellow_when_no_match(self) -> None:
        # キーワード何もマッチしない -> 末尾 (黄色)
        idx = choose_dialog_option(
            "今日も頑張ろう",  # マッチするが option に該当キーワードなし
            ("Aを選ぶ", "Bを選ぶ", "Cを選ぶ"),
        )
        # 練習文脈ルール発火するが option に頑張/本気/全力なし -> 次のルール
        # 休む文脈は prompt に無い -> fallback (index 2)
        assert idx == 2

    def test_fallback_index_clamped_to_options_length(self) -> None:
        # 2 つしかない選択肢で fallback=2 -> インデックス 1 に丸まる
        idx = choose_dialog_option(
            "意味不明な promp",
            ("A", "B"),
            fallback_index=2,
        )
        assert idx == 1

    def test_empty_options_returns_zero(self) -> None:
        assert choose_dialog_option("anything", ()) == 0

    def test_custom_rules_override_defaults(self) -> None:
        custom = (
            DialogChoiceRule(
                prompt_keywords=("テスト",),
                option_keywords=("特殊",),
            ),
        )
        idx = choose_dialog_option(
            "これはテストです",
            ("通常", "特殊", "別"),
            rules=custom,
        )
        assert idx == 1

    def test_first_matching_rule_wins(self) -> None:
        # 「緊張」「休」両方含む prompt -> 先頭規則 (緊張) が勝つ
        idx = choose_dialog_option(
            "緊張で休みたい",
            ("いつも通り", "ゆっくり休む", "全力"),
        )
        # rule[0] (緊張) -> "いつも通り" の index 0
        assert idx == 0


class TestDefaultRules:
    def test_default_rules_are_frozen(self) -> None:
        # frozen Pydantic モデルへの代入は失敗するはず
        rule = DEFAULT_DIALOG_RULES[0]
        with pytest.raises(ValueError, match="frozen"):
            rule.prompt_keywords = ()  # type: ignore[misc]
