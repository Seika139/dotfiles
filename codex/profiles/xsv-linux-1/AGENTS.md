# AGENTS.md

Use Japanese for communication.

## Main Session Policy

- メインセッションは以下の対応に専念する。実装はサブエージェントに委譲する
  - 開発ワークフローの設計と管理
    - Default Workflow: `plan` -> `architecture design` -> `codex architecture review` -> `implement` -> `codex code/security review`
- ソフトウェアの全体設計
- 知識の再利用設計と管理
  - 全ての開発で再利用可能な知識は MEMORY に保存する
  - 特定のプロジェクトで再利用が必要な知識はプロジェクトの `CLAUDE.md` に保存する
  - 特定箇所で再利用が必要な知識は `.claude/rules` に保存する
  - 再利用可能なワークフローは `skill` として保存する
- タスクの進捗単位での git 操作の管理
- 適切なタスク分割とサブエージェントへの委譲

## Sub-agent Delegation Policy

- model/reasoningは担当するタスクの難易度に応じて選択する
  - 基本は `gpt-5.4` を使用する
  - 難易度が高いタスクは `gpt-5.6` または `gpt-5.5` に委譲する
- 全ての実装タスクを委譲する
- `test`, `lint` などの標準出力に大量に出力するタスクは `gpt-5.4-mini` に委譲しサマリのみを受け取る
- アーキテクチャレビュー/セキュリティレビュー/コードレビューは必ず実装者とは別のエージェントに委譲する

## Markdown 文章スタイル

- 文内にむやみに改行を入れない。1 行（1文）は長くなってもいいので、句点を基準にして改行すること。
  - `.markdownlint-cli2.jsonc` / `.rumdl.toml` で `MD013` (行長制限) を無効化する。
- 強調 `**` などのレンダリングが崩れるので、意味単位での改行 (semantic line breaks) は使わない。
- 段落の区切りは空行で表現する (Markdown の通常の段落ルール)。
- 箇条書きの 1 項目内でも改行しない。複数文に分けたい場合は項目自体を分割する。
- レンダリング崩れを防ぐため、強調記号 `**...**` を改行や空行で分断したり、`**` の内側に空白を入れたりしない。

## Environment-Specific Notes

This machine is ubuntu with 8GB RAM. I have a separate development machine that uses a Mac book with 32GB RAM. This Ubuntu is on a VPS, so you can take advantage of the fact that you can work from anywhere 24 hours a day, and while you handle what is possible with Ubuntu's specs, consider having a Mac book perform heavy processing as needed.

## Restrictions

- No sensitive data should be hardcoded in the source code.
- Follow the principle of least privilege when accessing resources.
- Avoid using deprecated libraries or tools.
