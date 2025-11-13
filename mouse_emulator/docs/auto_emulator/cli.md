# CLI Reference

`auto_emulator` の Typer ベース CLI で利用できる主なサブコマンドとオプションをまとめます。いずれも `mise run resolve` で作成された `.venv` を前提に、`mise run auto-*` タスクから呼び出されます。

## サブコマンド

| コマンド | 説明 |
| --- | --- |
| `python -m auto_emulator run --config <path>` | ワークフローを実行します。 |
| `python -m auto_emulator validate --config <path>` | 設定ファイルの検証を行います。 |
| `python -m auto_emulator probe [--mode <mode>] [--interval <sec>]` | キャリブレーション領域に対するマウス座標を確認します。 |

> `mise run auto-run` などのラッパーから呼び出す場合も同じオプションを渡せます。

## 共通オプション

- `--pause-key <combo>`
  - 実行中に一時停止/再開をトグルするキーコンボ。例: `ctrl+p`, `ctrl+shift+p`。
  - `none`, `off`, `disable` を渡すと無効化。設定ファイルの `runtime.controls.pause_toggle` が既定値になります。

- `--log-file <path>`
  - 標準出力に加えてログファイルへも書き出します。相対パスは設定ファイルの `__base_dir__` を基準に解決されます。

- `--log-overwrite`
  - ログファイルを上書きモードで開きます。省略時は追記 (`append`)。設定ファイルでは `runtime.logging.mode` で制御できます。

- `--calibrate / --no-calibrate`
  - 実行時のキャリブレーション実施を強制します。未指定の場合は `runtime.calibration.enabled` に従います。

## `probe` コマンドのモード

| モード | 説明 |
| --- | --- |
| `click` (デフォルト) | クリックイベントが発生したタイミングで座標を表示します。 |
| `interval` | `--interval` で指定した周期で座標を表示します（最小 0.05s 程度）。 |

実行中は `esc` または `ctrl+c` で停止できます。`--pause-key` を指定した場合は一時停止/再開をトグル可能です。

### 取得できる座標の使い分け

`probe` の出力は複数の座標系を同時に表示します。設定ファイルへ転記するときは次のガイドラインに従ってください。

- `rel(region)=...`
  - 自動化シナリオの `actions[].options.target.relative` など、キャリブレーション領域に対する相対座標 (0.0〜1.0) が必要な場所で利用します。
- `abs(pynput)=...`
  - `runtime.calibration.preset.{left,top,right,bottom}` に保存する絶対座標です。`probe` 実行時のキャリブレーションと同じ表示領域であれば、この値をそのままプリセットに登録しても `_validate_preset_region` を通過します。
- `rel(screen)=...` / `abs(nss)=...`
  - デバッグ用途の参考情報です。マルチディスプレイ構成でどのスクリーンに属しているか、macOS の NSScreen 座標ではどの値になるかを確認できます。設定ファイルへ直接記述する必要はありません。

> `mise run auto-run --calibrate` などで手動キャリブレーションを実行した後に `probe` を起動すると、常に最新のキャリブレーション領域を基準とした `rel(region)` が得られます。

## エラー処理

- 設定ファイルの解析エラーや構文エラーは `ConfigurationError` をラップして `typer.Exit(code=1)` が発生します。
- 実行中に `KeyboardInterrupt` を受けると `typer.Exit(code=0)` で静かに終了します。
- ログファイルを指定すると、例外が発生した場合でも同内容が追記（または上書き）されます。

詳細な設定方法は [`configuration.md`](configuration.md) を参照してください。***
