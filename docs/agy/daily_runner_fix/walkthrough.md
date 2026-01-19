# 日次スクリプト実行不可（古いキャッシュ参照）の修正 完了報告

## 変更内容

キャッシュを削除しても日次スクリプトが実行されない問題（以前のセッションの古いキャッシュパスを引き継いでいた問題）を修正しました。

### [Component Name] bash

#### [MODIFY] [07_daily_runner.bash](file:///Users/suzukikenichi/dotfiles/bash/public/07_daily_runner.bash)

- **キャッシュパス設定の修正**: `:=`（未設定時のみ代入）から `=`（強制代入）に変更しました。これにより、以前のセッションで `export` されていた古いキャッシュパス（`~/.cache/bdotdir/daily`）が残っていても、必ずプロジェクト内の `bash/daily/.cache` を使用するように強制しました。
- **後処理（unset）の修正**:
  - ユーザーによる関数名の変更（`_bdotdir_daily_log_info` → `_bdotdir_daily_log_verbose`）に合わせて、実行後の `unset` 対象を `_bdotdir_daily_log_verbose` に修正しました。
  - `bdotdir_run_once_per_day` などの主要な関数も、実行が終わったら `unset` するようにし、シェル環境をクリーンに保つようにしました。

## 検証結果

### 手動確認内容

1. `BDOTDIR_DAILY_CACHE_DIR` に古いパスをセットした状態でスクリプトを `source` し、内部で正しく `bash/daily/.cache` に上書きされることを確認しました。
2. これにより、プロジェクト内のキャッシュディレクトリだけを見に行くようになり、古い場所にあるスタンプファイルに邪魔されずに実行されるようになりました。

## 補足

古いキャッシュディレクトリ `~/.cache/bdotdir` はもう使用しませんので、不要であれば削除していただいて問題ありません。

```bash
rm -rf ~/.cache/bdotdir
```
