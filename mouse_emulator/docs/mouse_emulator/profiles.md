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

- `actions`: 少なくとも 1 件必要です。
  - `description`: 任意の説明文。
  - `keys`: キーコンボを表す配列。`register` で収集された値と同じ形式を指定します。
  - `click_position`: キャリブレーション領域に対する相対座標（0.0〜1.0）。
- `calibration`: 実行時のキャリブレーション挙動。
  - `enabled`: `false` の場合は `preset` があればそれを利用します。
  - `color`: キャリブレーションのガイダンス表示色（`default`, `green`, `blue`, `warning`, `fail`）。
  - `preset`: 保存済みの絶対座標。ディスプレイ構成が変わった場合は自動でフォールバックして手動キャリブレーションを行います。
- `controls.pause_toggle`: 実行中に一時停止／再開をトグルするホットキー。`none` や空文字で無効化可能。
- `logging`: ログ設定。
  - `file`: ログ出力先ファイル（省略可能）。
  - `mode`: `"append"` または `"overwrite"`。

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

いずれもプロファイルが持つ設定を基準に、CLI の指定が優先されます。***
