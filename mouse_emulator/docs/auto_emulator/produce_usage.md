# プロデュース自走 使い方ガイド

シャニマス W.I.N.G. ルートを `auto-emulator produce-run` で自動進行
させるためのセットアップから停止までの一気通貫手順書。実機ゲームを
ブラウザで開いた状態で実行する想定。

> 関連: 観測ルールは [`produce_rules.md`](produce_rules.md)、座標
> 微調整は [`produce_calibration.md`](produce_calibration.md) を参照。

## 前提条件

- macOS (Apple Silicon)
- Python 3.11.6 以上 (`mise` で管理)
- `mise` / `uv` インストール済み
- **アクセシビリティ許可**: 「ターミナル.app」が "入力監視" と
  "アクセシビリティ" の両方を許可されていること (`システム設定 →
  プライバシーとセキュリティ`)
- Tesseract 5.x + 日本語データ (`brew install tesseract tesseract-lang`)
- シャニマス (https://shinycolors.enza.fun/) にログイン済みの
  ブラウザを起動できる状態

## 初回セットアップ

```bash
cd ~/dotfiles/mouse_emulator
mise run resolve                                  # .venv + 依存解決
brew install tesseract tesseract-lang            # OCR 用 (既存なら不要)
.venv/bin/python -m pytest tests/ -q             # 175 passed, 1 skipped を確認
```

すべての pytest が緑なら、コード側は動く状態。

## 実行フロー

### ステップ 1: シャニマスを開く

ブラウザでログイン → プロデュース開始画面まで進めておく。Engine は
**ホーム画面または schedule_lesson 画面**を起点として自走する。

### ステップ 2: produce-run を起動

```bash
mise run produce-auto

# または直接:
.venv/bin/python -m auto_emulator produce-run
```

オプションを追加するなら:

```bash
mise run produce-auto -- \
    --log-file /tmp/produce-$(date +%Y%m%d-%H%M).jsonl \
    --max-turns 200 \
    --pause-key ctrl+p
```

| オプション | 用途 |
| --- | --- |
| `--templates-dir <path>` | DigitMatcher の digit PNG ディレクトリ (default: `tests/fixtures/produce/digits`) |
| `--log-file <path>` | ターン毎の状態を JSONL で永続化 (省略時は D5 で自動命名 `~/.cache/auto-emulator/produce/produce-YYYYMMDD-HHMM.jsonl`) |
| `--no-log` | JSONL ログを完全に無効化 (D5 自動命名も抑止) |
| `--max-turns <N>` | 自走上限 (default 200) |
| `--pause-key <combo>` | 一時停止/再開ホットキー (例: `ctrl+p`) |
| `--no-calibrate` | キャリブレーションをスキップ (現状は preset 未対応なので必ず手動キャリブが走る) |

### ステップ 3: キャリブレーション

起動直後にターミナルに `キャリブレーションを開始します` と表示される。
画面上でマウスを動かし、**シャニマスのブラウザ画面の左上 → 右下**を
順にクリック (詳細は [`produce_calibration.md`](produce_calibration.md))。

成功すると `DigitMatcher: 14 テンプレートをロード` などのログが出て、
自走ループが始まる。

### ステップ 4: 自走中の挙動

毎ターン、ターミナルに以下のような行が出る:

```
[produce] turn season=2 week=8 fans_left=6225 -> lesson slot=0 (preferred lesson 'ボーカルレッスン' at slot 0)
```

`--log-file` を指定していれば、同じ情報が JSONL ファイルに 1 行
追記される。

### ステップ 5: 停止

| 操作 | 動作 |
| --- | --- |
| `Ctrl+C` | 即時中断 (現ターンの操作が途中で打ち切られる可能性あり) |
| `--pause-key ctrl+p` | 設定したキーで一時停止 / 再開 (Engine が見ている画面遷移は止まる) |
| ファン目標到達 | `stop_reason="complete"` でループ自然終了 |
| ターン上限 | `stop_reason="max_turns"` |
| 自動検出: 詰まり | `stop_reason="stuck:home" / "stuck:schedule" / "stuck:ocr" / "stuck:no_progress"` |

終了時には `停止理由: complete` の後に、D6 の **run サマリ**が
表示される (Ctrl+C 中断時も同じサマリが出る):

```text
=== Produce Run Summary ===
total turns: 42
stop reason: complete
season: 1 -> 4
fans_to_target: 500000 -> 0 (delta=+500000)
decisions:
  lesson: 28
  audition: 8
  rest: 4
  reflection: 2
```

## 自走中に出る Engine ログの読み方

```text
[produce] turn season=2 week=8 fans_left=6225 -> lesson slot=0 (...)
                  ^^ ^^      ^^                  ^^^^^^^ ^^^^^^^^
                  状態抽出値                     決定                理由
```

- `season` / `week` / `fans_left` が **未取得** (None) のターンが連続
  すると `stuck:ocr` で停止 → キャリブを見直す
- `lesson slot=0` が連続して状態が変わらないと `stuck:no_progress` で
  停止 → クリックが空振りしている可能性、`calibrate_produce.py` で
  座標確認
- 中間画面の連続消化中は `[produce] unknown screen streak=5; attempting
  modal dismiss` が出ることがある (B3)

## JSONL ログの活用

### D7: `produce-analyze` で過去ログを後追い集計

`produce-run` 中に書かれた JSONL は、後から
`produce-analyze` サブコマンドで同じサマリを出力できる:

```bash
.venv/bin/python -m auto_emulator produce-analyze \
    ~/.cache/auto-emulator/produce/produce-20260515-0930.jsonl
```

出力例:

```text
source: /Users/.../produce-20260515-0930.jsonl
=== Produce Run Summary ===
total turns: 42
stop reason: complete
season: 1 -> 4
fans_to_target: 500000 -> 0 (delta=+500000)
decisions:
  lesson: 28
  audition: 8
  rest: 4
  reflection: 2
```

### jq での生ログ操作

サマリでカバーされない粒度を見たい場合は jq で直接操作する:

```bash
# 最終行の停止理由を確認
tail -1 ~/.cache/auto-emulator/produce/produce-XXX.jsonl \
    | jq .stop_reason

# 各ターンのファン推移
jq '{turn: .turn_number, fans: .fans_to_target}' \
    ~/.cache/auto-emulator/produce/produce-XXX.jsonl
```

ログは追記モードで書かれるので、複数回の実行を 1 ファイルにまとめる
こともできる (ただし整合性のために実行毎にファイル名を分けるのを
推奨。D5 の自動命名は分単位なので普通は被らない)。

## トラブルシューティング

### `stuck:ocr` で即停止する

- Tesseract が `eng` / `jpn` 両方インストールされているか確認
  `tesseract --list-langs`
- DigitMatcher テンプレディレクトリが空でないか確認
  `ls tests/fixtures/produce/digits/`
- ヘッダー領域の座標が現解像度に合っているか
  → [`produce_calibration.md`](produce_calibration.md) でリージョン
  オーバーレイを生成

### `stuck:home` で停止する

- 中間画面のタップ位置 (`DialogPoints.advance_safe`) が現解像度で
  正しい座標にあるか
- 想定外モーダル (お知らせ等) が出ていないか → `try_dismiss_modal`
  が候補を試すが、新しい UI には候補追加が必要

### キャリブレーション後にクリック位置がずれる

- ブラウザのズーム率が 100% であることを確認
- DPI 設定変更後は再キャリブレーション必須
- `--no-calibrate` は preset 機構が未対応なので使えない (常に
  手動キャリブが走る)

### `stuck:no_progress` が頻発する

- ホーム → スケジュール画面遷移が成立していない可能性
- `produce_card` 座標 (default: 0.137, 0.770) の精度を疑う
- log を見て `decision_action_kind=lesson` が連続なら lesson
  選択ステップで詰まっている

### 戦闘 AUTO が始まらない

- `audition_battle` 画面検出に失敗 → 右下色 signature を確認
- AUTO トグル座標 (`AuditionBattlePoints.auto_toggle` =
  (0.782, 0.062)) が現解像度で正しいか目視確認

## ファン目標達成 (True End) 判定

`fans_to_target` が `0` になった瞬間に `complete` で停止する。
最終的なステータスは JSONL の最終行に保存される。

```bash
jq 'select(.stop_reason=="complete")' /tmp/produce-XXX.jsonl
```

W.I.N.G. ファイナル後の報酬画面消化は現状 `consume_until_home`
任せで、ホーム再到達まで自動で進む。

## 既存 `sample2.yml` との関係

旧経路 (`mise run auto-run --config profiles/auto_emulator/sample2.yml`)
は yml ベースのメカニカルクリックループで、状態判断は持たない。

新経路 `produce-auto` は OCR + DigitMatcher で状態を読み、シーズン
別戦略に基づいて自走する。**yml はサンプル用に残してあるが、本実行は
`produce-auto` を使うのが推奨**。
