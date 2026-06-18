# automation

マウスを一定間隔で自動クリックするシンプルなユーティリティ集です。依存管理に `uv`、タスクランナーに `mise` を使用します（旧構成の `poetry` から移行しました）。

## 必要要件

- macOS (Apple silicon) または Windows
- macOS の場合: アクセシビリティでターミナルによるマウス/キーボード操作の許可
- Python 3.12 以上
- `mise`, `uv`

## セットアップ

```bash
cd automation
mise run resolve   # .venv を自動作成し、依存関係を同期します
```

## 使い方

### シンプルな自動クリック

現在のカーソル位置を一定間隔でクリックし続けます。

```bash
mise run click                    # 1秒間隔（既定）
mise run click --duration 0.01    # 0.01秒間隔で連打
```

- `Ctrl+Z` (Windows: `Left Alt+Z`) でクリックのオン/オフを切り替えます。
- `Ctrl+X` (Windows: `Left Alt+Q`) または `Esc` で終了します。

### 座標を記録して再生

複数のクリック位置とその間隔を記録し、記録した順序・タイミングでループ再生します（マクロのレコーダー兼プレイヤー）。

```bash
mise run click-coords                  # 記録間隔をそのまま再生
mise run click-coords --duration 0.5   # 記録が1点のみのときの間隔（秒）
```

1. 起動後 `Enter` で記録モードを開始します。
2. 記録したい位置を順にクリックします。
3. 再度 `Enter` で記録を確定すると、記録した座標・間隔で自動クリックを開始します。
4. オン/オフ・終了のホットキーは「シンプルな自動クリック」と同じです。

## タスク一覧

| タスク                  | 説明                                 |
| ----------------------- | ------------------------------------ |
| `mise run resolve`      | `.venv` を作成し依存関係を同期します |
| `mise run upgrade`      | 依存関係を最新バージョンへ更新します |
| `mise run reset-venv`   | `.venv` を作り直します               |
| `mise run format`       | `ruff format` でコードを整形します   |
| `mise run click`        | シンプルな自動クリックを起動します   |
| `mise run click-coords` | 座標記録・再生版を起動します         |

## 補足

- `mise` タスクは `uv run python -m automation.<module>` でスクリプトを実行します。モジュール実行のためパッケージのビルド/インストールは行いません (`pyproject.toml` の `[tool.uv] package = false`)。
- リポジトリ直下の `auto_click.py` は `keyboard` ライブラリ（macOS では root 権限が必要）を使う旧版で、`pynput` ベースの `automation/auto_click.py` に置き換えられています。mise タスクは後者を使います。
