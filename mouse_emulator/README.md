# Mouse Emulator

macOS 上でキーボード操作によるマウスエミュレーションを行うツールです。`mise` を利用して `register` と `emulate` のタスクを提供します。

## 必要要件

- macOS (Apple silicon)
- アクセシビリティで "ターミナル" によるキーボード/マウス操作の許可
- Python 3.11 以上
- `mise`, `uv`

## 使い方

1. `mise run resolve` で依存関係をセットアップします（`.venv` が自動作成されます）。
2. `mise run register <profile-name>` でプロファイルを作成し、`profiles/<profile-name>.json` に保存されます。登録時は画面上でキャリブレーションを行い、領域の左上・右下でそれぞれ `shift+enter` を押して範囲を決めます。割り当てたいキーの組み合わせを押すと「キー: ... に対応する座標をクリックしてください」と表示されるので、その後に目的の位置をクリックしてください。
3. `mise run emulate profiles/<profile>.json` で登録済みプロファイルに基づいてマウス操作をエミュレートします。実行時にはプロファイルの `calibration` 設定に従ってキャリブレーションが行われ、登録済みのキーを押すと対応する位置でクリックが発動します。

登録時に取得したキャリブレーション領域は自動的にプロファイルへ `preset` として保存されます。後続の実行で手動キャリブレーションをスキップしたい場合は、プロファイルに以下のような設定を追記・編集してください。

```json
{
  "actions": [...],
  "calibration": {
    "enabled": false,
    "color": "green",
    "preset": {
      "left": 120.0,
      "top": 80.0,
      "right": 1320.0,
      "bottom": 880.0
    }
  }
}
```

`enabled: false` かつ `preset` が有効な場合は、キャリブレーションをスキップして保存済みの絶対座標を利用します。現在のディスプレイ構成と一致しない場合や、`preset` が設定されていない場合は自動的に手動キャリブレーションへフォールバックします。実行時に強制的にキャリブレーションを行いたいときは `mise run emulate --calibrate profiles/<profile>.json`、逆にスキップを強制したいときは `--no-calibrate` を指定してください。

追加のオプション:

- `--pause-key` で一時停止/再開のホットキーを一時的に上書きできます（例: `--pause-key ctrl+shift+p`、`--pause-key none` で無効化）。
- `--log-file` を指定すると標準出力に加えてログファイルにも出力されます。`--log-overwrite` を併用すると起動時に既存ログを上書きします。
- プロファイル内では `controls.pause_toggle` と `logging.{file,mode}` を設定して既定値を保存できます。

詳細は `docs/mise` および `docs/uv` を参照してください。

> **補足**: `mise` タスクは `.venv/bin/python` を利用して実行します。`uv run` を直接使うと macOS の SystemConfiguration アクセス制限で失敗する環境があるため、`mise run resolve` で作成された仮想環境を前提としています。

## ドキュメント

- ドキュメント全体の目次: [`docs/README.md`](docs/README.md)
- Auto Emulator
  - [概要](docs/auto_emulator/overview.md)
  - [設定ガイド](docs/auto_emulator/configuration.md)
  - [CLI リファレンス](docs/auto_emulator/cli.md)
- Mouse Emulator
  - [概要](docs/mouse_emulator/overview.md)
  - [プロファイル仕様](docs/mouse_emulator/profiles.md)
- サンプル設定: [`docs/examples/`](docs/examples/)
