# AGENTS.md

This profile is applied to user's global setting.
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

- コード検索、関連ファイルの特定、既存実装と影響範囲の調査は `cheap-researcher` に委譲する。
- 全ての実装タスクは `implementor` に委譲する。
- `test`、`lint`、`build` など標準出力が長くなるコマンドの実行と要約は `output-summarizer` に委譲する。
- アーキテクチャレビューは `architecture-reviewer`、コードレビューは `code-reviewer`、セキュリティレビューは `security-reviewer` に委譲し、必ず実装者とは別のエージェントを使う。

## Markdown 文章スタイル

- 文内にむやみに改行を入れない。1 行（1文）は長くなってもいいので、句点を基準にして改行すること。
  - `.markdownlint-cli2.jsonc` / `.rumdl.toml` で `MD013` (行長制限) を無効化する。
- 強調 `**` などのレンダリングが崩れるので、意味単位での改行 (semantic line breaks) は使わない。
- 段落の区切りは空行で表現する (Markdown の通常の段落ルール)。
- 箇条書きの 1 項目内でも改行しない。複数文に分けたい場合は項目自体を分割する。
- レンダリング崩れを防ぐため、強調記号 `**...**` を改行や空行で分断したり、`**` の内側に空白を入れたりしない。

## Restrictions

- No sensitive data should be hardcoded in the source code.
- Follow the principle of least privilege when accessing resources.
- Avoid using deprecated libraries or tools.
