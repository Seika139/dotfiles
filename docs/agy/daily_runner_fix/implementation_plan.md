# キャッシュ保存先が正しく反映されない問題の修正

## 概要

`07_daily_runner.bash` において、キャッシュディレクトリの変数が以前のセッションから引き継がれた古いパスを優先して使用してしまっていた問題を修正します。

## 原因

以前のバージョンで `export` されていた `BDOTDIR_DAILY_CACHE_DIR` などの環境変数が、シェルを閉じずに `source` し直した場合に、`:=${...}` 記法（デフォルト値設定）によって古い値が保持され続けていました。これにより、新しい `bash/daily/.cache` ではなく、古い `~/.cache/bdotdir/daily` を探しに行き、そこにある古いスタンプファイルを見つけて「実行済み」と判断されていました。

## 変更内容

### [Component Name] bash

#### [MODIFY] [07_daily_runner.bash](file:///Users/suzukikenichi/dotfiles/bash/public/07_daily_runner.bash)

1. **変数割り当ての強制化**: `:=` によるデフォルト値設定ではなく、直接代入 `=` を使用して、必ずプロジェクト内のパスが使用されるようにします。
2. **関数名変更の整合性修正**: `unset` 対象に `_bdotdir_daily_log_verbose` を追加し、存在しない `_bdotdir_daily_log_info` を削除します。
3. **不要な関数のクリーンアップ**: `bdotdir_run_once_per_day` と `bdotdir_run_daily_script` も実行後に `unset` するようにし、シェル環境を汚染しないようにします。

## 検証計画

### 手動確認

1. `$BDOTDIR_DAILY_CACHE_DIR` が古いパスに設定されている状態で `source` し、正しく `bash/daily/.cache` が評価されることを確認。
2. `bash/daily/.cache` を削除した状態で、スクリプトが正しく実行されることを確認。
