# Dodge Engine (障害物回避)

画面上部から降ってくる障害物を色検出で認識し、安全なレーンを自動タップするリアルタイムエンジンです。

## 概要

- **3レーン構成**のゲームに対応（レーン数は設定で変更可能）
- **色ベース検出** — テンプレートマッチングより高速（numpy 演算）
- 既存のキャリブレーション・一時停止機構をそのまま利用
- 高速キャプチャ（mss）と組み合わせて **約 30 FPS** のスキャンレートを実現

## 実行方法

```bash
# mise タスク経由
mise run auto-dodge --config profiles/auto_emulator/dodge_sample.yml

# 直接実行
.venv/bin/python -m auto_emulator dodge profiles/auto_emulator/dodge_sample.yml
```

### CLI オプション

| オプション | 説明 |
| --- | --- |
| `--calibrate / --no-calibrate` | キャリブレーションの実施を強制 |
| `--pause-key <combo>` | 一時停止/再開キー（例: `ctrl+p`） |

## アルゴリズム

```
ループ (scan_interval 間隔):
  1. mss で画面キャプチャ
  2. (score_region 設定時) 定期的にスコアを OCR で読取り → フェーズ切替
  3. detection_zone 内の各レーンを numpy でスキャン
  4. 障害物色 (RGB ±tolerance) に一致するピクセル数をカウント
  5. min_obstacle_pixels 以上 → そのレーンに障害物あり
  6. 安全なレーンのうち現在位置に最も近いものを選択
  7. レーン変更が必要な場合のみタップ（同じレーンならスキップ）
```

## 設定ファイル

YAML または JSON で記述します。サンプル: [`profiles/auto_emulator/dodge_sample.yml`](../../profiles/auto_emulator/dodge_sample.yml)

### 全体構成

```yaml
version: "1.0"
name: "my-dodge-game"     # 任意

obstacle:                  # 障害物の色定義
  r: 255
  g: 0
  b: 0
  tolerance: 30            # 各 RGB チャンネルの許容誤差

detection_zone:            # 障害物をスキャンする縦方向の範囲
  top: 0.4                 # 相対座標 (0.0-1.0)
  bottom: 0.6

lanes:                     # レーン定義 (2つ以上)
  - name: left
    x_min: 0.0             # スキャン範囲の左端 (相対)
    x_max: 0.33            # スキャン範囲の右端 (相対)
    tap:                   # 移動先としてタップする座標 (相対)
      x: 0.17
      y: 0.9
  - name: center
    x_min: 0.33
    x_max: 0.66
    tap: { x: 0.5, y: 0.9 }
  - name: right
    x_min: 0.66
    x_max: 1.0
    tap: { x: 0.83, y: 0.9 }

runtime:
  scan_interval: 0.03      # スキャン間隔 (秒)
  min_obstacle_pixels: 50   # 障害物判定の最小ピクセル数
  start_lane: 1             # 初期レーン (0-indexed)
  calibration:
    enabled: true
  controls:
    pause_toggle: "ctrl+p"

# --- スコアに応じた動的パラメータ切替 (任意) ---
score_region:               # スコア表示領域 (相対座標)
  x: 0.35
  y: 0.02
  width: 0.30
  height: 0.06
  interval: 1.5             # スコア読取り間隔 (秒)
  threshold: 180             # 二値化閾値

phases:                      # スコア閾値ごとのパラメータ変更
  - min_score: 500
    detection_zone:
      top: 0.30
      bottom: 0.62
    scan_interval: 0.008
    min_obstacle_pixels: 20
  - min_score: 300
    scan_interval: 0.010
  - min_score: 100
    scan_interval: 0.012
```

### 設定項目の詳細

#### `obstacle` — 障害物の色

| キー | 型 | デフォルト | 説明 |
| --- | --- | --- | --- |
| `r` | int (0-255) | — | 赤チャンネル |
| `g` | int (0-255) | — | 緑チャンネル |
| `b` | int (0-255) | — | 青チャンネル |
| `tolerance` | int (0-255) | 30 | 各チャンネルの許容誤差 |

色の特定方法: ゲーム画面のスクリーンショットをスポイトツールで調べるのが確実です。

#### `detection_zone` — スキャン範囲

キャリブレーション領域内の **縦方向** の範囲を相対座標で指定します。

- 障害物が十分に大きく見える位置（画面中央付近）を指定すると検出精度が上がります
- 範囲を狭くするとスキャンが高速になります

#### `lanes` — レーン定義

| キー | 型 | 説明 |
| --- | --- | --- |
| `name` | str | レーン名（ログ表示用） |
| `x_min` | float (0-1) | スキャン範囲の左端 |
| `x_max` | float (0-1) | スキャン範囲の右端 |
| `tap.x` | float (0-1) | タップ先の X 座標 |
| `tap.y` | float (0-1) | タップ先の Y 座標 |

#### `runtime` — ランタイム設定

| キー | 型 | デフォルト | 説明 |
| --- | --- | --- | --- |
| `scan_interval` | float | 0.03 | スキャン間隔（秒）。0.03 ≒ 33 FPS |
| `min_obstacle_pixels` | int | 50 | 障害物判定の最小ピクセル数 |
| `start_lane` | int | 1 | 初期レーン（0-indexed） |
| `calibration` | object | — | キャリブレーション設定（[cli.md](cli.md) 参照） |
| `controls` | object | — | 一時停止キー設定 |

#### `score_region` — スコア読取り領域（任意）

スコアを OCR で読取り、`phases` によるパラメータの動的切替に使用します。

| キー | 型 | デフォルト | 説明 |
| --- | --- | --- | --- |
| `x` | float (0-1) | — | スコア領域の左端（相対） |
| `y` | float (0-1) | — | スコア領域の上端（相対） |
| `width` | float (0-1) | — | スコア領域の幅（相対） |
| `height` | float (0-1) | — | スコア領域の高さ（相対） |
| `interval` | float | 1.0 | スコア読取り間隔（秒）。毎フレーム読む必要はない |
| `threshold` | int \| null | 180 | 二値化閾値。null で無効 |
| `tesseract_config` | str | `--psm 7 ...` | tesseract に渡すオプション |

#### `phases` — スコア連動フェーズ（任意）

`score_region` で読み取ったスコアに応じて `detection_zone`、`scan_interval`、`min_obstacle_pixels` を動的に変更します。`min_score` が大きいフェーズから優先的に適用されます。未指定の項目はデフォルト値（`runtime` / `detection_zone` の値）が使われます。

| キー | 型 | 説明 |
| --- | --- | --- |
| `min_score` | int | このフェーズが有効になる最低スコア |
| `detection_zone` | object \| null | 上書きする検出ゾーン |
| `scan_interval` | float \| null | 上書きするスキャン間隔 |
| `min_obstacle_pixels` | int \| null | 上書きする最小ピクセル数 |

## チューニングガイド

### 検出精度を上げるには

- `tolerance` を小さくする（例: 15-20）— ただし、ゲーム内で色にグラデーションがある場合は大きめに
- `min_obstacle_pixels` を大きくする — 偽検出を減らす
- `detection_zone` の範囲を狭くする — ノイズが少なくなる

### 反応速度を上げるには

- `scan_interval` を小さくする（例: 0.02 = 50 FPS）
- `detection_zone` の範囲を狭くする — 処理するピクセル数が減る
- キャリブレーション領域を必要最小限にする — キャプチャサイズが小さくなる

### 障害物の速度が上がるゲームへの対応

- `detection_zone.top` を小さくする — より上部（早い段階）で障害物を検出
- `scan_interval` を小さくする — ポーリング頻度を上げる
- `score_region` + `phases` でスコアに応じて自動調整 — 高スコア時にスキャン範囲を広げ、間隔を短くする
