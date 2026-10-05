# Claude Instructions for this Profile

This profile is applied to user's global setting.
Use Japanese for communication.

## Main Session Policy

- メインセッションは以下の対応に専念する
  - 開発ワークフローの設計と管理
    - Default Workflow: `plan` -> `architecture design` -> `codex architecture review` -> `implement` -> `codex code/security review`
- ソフトウェアの全体設計
- 知識の再利用設計と管理
  - 全ての開発で再利用可能な知識は MEMORY に保存する
  - 特定のプロジェクトで再利用が必要な知識はプロジェクトの `CLAUDE.md` に保存する
  - 特定箇所で再利用が必要な知識は `.claude/rules` に保存する
  - 再利用可能なワークフローは `skill` として保存する

## Change Discipline

- 要求を満たす範囲に収まるように変更を限定する。ただし、差分の少なさよりも正しさや安全性を優先する。
- 何かを削除したり移行する際は、過去のコードやデータを残さず積極的に削除する。gitの履歴から復元できるものは確認なく削除してよい。バックアップが必要な場合は削除前にユーザーに確認する。

## Sub-agent Delegation Policy

- model/reasoningは担当するタスクの難易度に応じて選択する
  - 基本は `sonnet` を使用する
  - 難易度が高いタスクは `codex` に委譲、もしくは `opus` を使用する
- 全ての実装タスクを委譲する
- `test`, `lint` などの標準出力に大量に出力するタスクは `haiku` に委譲しサマリのみを受け取る
- アーキテクチャレビュー/セキュリティレビュー/コードレビューは必ず実装者とは別のエージェントに委譲する

## Suggested Tools

- Use `rg` instead of `grep` for filtering command output in Bash.
  - パイプの受け手として使う場合は `cmd | rg 'PATTERN' -` のように `-` で stdin を明示する。
  - ファイル検索として使う場合は `rg -n 'PATTERN' src/` のように対象パスを明示する。
  - 読み取り範囲を省略したコマンド (`rg 'PATTERN'`, `grep -r 'PATTERN'`, 引数なしの `ls`) は cwd 全体を読むと解析され、`Read(.env)` などの deny rule によって承認プロンプトが要求されるため回避する。
  - パイプの受け手の `grep` は stdin のみと解析されるので中断しない。`rg` は再帰検索がデフォルトのため `-` が必要になる。
- `.gitignore` を自動的に除外する高速な `fd` コマンドを `find` の代わりに使う。

## Markdown 文章スタイル

- 文内にむやみに改行を入れない。1 行（1文）は長くなってもいいので、句点を基準にして改行すること。
  - `.markdownlint-cli2.jsonc` / `.rumdl.toml` で `MD013` (行長制限) を無効化する。
- 強調 `**` などのレンダリングが崩れるので、意味単位での改行 (semantic line breaks) は使わない。
- 段落の区切りは空行で表現する (Markdown の通常の段落ルール)。
- 箇条書きの 1 項目内でも改行しない。複数文に分けたい場合は項目自体を分割する。
- レンダリング崩れを防ぐため、強調記号 `**...**` を改行や空行で分断したり、`**` の内側に空白を入れたりしない。
