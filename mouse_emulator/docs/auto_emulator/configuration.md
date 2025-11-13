# Configuration Guide

`auto_emulator` のワークフロー定義は YAML/JSON で記述します。ここでは主要セクションと代表的な指定方法をまとめます。

## 基本構造

```yaml
version: "1.1"
name: "シナリオ名"
description: "概要"
runtime:
  capture_interval: 0.4 # デフォルト監視間隔 (秒)
  max_iterations: 50 # 全体ループの最大回数 (省略可)
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
    mode: append # append or overwrite
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
    actions: [...]
    transitions: { ... }
    control: { ... }
```

### トップレベルフィールド一覧

| フィールド    | 必須/任意 | デフォルト         | 説明                                                        |
| ------------- | --------- | ------------------ | ----------------------------------------------------------- |
| `version`     | 必須      | なし               | 設定フォーマットのバージョン文字列。                        |
| `name`        | 任意      | `null`             | フローの名称。                                              |
| `description` | 任意      | `null`             | シナリオの説明文。                                          |
| `runtime`     | 任意      | 各項目に既定値あり | 実行全体の共通設定。省略時は既定値が適用されます。          |
| `regions`     | 任意      | `[]`               | 相対座標で定義する領域リスト。                              |
| `steps`       | 必須      | なし               | 自動化ステップの配列。空にできません。                      |
| `metadata`    | 任意      | `{}`               | 任意のメタデータ。`__base_dir__` など内部情報を格納します。 |

### runtime

| フィールド              | 必須/任意 | デフォルト | 説明                                                                          |
| ----------------------- | --------- | ---------- | ----------------------------------------------------------------------------- |
| `capture_interval`      | 任意      | `0.2` 秒   | `watch.interval` を省略した場合に使用される監視間隔。                         |
| `max_iterations`        | 任意      | `null`     | ステップループの最大反復回数。`null` で無制限。                               |
| `calibration.enabled`   | 任意      | `true`     | `false` にすると `preset` を優先してキャリブレーションをスキップ。            |
| `calibration.color`     | 任意      | `"green"`  | キャリブレーションガイドのカラー。`default`/`green`/`blue`/`warning`/`fail`。 |
| `calibration.preset`    | 任意      | `null`     | 既知の絶対座標。`enabled: false` と組み合わせると事前設定を利用。             |
| `controls.pause_toggle` | 任意      | `"ctrl+p"` | 一時停止/再開のトグルキー。`none` や `disable` で無効化可能。                 |
| `logging.file`          | 任意      | `null`     | セッションログを保存するファイルパス。                                        |
| `logging.mode`          | 任意      | `"append"` | ログの書き込みモード (`append` / `overwrite`)。                               |

### regions

`watch.region` から参照できる矩形領域を 0.0〜1.0 の相対座標で宣言します。省略時はキャリブレーション領域全体が対象になります。

| フィールド                          | 必須/任意 | デフォルト | 説明                                                                         |
| ----------------------------------- | --------- | ---------- | ---------------------------------------------------------------------------- |
| `name`                              | 必須      | なし       | 領域名。`watch.region` で参照します。                                        |
| `description`                       | 任意      | `null`     | ドキュメント用の補足説明。                                                   |
| `left` / `top` / `right` / `bottom` | 必須      | なし       | 0.0〜1.0 の相対座標。`right > left`、`bottom > top` を満たす必要があります。 |

## Watch セクション

```yaml
watch:
  detector:
    type: "template"
    options:
      template_path: "../../sample_images/start_button.png"
      threshold: 0.72
      grayscale: true
      auto_shrink: true
      relative_size:
        width: 0.45
  region: "main"
  interval: 0.4
  timeout: 8.0
  max_attempts: "infinite"
  stop_on_failure: false
```

| フィールド         | 必須/任意 | デフォルト                 | 説明                                                   |
| ------------------ | --------- | -------------------------- | ------------------------------------------------------ |
| `detector.type`    | 必須      | なし                       | `template` / `ocr` / `null` など検出器の種類。         |
| `detector.options` | 任意      | `{}`                       | 検出器固有のパラメータ。型ごとの詳細は下表参照。       |
| `region`           | 任意      | キャリブレーション領域全体 | `regions` で定義した名前。省略すると全域をキャプチャ。 |
| `interval`         | 任意      | `runtime.capture_interval` | 各試行間のスリープ秒数。                               |
| `timeout`          | 任意      | `null`                     | 経過すると `timeout` 遷移にフォールバック。            |
| `max_attempts`     | 任意      | `1`                        | 試行回数の上限。`"infinite"` で無制限。                |
| `stop_on_failure`  | 任意      | `false`                    | `true` の場合、最初の失敗でステップを終了。            |

`template` 検出器で利用する主なオプション:

| フィールド                                     | 必須/任意 | デフォルト           | 説明                                             |
| ---------------------------------------------- | --------- | -------------------- | ------------------------------------------------ |
| `template_path`                                | 必須      | なし                 | 比較対象となるテンプレート画像へのパス。         |
| `threshold`                                    | 任意      | `0.8`                | マッチング判定に使用するしきい値。               |
| `match_method`                                 | 任意      | `"TM_CCOEFF_NORMED"` | OpenCV のテンプレートマッチング手法。            |
| `grayscale`                                    | 任意      | `true`               | マッチング前にグレースケール化するか。           |
| `auto_shrink`                                  | 任意      | `true`               | 監視領域よりテンプレートが大きい場合に自動縮小。 |
| `relative_size.width` / `relative_size.height` | 任意      | なし                 | キャプチャ領域に対する比率でリサイズを指定。     |

`ocr` 検出器の主なオプション:

| フィールド                      | 必須/任意 | デフォルト | 説明                                                   |
| ------------------------------- | --------- | ---------- | ------------------------------------------------------ |
| `pattern` / `contains` / `text` | 任意      | なし       | 検出テキストの評価条件。用途に合わせていずれかを指定。 |
| `lang`                          | 任意      | `"eng"`    | Tesseract に渡す言語コード。                           |
| `threshold`                     | 任意      | `null`     | 2 値化しきい値。未指定なら自動。                       |
| `grayscale`                     | 任意      | `true`     | OCR 前にグレースケール化するか。                       |

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

| フィールド   | 必須/任意 | デフォルト | 説明                                                                                                     |
| ------------ | --------- | ---------- | -------------------------------------------------------------------------------------------------------- |
| `op`         | 必須      | なし       | 条件の種別。`all`/`any`/`not`/`match`/`always`/`never`/`state_*`/`text_*` を指定。                       |
| `conditions` | 条件付き  | `[]`       | `all`・`any` は 1 件以上、`not` は 1 件のみ必須。その他の演算子では省略。                                |
| `options`    | 条件付き  | `{}`       | 判定に必要な追加パラメータ。例: `match.min_score`、`state_equals.key`/`value`、`text_matches.value` 等。 |

## Actions

代表的なアクション:

| フィールド     | 必須/任意 | デフォルト | 説明                                                               |
| -------------- | --------- | ---------- | ------------------------------------------------------------------ |
| `type`         | 必須      | なし       | 実行するアクション種別。`click` / `wait` など。                    |
| `pointer_mode` | 任意      | `"move"`   | ポインタ操作時のモード。`move`/`absolute`/`adaptive`。             |
| `options`      | 任意      | `{}`       | アクション固有パラメータ。タイプごとの詳細を以下にまとめています。 |

### `click` アクション

| オプション             | 必須/任意 | デフォルト   | 説明                                                                                                        |
| ---------------------- | --------- | ------------ | ----------------------------------------------------------------------------------------------------------- |
| `target.use_detection` | 任意      | `true`       | 直前の検出結果 (`DetectionResult`) が持つ領域中心をクリック対象にします。検出がない場合はエラーになります。 |
| `target.relative`      | 任意      | `null`       | `[x, y]`（0〜1）の相対座標。指定すると `use_detection` より優先され、明示した地点をクリックします。         |
| `offset`               | 任意      | `[0.0, 0.0]` | クリック座標に加算する相対オフセット。微調整に使用します。                                                  |
| `button`               | 任意      | `"left"`     | クリックに利用するボタン。`left` / `right` / `middle` を指定できます。                                      |

> メモ: `pointer_mode` を `"absolute"` にすると、相対座標をディスプレイ座標に変換してクリックします。`move` / `adaptive` では相対座標のまま `click_relative` が呼ばれます。

### `drag` アクション

| オプション            | 必須/任意 | デフォルト    | 説明                                                                          |
| --------------------- | --------- | ------------- | ----------------------------------------------------------------------------- |
| `start.use_detection` | 任意      | `true`        | 始点を直前検出の中心にします。                                                |
| `start.relative`      | 任意      | `null`        | 始点の相対座標。指定すると `start.use_detection` より優先されます。           |
| `end.use_detection`   | 条件付き  | `false`       | 終点に検出結果を利用する場合に `true` を設定します。                          |
| `end.relative`        | 条件付き  | なし          | `[x, y]` の相対座標。`end.use_detection` を指定しない場合はこちらが必須です。 |
| `offset`              | 任意      | `[0.0, 0.0]`  | 始点・終点の両方に適用する共通オフセット。                                    |
| `start_offset`        | 任意      | `offset` の値 | 始点のみのオフセット。`offset` より優先されます。                             |
| `end_offset`          | 任意      | `offset` の値 | 終点のみのオフセット。`offset` より優先されます。                             |
| `button`              | 任意      | `"left"`      | ドラッグに使用するボタン。                                                    |
| `steps`               | 任意      | `12`          | ドラッグ経路を分割するステップ数。1 以上の整数。                              |
| `step_delay`          | 任意      | `0.01`        | 各ステップ間の待機秒数。                                                      |
| `hold`                | 任意      | `0.05`        | 押下開始時にボタンを保持する秒数。                                            |

### `wait` アクション

| オプション | 必須/任意 | デフォルト | 説明                                             |
| ---------- | --------- | ---------- | ------------------------------------------------ |
| `duration` | 必須      | なし       | 待機する秒数。0 より大きい値を指定してください。 |

### `set_state` アクション

| オプション | 必須/任意 | デフォルト | 説明                                                                |
| ---------- | --------- | ---------- | ------------------------------------------------------------------- |
| `key`      | 必須      | なし       | `AutomationContext.shared_state` に保存するキー。空文字は不可です。 |
| `value`    | 任意      | `null`     | 保存する値。任意の JSON 互換型を登録できます。                      |
| `remove`   | 任意      | `false`    | `true` を指定すると `key` を削除し、`value` は無視されます。        |

### `log` アクション

| オプション | 必須/任意 | デフォルト | 説明                                                                                        |
| ---------- | --------- | ---------- | ------------------------------------------------------------------------------------------- |
| `message`  | 条件付き  | なし       | 出力する文字列。未指定で `last_detection.data["text"]` が存在する場合はその値を使用します。 |
| `prefix`   | 任意      | `"[auto]"` | メッセージの先頭に付与するプレフィックス。                                                  |

### `noop` アクション

設定検証などに利用する「何もしない」アクションです。追加オプションはありません。

アクションは配列として複数指定できます。YAML ファイルの上から順に実行され、いずれかが失敗するとステップ全体が失敗扱いになります。

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

上記では `value_from_detection` や `value_from_regex` を利用して OCR 結果を shared_state に保存し、`comparator` を使った比較で遷移先を切り分けています。コンパレータ演算はカスタム実装が必要な場合があるため、`ConditionEvaluator` に相応のロジックがあることを確認してください。\*\*\*
