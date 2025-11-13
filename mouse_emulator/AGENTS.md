# Mouse Emulator / Auto Emulator Agent Guide

macOS (Apple Silicon) 向けのキーボード駆動マウス制御ツールです。`mouse_emulator` で手動操作を補助し、`auto_emulator` でテンプレート照合や OCR を利用した自動実行フローを構築します。本書はプロジェクトを触るエージェント向けの簡易ガイドです。

## セットアップ

- 前提: macOS (Apple Silicon) / Python 3.11 以上 / アクセシビリティで「ターミナル」が入力監視・制御を許可済み
- 依存管理: [mise](https://mise.jdx.dev/) + [uv](https://github.com/astral-sh/uv)

```bash
# 依存解決と仮想環境 (.venv) の作成
cd mouse_emulator
mise run resolve

# VS Code 等で開く場合は `mouse_emulator/.venv` を使用
```

> **NOTE:** `mise run` 実行時に `~/Library/Caches/mise` への書き込み権限が不足していると警告が出ます。必要に応じて権限を修正してください。

## ディレクトリ概要

| パス                             | 説明                                                                                     |
| -------------------------------- | ---------------------------------------------------------------------------------------- |
| `src/mouse_emulator`             | 手動エミュレータ CLI (`register`, `emulate`) 本体。                                      |
| `src/auto_emulator`              | 自動化シナリオエンジン。テンプレート検出器や OCR などを含む。                            |
| `src/mouse_core`                 | キャリブレーションやポインタ制御などの共通モジュール。                                   |
| `profiles/mouse_emulator/*.json` | 手動エミュレータ用プロファイル。                                                         |
| `profiles/auto_emulator/*.yml`   | 自動化シナリオ設定ファイル。`sample2.yml` が最新サンプル。                               |
| `docs/`                          | 仕様ドキュメント (`mouse_emulator/profiles.md`, `auto_emulator/configuration.md` など)。 |

## 主な mise タスク

| コマンド                                       | 説明                                                                                           |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `mise run resolve`                             | `.venv` を生成し依存を同期。最初に実行する。                                                   |
| `mise run register --prof <name>`              | 新規プロファイルを作成 (キャリブレーション + キー登録)。                                       |
| `mise run emulate --prof <path-or-name>`       | 指定プロファイルでマウス操作を再生。`--pause-key`、`--log-file` 等で一時的に設定を上書き可能。 |
| `mise run auto-run --config <config.yml>`      | `auto_emulator` を起動しテンプレート/OCR ベースの自動シナリオを実行。                          |
| `mise run auto-validate --config <config.yml>` | 自動化設定ファイルの検証。                                                                     |
| `mise run check` / `mise run format`           | `ruff`, `mypy`, `pytest` を用いた品質確認。 (キャッシュ書き込み権限に注意)                     |

## プロファイル (mouse_emulator)

- JSON 形式。`actions[]` は必須で、各要素は `description`, `keys`, `click_position` を持ちます。
- キャリブレーション設定は `calibration.enabled` / `calibration.preset` / `calibration.color` で制御。プリセットを使う場合は `enabled: false` と併用します。
- 一時停止トグルやロギングは `controls` / `logging` に保存でき、CLI 引数で一時的に上書き可能。
- 詳細仕様は `docs/mouse_emulator/profiles.md` を参照。

## 自動化シナリオ (auto_emulator)

- 設定は YAML/JSON で `docs/auto_emulator/configuration.md` に詳述。トップレベル項目、`watch` / `conditions` / `actions` の必須・デフォルトを表形式でまとめ済み。
- `template` 検出器は `auto_shrink` (既定 `true`) で監視領域を超えるテンプレートも自動縮小。`relative_size.width/height` で比率指定が可能。
- `actions` 配列は YAML に記述した順に実行され、途中で例外が発生するとそのステップは失敗扱いになり後続へ進みません。
- `profiles/auto_emulator/sample2.yml` が最新サンプル。テンプレート画像は `profiles/auto_emulator/images/` でメンテナンスしてください。

## 実装上の注意

- `TerminationMonitor` は macOS の TIS API 制約を避けるため単一リスナー構成です。キーボード監視を追加する場合は既存のモニタ経由でイベントを渡す設計を崩さないこと。
- テンプレート検出ではキャプチャ配列サイズに合わせてリサイズするよう `_prepare_template` を実装済み。`relative_size` を調整することで高解像度でも安全に動作します。
- `ruff format` 利用に合わせて `COM812` は lint 無効化済み。警告が出ても無視して構いません。
- 便利なテストセット: `pytest tests/test_detectors.py tests/test_emulate_calibration.py tests/test_termination.py`。自動化シナリオは実機でのスポット確認を推奨します。

## よくあるトラブルと対処

| 症状                                                     | 対処                                                                                                        |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `mise` がキャッシュ書き込みエラーを出す                  | `~/Library/Caches/mise` の権限を修正 (`chmod` / `chown`) する。                                             |
| `uv run` が `TISCopyCurrentKeyboardInputSource` で落ちる | 旧実装時の問題。リスナー追加時は TerminationMonitor の仕組みを尊重する。                                    |
| `matchTemplate` でアサーション失敗                       | テンプレートと監視領域のサイズが不整合。`auto_shrink` や `relative_size` を見直すかテンプレートを撮り直す。 |

## 参考リソース

- `docs/mouse_emulator/overview.md` … 手動エミュレータ機能の概要
- `docs/mouse_emulator/profiles.md` … プロファイル構造の詳細
- `docs/auto_emulator/configuration.md` … 自動化設定リファレンス
- `docs/examples/` … JSON/YAML サンプル集
- `mouse_emulator/todo.md` … 既知の TODO や改善案

新しい変更を加えた際は、関連ドキュメントとこのガイドの更新を忘れずに行ってください。
