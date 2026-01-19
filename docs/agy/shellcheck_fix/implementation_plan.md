# ShellCheck 警告の修正計画

## 概要

`bash/mise.toml` の `shellcheck` タスクで報告された警告を修正し、スクリプトの堅牢性と品質を向上させます。

## 修正内容

### [Component Name] bash

#### [MODIFY] [11_alias.bash](file:///Users/suzukikenichi/dotfiles/bash/public/11_alias.bash)

- **SC2086**: `sed s/^M//g "$1" | less "$LESS"` および `less "$LESS" "$1"` のようにクォートを追加します。

#### [MODIFY] [41_ltsv_to_json.bash](file:///Users/suzukikenichi/dotfiles/bash/public/41_ltsv_to_json.bash)

- **SC2128**: `read -ra line` を `read -r line` に修正（単一の文字列として読み込むため）。
- **SC2162**: `read key value` を `read -r key value` に修正します。

#### [MODIFY] [12_git_alias.bash](file:///Users/suzukikenichi/dotfiles/bash/public/12_git_alias.bash)

- **SC2089/SC2090**: `command1` を配列に変更し、`"${command1[@]}"` で実行するように修正します。
- **SC2086**: `git diff "$2".."$3"` のようにクォートを追加します。

#### [MODIFY] [04_prompt.bash](file:///Users/suzukikenichi/dotfiles/bash/public/04_prompt.bash)

- **SC2016**: `PS1` 設定時のバッククォートは遅延評価のために意図的に使用されているため、`# shellcheck disable=SC2016` を追加します。

## 検証計画

### 自動テスト

1. `mise run shellcheck` を実行し、修正したファイルの警告が消えていることを確認。
