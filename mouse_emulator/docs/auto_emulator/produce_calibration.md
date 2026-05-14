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

## 座標の階層

すべての座標は **画像サイズに対する fractional (0.0-1.0)** で持つ。
解像度が変わっても比率指定なので追従するが、UI レイアウト自体が
変われば調整が必要。

| 型 | 担当 |
| --- | --- |
| `HeaderRegions` | シーズン / 残り週 / ファン (画面上部) |
| `StatsRegions` | 6 ステ表示行 |
| `StatusRegions` | HP バー / トラブル率 / テンション |
| `LessonRegions` | スケジュール画面のレッスンカード 6 枚 |
| `HomeActionPoints` | ホーム画面のカード (プロデュース / 休む等) |
| `ScheduleActionPoints` | スケジュール画面のタブ / 決定 / 戻る |
| `AuditionBattlePoints` | 戦闘画面の AUTO / 倍速 / 一時停止 |
| `DialogPoints` | 早送り×4 / 3 択 (桃緑黄) / 中央タップ |
| `ItemActionPoints` | アイテム選択 / 使用 / 閉じる |
| `ModalDismissPoints` | 想定外モーダル除去候補 |

## 主要ツール: `tools/calibrate_produce.py`

スクリーンショットに **全リージョン矩形 + 全アクションマーカー**を
重ね描きした PNG を生成する。

```bash
# 既存フィクスチャに対して
.venv/bin/python tools/calibrate_produce.py \
    tests/fixtures/produce/schedule_s2_w8_fans6225.png \
    --out /tmp/calibrated.png
open /tmp/calibrated.png
```

オプション:

| フラグ | 効果 |
| --- | --- |
| `--out <path>` | 出力 PNG パス (default: `<input>_calibrated.png`) |
| `--no-regions` | リージョン矩形を描かない (マーカーだけ表示) |
| `--no-points` | アクションマーカーを描かない (矩形だけ表示) |

線太さは画像幅から自動算出されるので、大小いずれの解像度でも
視認可能。

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
.venv/bin/python tools/calibrate_produce.py \
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
.venv/bin/python -m pytest tests/test_produce_state_reader.py tests/test_produce_digit_matcher.py -q
```

完全一致が要件 (D4 anchor) なので、座標を変えると壊れる場合は
**新フィクスチャでテストを増やす** か、conditional テストにする。

## 数字テンプレート追加手順 (digit "4" 等を補充)

`tests/fixtures/produce/digits/{digit}_{style}.png` 形式の PNG を
追加すれば `load_digit_templates` が自動で読み込む。

### 手順

1. **対象 digit を含む画面のスクショ**を撮る (例: ファン数が "4" を含む)
2. その画面の "4" を含む数値を `calibrate_produce.py` で位置確認
3. 「4」の周囲を Pillow で切り出す:

   ```python
   from PIL import Image
   img = Image.open("/path/to/screenshot.png")
   # 例: PNG 座標で "4" digit が (1100, 880, 1130, 940) 付近
   img.crop((1100, 880, 1130, 940)).save(
       "tests/fixtures/produce/digits/4_stats.png"
   )
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

| 画面種別 | 検出条件 |
| --- | --- |
| `schedule_lesson` | R > 200, G < 170, B > 150 (マゼンタ = 決定ボタン) |
| `home` | G > R+10, G > B (緑 = 流行確認カード) |
| `audition_battle` | RGB すべて < 140 (ダーク = ステージ背景) |

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
