# プロデュース自走 キャリブレーション HOWTO

`ProduceStateReader` と `ProduceEngine` が依存しているリージョン座標
(`HeaderRegions` / `StatsRegions` / ...) の調整・確認手順。新しい
解像度・別環境で動かすときの作業手順書。

> 観測知見は [`produce_rules.md`](produce_rules.md)、起動手順は
> [`produce_usage.md`](produce_usage.md) を参照。

## いつキャリブが必要か

- 新しい解像度のディスプレイで動かすとき
- ブラウザのズーム率を変えたとき
- シャニマス側の UI レイアウトが更新されたとき
- `stuck:ocr` / `stuck:no_progress` が頻発するとき
- 新しい数字スタイル (例えば S5 以降の新フォント) が出てきたとき

## キャリブの基準は canvas 領域 (重要)

シャニマスは `<canvas width=1135 height=640>` (アスペクト ≈ 1.773) で
描画され、ブラウザやディスプレイによって canvas の **外側に余白**が
付く。そのため全 fractional 座標は **canvas 領域そのもの**を基準に
する。ディスプレイ全体や 16:9 を基準にすると破綻する。

- `produce-run` のキャリブ手順 (左上→右下クリック) は **canvas の角
  ぴったり**を指すこと。余白を含めると全座標がズレる。
- スクショを撮るときも canvas 描画部分だけを切り出す
  (`screencapture -i` で canvas の角を囲う)。
- リファレンス: `tests/fixtures/produce/real_schedule_canvas.png`
  (実機 canvas 領域キャプチャ)。デフォルト座標はこれを基準に Phase 3 で
  調整済み。旧 fixture (`schedule_s2_w8_fans6225.png`, 3024x1610) は
  canvas 外の余白を含むため座標基準には使わない。

## 座標の階層

すべての座標は **canvas 領域に対する fractional (0.0-1.0)** で持つ。
解像度が変わっても比率指定なので追従するが、UI レイアウト自体が
変われば調整が必要。

| 型                     | 担当                                       |
| ---------------------- | ------------------------------------------ |
| `HeaderRegions`        | シーズン / 残り週 / ファン (画面上部)      |
| `StatsRegions`         | 6 ステ表示行                               |
| `StatusRegions`        | HP バー / トラブル率 / テンション          |
| `LessonRegions`        | スケジュール画面のレッスンカード 6 枚      |
| `HomeActionPoints`     | ホーム画面のカード (プロデュース / 休む等) |
| `ScheduleActionPoints` | スケジュール画面のタブ / 決定 / 戻る       |
| `AuditionBattlePoints` | 戦闘画面の AUTO / 倍速 / 一時停止          |
| `DialogPoints`         | 早送り×4 / 3 択 (桃緑黄) / 中央タップ      |
| `ItemActionPoints`     | アイテム選択 / 使用 / 閉じる               |
| `ModalDismissPoints`   | 想定外モーダル除去候補                     |

## 主要ツール: `tools/calibrate_produce.py`

3 つのサブコマンドを持つ統合キャリブ CLI:

| サブコマンド   | 用途                                                              |
| -------------- | ----------------------------------------------------------------- |
| `overlay`      | スクショに全リージョン矩形 + アクションマーカーを描画 (目視確認)  |
| `extract`      | スクショの指定領域を crop して PNG 保存 (digit テンプレ補充用)    |
| `dump-regions` | 現コード定義の全 fractional 座標を JSON 出力 (プロファイル化前段) |

### `overlay`: 矩形 + マーカー重ね描き

```bash
.venv/bin/python tools/calibrate_produce.py overlay \
    tests/fixtures/produce/schedule_s2_w8_fans6225.png \
    --out /tmp/calibrated.png
open /tmp/calibrated.png
```

オプション:

| フラグ         | 効果                                              |
| -------------- | ------------------------------------------------- |
| `--out <path>` | 出力 PNG パス (default: `<input>_calibrated.png`) |
| `--no-regions` | リージョン矩形を描かない (マーカーだけ表示)       |
| `--no-points`  | アクションマーカーを描かない (矩形だけ表示)       |

線太さは画像幅から自動算出されるので、大小いずれの解像度でも視認可能。

### `extract`: スクショから領域を crop

数字テンプレ (`tests/fixtures/produce/digits/{digit}_{style}.png`) を
補充するときの定番フロー。fractional でも pixel でも指定できる。

```bash
# fractional 指定 (overlay と同じ座標体系)
.venv/bin/python tools/calibrate_produce.py extract \
    /path/to/screenshot.png \
    --out tests/fixtures/produce/digits/4_pink.png \
    --frac 0.605,0.040,0.020,0.052

# pixel 指定 (実機 PNG 上の絶対座標)
.venv/bin/python tools/calibrate_produce.py extract \
    /path/to/screenshot.png \
    --out tests/fixtures/produce/digits/4_pink.png \
    --px 1900,80,60,80
```

`--frac` と `--px` は排他。指定が `x,y,w,h` 4 値でない or 数値解釈不能なら
exit code 3 で停止する。

### `dump-regions`: 現座標を JSON 出力

`HeaderRegions` / `StatsRegions` / `StatusRegions` / `LessonRegions` と、
すべてのアクション座標 (`HomeActionPoints` 等) を 1 つの JSON にまとめる。
将来のプロファイル化 (`--no-calibrate` 対応や複数解像度プリセット) の
前段、または座標変更の差分レビュー用。

```bash
# ファイル出力
.venv/bin/python tools/calibrate_produce.py dump-regions --out /tmp/regions.json

# 標準出力 (--out 省略)
.venv/bin/python tools/calibrate_produce.py dump-regions | jq .points.dialog
```

出力構造:

```json
{
  "regions": {
    "header": {"season_digit": {"x": ..., "y": ..., "w": ..., "h": ...}, ...},
    "stats": {"stat_centers_x": [...], "by_label": {"Vo": {...}, "Da": {...}}},
    "status": {...},
    "lessons": {...}
  },
  "points": {
    "home": {"produce_card": {"x": ..., "y": ..., "description": "..."}, ...},
    "schedule": {...},
    "audition_battle": {...},
    "dialog": {...},
    "modal_dismiss": {...},
    "item": {...}
  }
}
```

## 新解像度での調整フロー

### ステップ 1: 新解像度のスクショを撮る

シャニマスのプロデュース画面 (スケジュール選択) を新しい解像度・
ズーム率で開き、PNG を保存。`mss` でも macOS のスクリーンキャプ
チャでも可。

```bash
# 例: macOS のスクリーンショット
# Cmd+Shift+5 でブラウザ画面のみキャプチャ
```

### ステップ 2: 現リージョンを重ねて確認

```bash
.venv/bin/python tools/calibrate_produce.py overlay \
    /path/to/new_screen.png \
    --out /tmp/new_cal.png
```

矩形が想定した UI 要素 (数字・ボタン) に重なっていればキャリブ
不要。ズレている要素を特定する。

### ステップ 3: 該当リージョンの fractional 値を更新

たとえば `HeaderRegions.fans_to_target` が「6,225 人」の "6"
よりやや左にズレている場合、`src/auto_emulator/games/produce/reader.py`
の該当 `field(default_factory=...)` の `x` を 0.01 単位で右にずらす。

```python
fans_to_target: FractionalRegion = field(
    default_factory=lambda: FractionalRegion(
        x=0.605, y=0.040, w=0.100, h=0.052,
        #   ^^^ ここを調整 (例 0.615 にする)
    ),
)
```

### ステップ 4: ツールで再確認

調整後にもう一度 `calibrate_produce.py` を走らせて重ね描きを見る。
合うまでステップ 3-4 を反復。

### ステップ 5: テストで回帰確認

`schedule_s2_w8_fans6225.png` で動くゴールデンテストが壊れないか
確認:

```bash
.venv/bin/python -m pytest \
    tests/test_produce_state_reader.py \
    tests/test_produce_digit_matcher.py -q
```

完全一致が要件 (D4 anchor) なので、座標を変えると壊れる場合は
**新フィクスチャでテストを増やす** か、conditional テストにする。

## 数字テンプレート追加手順 (digit "4" 等を補充)

`tests/fixtures/produce/digits/{digit}_{style}.png` 形式の PNG を
追加すれば `load_digit_templates` が自動で読み込む。

### 手順

1. **対象 digit を含む画面のスクショ**を撮る (例: ファン数が "4" を含む)
2. `overlay` で位置確認 → 該当 digit の pixel/fractional 座標を見繕う
3. `extract` サブコマンドで切り出す (Pillow 手書き不要):

   ```bash
   # 例: PNG 座標で "4" digit が (1100, 880) から 30x60 px の領域
   .venv/bin/python tools/calibrate_produce.py extract \
       /path/to/screenshot.png \
       --out tests/fixtures/produce/digits/4_stats.png \
       --px 1100,880,30,60
   ```

4. テストを走らせて新テンプレートが認識されることを確認:

   ```bash
   .venv/bin/python -m pytest tests/test_produce_digit_matcher.py -q
   ```

5. 既存ゴールデンを壊さないことを確認 (新テンプレが既存マッチを
   壊さないか)

## 画面検出 (`detect_screen_kind`) のキャリブ

`ProduceStateReader.detect_screen_kind` は**右下コーナーの RGB**を
signature にしている:

| 画面種別          | 検出条件                                          |
| ----------------- | ------------------------------------------------- |
| `schedule_lesson` | R > 200, G < 170, B > 150 (マゼンタ = 決定ボタン) |
| `home`            | G > R+10, G > B (緑 = 流行確認カード)             |
| `audition_battle` | RGB すべて < 140 (ダーク = ステージ背景)          |

新画面 (例: `schedule_audition`, `dialog`, `result`) を識別したい
場合の追加手順:

1. 該当画面のスクショで右下 fractional (0.81-0.88, 0.91-0.96) の
   平均 RGB を測る:

   ```python
   import numpy as np
   from PIL import Image
   img = Image.open("dialog_screen.png")
   arr = np.asarray(img.convert("RGB"))
   h, w = arr.shape[:2]
   br = arr[int(h*0.91):int(h*0.96), int(w*0.81):int(w*0.88)]
   r = float(br[:, :, 0].mean())
   g = float(br[:, :, 1].mean())
   b = float(br[:, :, 2].mean())
   print(f"R={r:.0f} G={g:.0f} B={b:.0f}")
   ```

2. 既存 3 画面と区別できる条件を見つけて
   `reader.detect_screen_kind` に分岐を追加

3. `state.py` の `ScreenKind` リテラルにも追加 (既に
   `wing_semifinal` 等の枠は用意済み)

4. テスト追加: `test_<screen>_fixture` で固定一致を主張

## 色 signature が衝突するとき

新画面の右下色が既存と被って区別できない場合は、別の領域 (中央
ロゴ、ヘッダー文字色など) を補助 signature として追加する。
`detect_screen_kind` を分岐分けして「右下が schedule 色」かつ
「中央に WING ロゴ色」なら `wing_semifinal` といった連結条件で
識別する。

## OCR ベースのフォールバック

DigitMatcher で読めない数字 (`4` がテンプレに無い等) は `_ocr_int`
が Tesseract にフォールバックする。Tesseract は装飾フォントで誤認
しやすいので、新フォントスタイルが出てきたら早めにテンプレを補充
するのが推奨。

## キャリブが終わったあとの確認チェックリスト

- [ ] `pytest tests/` がすべて緑
- [ ] `calibrate_produce.py` でリージョンが UI 要素に重なっている
- [ ] DigitMatcher テンプレが要求 digit をすべてカバー
- [ ] `detect_screen_kind` が想定画面を正しく識別
- [ ] `produce-auto` が少なくとも 1 ターン分の状態を正しく抽出
      (試運転で `[produce] turn season=X week=Y fans_left=Z` を確認)

ここまで通れば実機 dry-run の準備が整っている。
