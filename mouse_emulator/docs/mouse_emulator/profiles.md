# Profile Reference

`mouse_emulator` のプロファイルは JSON 形式で、キャリブレーション設定と複数のアクションを持ちます。`mise run register` で生成されたファイルをベースに手動編集する場合は、以下の構造を参考にしてください。

```json
{
  "actions": [
    {
      "description": "中央クリック",
      "keys": ["ctrl", "space"],
      "click_position": { "x": 0.5, "y": 0.5 }
    }
  ],
  "calibration": {
    "enabled": false,
    "color": "green",
    "preset": {
      "left": 120.0,
      "top": 80.0,
      "right": 1320.0,
      "bottom": 880.0
    }
  },
  "controls": {
    "pause_toggle": "ctrl+p"
  },
  "logging": {
    "file": "logs/mouse_emulator.log",
    "mode": "append"
  }
}
```

## セクション解説

### トップレベルフィールド

| フィールド    | 必須/任意 | デフォルト                                        | 説明                                                                       |
| ------------- | --------- | ------------------------------------------------- | -------------------------------------------------------------------------- |
| `actions`     | 必須      | なし                                              | アクション定義の配列。少なくとも 1 件必要です。                            |
| `calibration` | 任意      | `enabled: true`, `color: "green"`, `preset: null` | キャリブレーション挙動を制御します。省略時は自動キャリブレーションを実行。 |
| `controls`    | 任意      | `pause_toggle: "ctrl+p"`                          | 一時停止トグルなどの操作設定。                                             |
| `logging`     | 任意      | `file: null`, `mode: "append"`                    | ログ出力の設定。                                                           |

### `actions[]` の項目

| フィールド       | 必須/任意 | デフォルト | 説明                                                                         |
| ---------------- | --------- | ---------- | ---------------------------------------------------------------------------- |
| `description`    | 必須      | なし       | ユーザー向けの説明テキスト。空文字は許可されません。                         |
| `keys`           | 必須      | なし       | 発火させるキーコンボ。`register` で取得した形式を使用します。                |
| `click_position` | 必須      | なし       | キャリブレーション領域内の相対座標（0.0〜1.0）。範囲外の場合は実行時エラー。 |

### `calibration` の項目

| フィールド | 必須/任意 | デフォルト | 説明                                                                                              |
| ---------- | --------- | ---------- | ------------------------------------------------------------------------------------------------- |
| `enabled`  | 任意      | `true`     | `false` にすると手動キャリブレーションをスキップし、`preset` が設定されていればそれを利用します。 |
| `color`    | 任意      | `"green"`  | キャリブレーション時のガイダンスカラー（`default`/`green`/`blue`/`warning`/`fail`）。             |
| `preset`   | 任意      | `null`     | 既知の絶対座標。`enabled: false` と組み合わせることで即時利用できます。                           |

### `controls` の項目

| フィールド     | 必須/任意 | デフォルト | 説明                                                                 |
| -------------- | --------- | ---------- | -------------------------------------------------------------------- |
| `pause_toggle` | 任意      | `"ctrl+p"` | 実行中の一時停止/再開を切り替えるキー。`none` や空文字で無効化可能。 |

### `logging` の項目

| フィールド | 必須/任意 | デフォルト | 説明                                                      |
| ---------- | --------- | ---------- | --------------------------------------------------------- |
| `file`     | 任意      | `null`     | ログ出力先ファイル。未指定の場合は標準出力のみ。          |
| `mode`     | 任意      | `"append"` | `append` で追記、`overwrite` で起動時にファイルを初期化。 |

### `probe` で取得した値の登録先

`mise run auto-probe`（`python -m auto_emulator probe`）や `mise run probe` の出力は複数の座標系を併記します。JSON プロファイルへ手動登録する際は次を目安にしてください。

- `rel(region)=...`
  `actions[].click_position` など、キャリブレーション領域に対する相対値が必要なフィールドへ対応します。
- `abs(pynput)=...`
  `calibration.preset.left/top/right/bottom` へ書き込む絶対座標です。`probe` と同じ手順でキャリブレーションしていれば、そのままコピーしても `_validate_preset_region` の検証を通過します。
- `rel(screen)=...` / `abs(nss)=...`
  マルチディスプレイ時のデバッグ用情報です。登録不要ですが、ディスプレイ境界付近で値のずれがないか確認するときに参照できます。

## サンプル

- [`docs/examples/mouse_profile_basic.json`](../examples/mouse_profile_basic.json) … 最小構成のプロファイル例。
- [`docs/examples/auto_emulator_template.yml`](../examples/auto_emulator_template.yml) … テンプレート照合でトリガーする auto_emulator 例。
- [`docs/examples/auto_emulator_ocr.yml`](../examples/auto_emulator_ocr.yml) … OCR で文字列検出を行う auto_emulator 例。

CLI から一時的に設定を上書きしたい場合は次のオプションが利用できます。

- `mise run emulate --pause-key ctrl+p --log-file logs/session.log --log-overwrite --prof basic`
- `mise run emulate --calibrate --prof basic`

いずれもプロファイルが持つ設定を基準に、CLI の指定が優先されます。
