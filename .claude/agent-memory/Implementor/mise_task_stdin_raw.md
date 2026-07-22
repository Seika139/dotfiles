---
name: mise-task-stdin-raw
description: mise task はデフォルトで stdin を読まない。対話 fzf など stdin が必要な file task には raw=true が必須
metadata:
  type: project
---

mise の task はデフォルトで stdin を読まない（mise 本体がロックして横取りする）。task 内で対話 fzf 等の stdin 入力を使いたい場合は `#MISE raw=true`（TOML task では `raw = true`）を明示しないと動かない。

**Why:** 公式ドキュメント (tasks/running-tasks.html) に明記: "Stdin is not read by default. To enable this, set raw = true on the task that needs it." raw=true は他タスクとの並列実行を防ぐ (RWMutex write lock) 副作用もある。

**How to apply:** dotfiles リポジトリの `mise/tasks/repo-preset-install.sh` は `mise/scripts/repo-preset/select.sh` の対話 fzf (stdin 使用) にフォールバックする設計のため `#MISE raw=true` を付与した。同様に stdin/対話ツールを呼ぶ file task を書くときは必ずこのフラグを検討する。関連: [[mise-file-task-usage-flags]]
