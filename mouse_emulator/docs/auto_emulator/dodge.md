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
  2. detection_zone 内の各レーンを numpy でスキャン
  3. 障害物色 (RGB ±tolerance) に一致するピクセル数をカウント
  4. min_obstacle_pixels 以上 → そのレーンに障害物あり
  5. 安全なレーンのうち現在位置に最も近いものを選択
  6. レーン変更が必要な場合のみタップ（同じレーンならスキップ）
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
    # preset:              # キャリブレーション済みの場合
    #   left: 100
    #   top: 200
    #   right: 1100
    #   bottom: 900
  controls:
    pause_toggle: "ctrl+p"
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
