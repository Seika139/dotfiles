# Auto Emulator ドキュメント

本書は `auto_emulator` の設定方法と使い方をまとめたものです。既存の `mouse_emulator` とは別タスクで動作し、画像テンプレート照合や OCR をトリガーにマウス操作を自動化できます。

---

## 1. 概要

- CLI コマンド: `mise run auto-run --config <path>` で実行、`mise run auto-validate` で設定検証。キャリブレーション後の座標確認は `mise run auto-probe` を利用。
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
  capture_interval: 0.4 # 監視間隔（seconds）
  max_iterations: 50 # ステップ全体の最大実行回数（省略可）
  calibration:
    enabled: true # 開始時キャリブレーション実行
    color: green # ガイドメッセージ色
regions:
  - name: "main"
    left: 0.0 # キャリブレーション領域に対する相対座標
    top: 0.0
    right: 1.0
    bottom: 1.0
steps:
  - id: "step_id"
    description: "説明"
    watch: { ... }
    conditions: { ... }
    actions: [...]
    transitions: { ... }
    control: { ... }
```

### 3.2 Watch セクション

- `detector.type` … `"template"`, `"ocr"`, `"null"` など。拡張した場合は新しい type を指定。
- `options` … 検出器ごとのパラメータ。JSON/YAML で辞書として記述。
  - `template` では `template_path` を設定ファイルから見た相対パスで記述する（例: `../../sample_images/foo.png`）。
  - `ocr` は `pattern`（正規表現）, `contains`（部分一致）, `lang`, `threshold` などを利用可。
- `region` … `regions` で定義した名前。省略するとキャリブレーション領域全体。
- `interval` / `timeout` / `max_attempts` / `stop_on_failure` を組み合わせてリトライ制御を行う。

#### よくある記述例

```yaml
watch:
  detector:
    type: "template"
    options:
      template_path: "../../sample_images/start_button.png"
      threshold: 0.72
      grayscale: true
  region: "main"
  interval: 0.4
  timeout: 8.0
  max_attempts: "infinite"
```

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
    threshold: 0.75 # 0.0〜1.0
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
    pattern: "complete|finish" # 正規表現
    contains: null # 部分一致に使う文字列
    lang: "eng"
    grayscale: true
    threshold: 150 # 二値化閾値 (0-255)
    tesseract_cmd: "/usr/local/bin/tesseract" # 任意
```

- `pattern` と `contains` はどちらか一方 / 両方指定可能。
- 取得したテキストは `result.data["text"]` に保存される。

#### null

- 常に未検出。テストや待機用。

### 3.4 Conditions

- `op` には `all`/`any`/`not`/`match`/`always`/`never` に加え、`state_equals`/`state_not_equals`、OCR テキストを扱う `text_contains`/`text_equals`/`text_matches` を使用できる。
- `conditions` は `all`/`any`/`not` のみがネスト可能。`match` や `text_*` など比較系は子を持てない。
- `options` の主な項目:
  - `min_score` … `match` 用。`result.score` がこの値以上で成功。
  - `key` / `value` … state 系のキーと比較値。
  - `ignore_case` … テキスト比較時に大文字小文字を無視する（デフォルト true）。
  - `value` に正規表現を指定すると `text_matches` で利用できる。

```yaml
conditions:
  op: "all" | "any" | "not" | "match" | "always" | "never" | "state_equals" | "state_not_equals" | "text_contains" | "text_equals" | "text_matches"
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

- `text_*`: OCR などの結果テキストを評価。`value`（比較対象）と `ignore_case`（省略時 true）を指定し、部分一致 / 完全一致 / 正規表現をサポート。

### 3.5 Actions

- 各アクションは `options` で細かい振る舞いを指定する。
  - `click`: `target.relative`・`target.use_detection`・`offset`・`button` など。
  - `drag`: `start` / `end` のターゲット（`use_detection` を使うと最後に検出した領域中心が参照される）、`steps`・`step_delay`・`hold`。
  - `wait`: `duration`（秒）。必ず正の値。
  - `set_state`: `key` と `value` を指定。`remove: true` でキー削除。
  - `log`: `message`（省略時は `last_detection.data["text"]` を利用）と `prefix`。
- アクションは複数指定できる。配列で列挙された順に実行される。

サンプル：

```yaml
actions:
  - type: "click"
    options:
      target:
        use_detection: true
      offset: [0.0, 0.02]
      button: "left"
  - type: "wait"
    options:
      duration: 0.5
  - type: "log"
    options:
      prefix: "[auto]"
      message: "ボタンをクリックしました"
```

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

  - type: "log"
    options:
      message: "準備完了を検出しました"
      prefix: "[auto]"
```

### 3.6 Transitions & Control

- `transitions` でステップ間遷移を定義。`success`/`failure`/`timeout`/`default` のいずれかに次ステップ ID を記述する。
- `control.repeat` で同じステップを繰り返す回数を指定（整数）。`break_on` で特定結果が出たらループを抜ける。
- `runtime.max_iterations` と合わせて無限ループを防ぐ。

```yaml
transitions:
  success: "next_step_id"
  failure: "retry_step_id"
  timeout: "fallback"
  default: "backup_step"

control:
  repeat: 3 | "infinite"
  break_on: success | failure | timeout
  max_duration: 5.0 # 秒
```

- `repeat` を指定しない場合は 1 回のみ評価。
- `break_on` は該当結果でループを終了。
- ウォッチの `max_attempts` と併用することで柔軟なリトライ制御が可能。

## 4. 実行手順

1. **依存関係の解決**: `mise run resolve`
2. **設定ファイル検証**: `mise run auto-validate --config profiles/auto_emulator/example.yml`
3. **キャリブレーション支援**: `mise run auto-probe` でキャリブレーション後にカーソル座標の絶対・相対値を確認（`--mode click` でクリック時のみ表示）。
4. **本番実行**: `mise run auto-run --config <設定ファイル>`
   - `--calibrate/--no-calibrate` オプションでキャリブレーション有無を指定可能。
   - 実行中に `Esc` または `Ctrl+C` を押すとすぐに停止できます（グローバルリスナーで監視）。

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
- ステップ進行状況は標準出力に `[auto] step=...` / `result=...` としてログされる。詳細ログが欲しい箇所は `type: log` アクションで任意のメッセージを追記できる。
- `mise run auto-probe --mode interval` で定期的な座標確認、`--mode click` でクリック時のみ座標を採取できます（いずれも `Ctrl+C` で終了）。

## 7. 設定作成のヒント

1. **画像素材を整理**
   `sample_images/` やプロジェクト固有の `assets/` ディレクトリを用意し、テンプレートに使う画像を配置。`mise run auto-probe --mode click` で相対座標を事前に把握できる。

2. **テンプレート照合の調整**

   - 大きく形が異なるボタンは個別にテンプレート化する。複数サイズが存在する場合はパターンごとにステップを分けるか、`match_method`・`threshold` を変えてテストする。
   - `mise run auto-validate` を実行すると YAML の構文や設定値のバリデーションが行われるため、早めにエラーを検知できる。

3. **OCR の文字列確認**

   - `mise run auto-probe` で相対座標を把握し、OCR 用の領域に別ステップを割り当てる。
   - `tests/test_detectors.py` の OCR テストを参考に、実際のスクリーンショットで `pattern` や `contains` を調整するとよい。

4. **アクションの共通化**

   - よく使うクリックポイントは `set_state` でフェーズを分けておくと後続ステップで条件分岐がしやすい。
   - 複数箇所で同じログを出したい場合は `log` アクションの `prefix` を統一しておくと、標準出力のフィルタリングがしやすい。

5. **テストと回帰確認**
   - `docs/examples/basic_autorun.yml` はテンプレート → クリック →OCR の最小シナリオ例。自分のプロジェクト用にテンプレートパスを差し替えて試せる。
   - `tests/` 配下に独自の画像を置いて pytest を回すことで、設定変更時の回帰を早期に検知可能。

---

- 基本サンプル: `docs/examples/basic_autorun.yml`
- 標準の検出器／アクション／条件が足りなくなったら、`src/auto_emulator/detectors/` や `src/auto_emulator/actions/` にプラグインを追加し、設定から `type` を指定すれば拡張できます。

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
