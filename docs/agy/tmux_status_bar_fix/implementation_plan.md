# tmux ステータスバー表示修正 (macOS 対応)

現在の `.tmux.conf` では Linux/WSL 前提のコマンド (`top -bn1`, `free`) が使用されており、macOS では動作しません。
OS を判定して、適切なコマンドを呼び出すように修正します。

## 提案される変更

### [.tmux.conf](file:///Users/suzukikenichi/dotfiles/.tmux.conf)

`status-right` の設定を、OS に応じて切り替えるように変更します。

#### 修正内容

```tmux
# macOS (Darwin) の場合
if-shell 'uname -s | grep -q Darwin' \
    'set -g status-right "\"#{=21:pane_title}\" | CPU: #(top -l 1 -n 0 | grep \"CPU usage\" | awk \"{print \$3}\" | sed \"s/%%//\")%% | Mem: #(memory_pressure -Q | grep \"System-wide memory free percentage\" | awk \"{print 100-\$5}\")%% "' \
    'set -g status-right "\"#{=21:pane_title}\" | CPU: #(top -bn1 | grep \"Cpu(s)\" | awk \"{print \$2}\")%% | Mem: #(free | grep Mem | awk \"{printf \\\"%.0f%%%%\\\", \$3/\$2 * 100}\") "'
```

> [!NOTE]
>
> - macOS の `top` は `-l 1 -n 0` を使うことで、プロセス情報を取得せずに統計情報だけを素早く取得できます。
> - メモリ使用率は `memory_pressure -Q` から「空き容量」のパーセンテージを取得し、100 から引くことで使用率を算出します。

## 検証計画

### 手動確認

1. tmux をリロード (`PREFIX + r`) または `tmux source-file ~/.tmux.conf` を実行。
2. ステータスバー右側に CPU と Mem の値が表示されることを確認。
