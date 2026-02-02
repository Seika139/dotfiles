# Walkthrough - tmux ステータスバー表示修正

macOS と Linux/WSL の両方で CPU/メモリ使用率が正しく表示されるように `.tmux.conf` を更新しました。

## 変更内容

### [.tmux.conf](file:///Users/suzukikenichi/dotfiles/.tmux.conf)

- `uname -s` による OS 条件分岐を追加。
- macOS では `top -l 1` と `memory_pressure` を使用するように変更。
- ステータスバー右側の最大長を `80` に拡張。

## 検証結果

### macOS での動作確認

以下のコマンドを実行して、値が正しく取得できることを確認しました。

1. **CPU 使用率取得:**
   `top -l 1 -n 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//'`
   -> 数値が取得できることを確認
2. **メモリ使用率取得:**
   `memory_pressure -Q | grep "System-wide memory free percentage" | awk '{print 100-$5}'`
   -> 数値が取得できることを確認

## 変更内容 (最終修正)

`printf` 内のフォーマット指定(`%.1f`)が tmux のエスケープシーケンスと競合し、表示が `.1f%` となってしまう問題を解決しました。

- **改善策:** `awk` の `printf` を使わず、単純な `print` による加算結果の出力に変更。
- **%% エスケープ:** tmux 側で `%%` を使用することで、最終的なステータスバー表示で確実に `%` が表示されるようにしました。
- **安定性:** `sed` などのパイプを減らし、`awk` 内でパターンマッチ（`/CPU usage/` 等）を行うことで、コマンドをより堅牢にしました。

## 検証結果

- ステータスバーに `CPU: 12.3% | Mem: 45.6%` (数値は動的) と正しく表示されることを確認しました。
