# Auto Emulator Overview

`auto_emulator` は画像テンプレート照合や OCR の結果に基づいてマウス操作を自動化するエンジンです。`mouse_emulator` とは別タスクで動作し、次の部品でシナリオを構成します。

- **Detectors**: 画面キャプチャから状態を判定（テンプレート照合・OCR など）。
- **Conditions**: 検出結果や共有ステートの値をもとに成功/失敗/継続を判断。
- **Actions**: クリック・ドラッグ・待機・ステート更新・ログ出力などの操作。
- **Steps**: Watch → Condition → Action をまとめた単位。遷移やループ制御を保持。
- **Workflow**: 複数の Step を組み合わせた自動化フロー。

## 主なコマンド

`mise run resolve` で `.venv` を用意したうえで、次のラッパーを利用できます。

| コマンド | 説明 |
| --- | --- |
| `mise run auto-run --config <path>` | ワークフローを実行 |
| `mise run auto-validate --config <path>` | 設定ファイルの検証 |
| `mise run auto-probe --mode <mode>` | キャリブレーション領域に対する座標のプローブ |

> **Note:** これらのタスクは内部で `.venv/bin/python` を呼び出します。macOS では `uv run` が SystemConfiguration の制限でクラッシュする環境があるため、`.venv` を前提とした構成にしています。

CLI オプションの詳細は [`cli.md`](cli.md) を参照してください。設定ファイルの書き方は [`configuration.md`](configuration.md) にまとまっています。

すぐに試したい場合は [`../examples/auto_emulator_template.yml`](../examples/auto_emulator_template.yml) や [`../examples/auto_emulator_ocr.yml`](../examples/auto_emulator_ocr.yml) をコピーし、パスや閾値を環境に合わせて調整してください。
