# Documentation Index

このディレクトリでは `mouse_emulator` と `auto_emulator` の利用方法をテーマ別にまとめています。

## 構成

- `auto_emulator/`
  - `overview.md` … ツールの全体像とワークフローの概要
  - `configuration.md` … YAML/JSON 設定ファイルの書き方、検出器・条件・アクションの詳細
  - `cli.md` … `mise run auto-*` で利用可能なコマンドラインオプション、ログ設定、一時停止キーなど
- `mouse_emulator/`
  - `overview.md` … キーボード操作でマウスをエミュレートする仕組みの概要
  - `profiles.md` … プロファイル JSON のフィールド解説、キャリブレーションのプリセット化、ログ・一時停止設定
- `examples/` … 各ツールでそのまま試せる設定ファイル／プロファイル例

## はじめに

1. まだ環境構築をしていない場合は `README.md` に沿って `mise run resolve` を実行し、`.venv` を作成します。
2. `auto_emulator` を触りたい場合は `auto_emulator/overview.md` → `configuration.md` の順に読むと流れがつかみやすいです。
3. `mouse_emulator` のキーバインド制御を試す場合は `mouse_emulator/overview.md` と `profiles.md`、`examples/mouse_profile_basic.json` を参照してください。

必要に応じて `examples/` 内のファイルをコピーし、自分のケースに合わせて編集してみてください。***
