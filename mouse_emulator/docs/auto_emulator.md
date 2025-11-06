# Auto Emulator ドキュメント

本書は `auto_emulator` の設定方法と使い方をまとめたものです。既存の `mouse_emulator` とは別タスクで動作し、画像テンプレート照合や OCR をトリガーにマウス操作を自動化できます。

---

## 1. 概要

- CLI コマンド: `mise run auto-run --config <path>` で実行、`mise run auto-validate` で設定検証。
- 主要構成
  - **検出器 (Detectors)**: 画面キャプチャから条件判定（テンプレート照合 / OCR / 任意追加）。
  - **条件 (Conditions)**: 検出結果や共有ステートを評価して成功 / 失敗 / 継続を決定。
  - **アクション (Actions)**: クリック・ドラッグ・待機・ステート更新などの操作。
  - **ステップ (Steps)**: Watch → Condition → Action の単位。遷移やループ制御を保持。
  - **シナリオ (Workflow)**: 複数ステップの遷移で構成される自動化フロー。

## 2. インストール前提

- Python 3.11+
- `mise run resolve` で依存パッケージ取得
  - OpenCV（画像処理）, Pillow（スクリーンキャプチャ）, pytesseract（OCR）, numpy 等
- macOS (Apple Silicon) を想定
- Tesseract バイナリが必要（`brew install tesseract` など）。`pytesseract` から参照可能なパスに配置するか、設定で `tesseract_cmd` を指定。

## 3. 設定ファイル（YAML/JSON）

### 3.1 ルート構造

```yaml
version: "1.1"
name: "シナリオ名"
description: "概要"
runtime:
  capture_interval: 0.4     # 監視間隔（seconds）
  max_iterations: 50        # ステップ全体の最大実行回数（省略可）
  calibration:
    enabled: true           # 開始時キャリブレーション実行
    color: green            # ガイドメッセージ色
regions:
  - name: "main"
    left: 0.0               # キャリブレーション領域に対する相対座標
    top: 0.0
    right: 1.0
    bottom: 1.0
steps:
  - id: "step_id"
    description: "説明"
    watch: {...}
    conditions: {...}
    actions: [...]
    transitions: {...}
    control: {...}
```

### 3.2 Watch セクション

```yaml
watch:
  detector:
    type: "template" | "ocr" | "null" | 他
    options: {...}                 # 検出器ごとの設定
  region: "main"                   # `regions` で定義した名前
  interval: 0.5                    # 監視ループの待機時間（デフォルト: runtime.capture_interval）
  timeout: 10.0                    # 秒。超過で timeout 遷移へ
  max_attempts: 3 | "infinite"     # 試行回数
  stop_on_failure: false           # true で失敗即終了
```

### 3.3 Detector オプション

#### template

```yaml
detector:
  type: "template"
  options:
    template_path: "../../sample_images/button.png"
    threshold: 0.75     # 0.0〜1.0
    match_method: "TM_CCOEFF_NORMED"
    grayscale: true
```

- `template_path` は設定ファイルのディレクトリ基準で解決。
- `match_method` は OpenCV のテンプレートマッチ関数に準拠。
- 検出成功時は `DetectionResult.region` に一致領域が格納される。

#### ocr

```yaml
detector:
  type: "ocr"
  options:
    pattern: "complete|finish"   # 正規表現
    contains: null               # 部分一致に使う文字列
    lang: "eng"
    grayscale: true
    threshold: 150               # 二値化閾値 (0-255)
    tesseract_cmd: "/usr/local/bin/tesseract"  # 任意
```

- `pattern` と `contains` はどちらか一方 / 両方指定可能。
- 取得したテキストは `result.data["text"]` に保存される。

#### null

- 常に未検出。テストや待機用。

### 3.4 Conditions

```yaml
conditions:
  op: "all" | "any" | "not" | "match" | "always" | "never"
  conditions: [...]           # ネスト可能
  options: {...}
```

- `match`: `result.matched` が true かつ `options.min_score` 以上で成功。
- `state_equals` / `state_not_equals`: `shared_state` の値を比較。例:

```yaml
conditions:
  op: "state_equals"
  options:
    key: "phase"
    value: "waiting"
```

### 3.5 Actions

```yaml
actions:
  - type: "click"
    pointer_mode: "move" | "absolute"
    options:
      target:
        relative: [0.5, 0.5]  # 省略時は検出領域中心を利用
      offset: [0.0, 0.02]
      button: "left" | "right" | "middle"

  - type: "drag"
    options:
      start:
        use_detection: true
      end:
        relative: [0.8, 0.5]
      steps: 15
      step_delay: 0.01
      hold: 0.05

  - type: "wait"
    options:
      duration: 0.5

  - type: "set_state"
    options:
      key: "phase"
      value: "ready"
      remove: false
```

### 3.6 Transitions & Control

```yaml
transitions:
  success: "next_step_id"
  failure: "retry_step_id"
  timeout: "fallback"
  default: "backup_step"

control:
  repeat: 3 | "infinite"
  break_on: success | failure | timeout
  max_duration: 5.0              # 秒
```

- `repeat` を指定しない場合は 1 回のみ評価。
- `break_on` は該当結果でループを終了。
- ウォッチの `max_attempts` と併用することで柔軟なリトライ制御が可能。

## 4. 実行手順

1. **依存関係の解決**: `mise run resolve`
2. **設定ファイル検証**: `mise run auto-validate --config profiles/auto_emulator/example.yml`
3. **キャリブレーション**: 実行開始時に領域を指定（基本は画面全体を囲む）。
4. **本番実行**: `mise run auto-run --config <設定ファイル>`
   - `--calibrate/--no-calibrate` オプションでキャリブレーション有無を指定可能。
   - `ESC` / `Ctrl+C` で終了。

## 5. 共有ステートの活用

- `set_state` アクションで `key/value` を保存し、`state_equals` 条件で遷移を制御。
- シナリオ例:
  1. `detect_ready_button` ステップでボタンを検出 → `phase = "ready"`
  2. `press_ready_button` でクリック → `phase = "waiting"`
  3. `await_result` で OCR により結果テキストを検出 → `phase = "complete"`
- `shared_state` は `AutomationContext.shared_state` に保持され、全ステップ間で共有される。

## 6. キャプチャサービス

- 実行時は `PILScreenCaptureService`（`ImageGrab`）を使用。
- テストでは `FileSequenceCaptureService` で静的画像を順番に返す。
- `ScreenCaptureService` を実装すれば別方式（例：Metal API）への差し替えも可能。

## 7. テスト戦略

- `tests/test_detectors.py`：テンプレート照合・OCR の単体テスト。
- `tests/test_actions.py`：アクションの座標処理・ステート更新。
- `tests/test_runtime_engine.py`：ステータス遷移とループ制御の検証。
- `tests/test_conditions.py`：状態条件・スコア判定。

テスト実行は `mise run check` または `uv run pytest`。

## 8. サンプル構成ファイル

`profiles/auto_emulator/example.yml` はテンプレート検出 → ボタンクリック → OCR 判定 → ループ待機の最小シナリオです。プロジェクト固有のテンプレート画像を `sample_images/` などに配置し、パスを修正して利用してください。

## 9. 今後の拡張アイデア

- 検出器: UI アクセシビリティ API、RGB ヒストグラム比較など。
- アクション: キーボード入力、複合ジェスチャー、スクロール。
- DSL: シナリオ分岐（`selector` ノード）や並列実行の導入。
- 設定管理: JSONSchema / Pydantic モデルからの自動ドキュメント生成。

---

ご不明点があれば `docs/auto_emulator.md` に追記するか、コメントアウト形式でメモを残しておくと共有がしやすくなります。
