# Configuration Guide

`auto_emulator` のワークフロー定義は YAML/JSON で記述します。ここでは主要セクションと代表的な指定方法をまとめます。

## 基本構造

```yaml
version: "1.1"
name: "シナリオ名"
description: "概要"
runtime:
  capture_interval: 0.4   # デフォルト監視間隔 (秒)
  max_iterations: 50       # 全体ループの最大回数 (省略可)
  calibration:
    enabled: true
    color: green
    preset:
      left: 120
      top: 80
      right: 1320
      bottom: 880
  controls:
    pause_toggle: "ctrl+p"
  logging:
    file: "logs/autorun.log"
    mode: append            # append or overwrite
regions:
  - name: "main"
    left: 0.0
    top: 0.0
    right: 1.0
    bottom: 1.0
steps:
  - id: "step_id"
    description: "説明"
    watch: { ... }
    conditions: { ... }
    actions: [ ... ]
    transitions: { ... }
    control: { ... }
```

### runtime

- `capture_interval`: `watch.interval` を省略した場合のデフォルト間隔。
- `max_iterations`: Step 実行の上限。`null` で無制限。
- `calibration`: `enabled` が `false` かつ `preset` が有効な場合はキャリブレーションをスキップして保存済みの座標を使用します。プリセットが現在のディスプレイと一致しない場合は自動的に手動キャリブレーションへフォールバックします。
- `controls.pause_toggle`: 実行中に一時停止／再開をトグルするホットキー。`none` や `disable` で無効化。
- `logging`: ログファイルとモードの指定。`auto-run` の CLI から `--log-file` や `--log-overwrite` を渡すと一時的に上書きできます。

### regions

`watch.region` から参照できる矩形領域を 0.0〜1.0 の相対座標で宣言します。省略時はキャリブレーション領域全体が対象になります。

## Watch セクション

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
  stop_on_failure: false
```

- `detector.type`: `template` / `ocr` / `null` など。独自実装を追加した場合はその名前を指定。
- `options`: 検出器ごとのパラメータ。`template` では `threshold` や `match_method`、`ocr` では `pattern` / `contains` / `lang` / `threshold` などを設定。
- `region`: `regions` で定義した名前。省略時はキャリブレーション領域全体。
- `interval`: 各試行の待機時間（省略時は `runtime.capture_interval`）。
- `timeout`: 秒数。経過すると `timeout` 遷移に進む。
- `max_attempts`: 試行回数。数値または `"infinite"`。
- `stop_on_failure`: true の場合、最初の失敗で Step を終了。

## Conditions

```yaml
conditions:
  op: "all"
  conditions:
    - op: "match"
      options:
        min_score: 0.8
    - op: "state_equals"
      options:
        key: "phase"
        value: "waiting"
```

- `op`: `all` / `any` / `not` / `match` / `always` / `never` / `state_equals` / `state_not_equals` / `text_contains` / `text_equals` / `text_matches`。
- `conditions`: `all` / `any` / `not` のときに子条件を列挙。
- `options`: 比較に必要な情報を指定。`match` では `min_score`、`state_*` では `key` と `value`、`text_*` では `value` と `ignore_case` を利用。

## Actions

代表的なアクション:

- `click`: `target.use_detection`（最後に検出した領域中心を使う）、`target.relative`、`offset`、`button`。
- `drag`: `start` と `end` のターゲット指定、`steps`、`step_delay`、`hold`。
- `wait`: `duration`（秒）。
- `set_state`: `key` / `value` / `remove`.
- `log`: `message` / `prefix`。省略時は `last_detection.data["text"]` を記録。

アクションは配列で順次実行されます。

## 例

`docs/examples/auto_emulator_template.yml` や `docs/examples/auto_emulator_ocr.yml` に、テンプレート照合・OCR を用いた具体例があります。ベースとなる `basic_autorun.yml` と合わせて、必要に応じてコピーして利用してください。

### OCR 結果で分岐するケース

次のサンプルは、特定領域から OCR で数値を読み取り、値に応じて遷移先を変える例です。

```yaml
steps:
  - id: "read_value"
    watch:
      detector:
        type: "ocr"
        options:
          region: "score_area"
          lang: "eng"
          grayscale: true
          threshold: 160
    conditions:
      op: "text_matches"
      options:
        value: "\\d+"
        ignore_case: true
    actions:
      - type: "set_state"
        options:
          key: "raw_score"
          value_from_detection: true
      - type: "set_state"
        options:
          key: "score"
          value_from_regex:
            source_state: "raw_score"
            pattern: "(\\d+)"
            group: 1
    transitions:
      success: "route_by_score"
      timeout: "fallback"

  - id: "route_by_score"
    watch: { detector: { type: "null" } }
    conditions:
      op: "always"
    actions: []
    transitions:
      default: "score_ge_50"

  - id: "score_ge_50"
    watch: { detector: { type: "null" } }
    conditions:
      op: "state_equals"
      options:
        key: "score"
        comparator: ">="
        value: 50
    transitions:
      success: "id_1"
      default: "score_ge_30"

  - id: "score_ge_30"
    watch: { detector: { type: "null" } }
    conditions:
      op: "state_equals"
      options:
        key: "score"
        comparator: ">="
        value: 30
    transitions:
      success: "id_2"
      default: "id_3"
```

上記では `value_from_detection` や `value_from_regex` を利用して OCR 結果を shared_state に保存し、`comparator` を使った比較で遷移先を切り分けています。コンパレータ演算はカスタム実装が必要な場合があるため、`ConditionEvaluator` に相応のロジックがあることを確認してください。***
