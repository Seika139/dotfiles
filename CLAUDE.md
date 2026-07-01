# Claude Instructions for this Profile

This profile is applied to user's global setting.
Use Japanese for communication.

## Environment-Specific Notes

This machine is ubuntu with 8GB RAM. I have a separate development machine that uses a Mac book with 32GB RAM. This Ubuntu is on a VPS, so you can take advantage of the fact that you can work from anywhere 24 hours a day, and while you handle what is possible with Ubuntu's specs, consider having a Mac book perform heavy processing as needed.

## Main Session Policy

- メインセッションは以下の対応に専念する。実装はサブエージェントに委譲する
  - 開発ワークフローの設計と管理
    - Default Workflow: `plan` -> `architecture design` -> `architecture review` -> `implement` -> `code/security review`
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
  - 基本は `sonnet` を使用する
  - 難易度が高いタスクは `codex` に委譲、もしくは `opus` を使用する
- 全ての実装タスクを委譲する
- `test`, `lint` などの標準出力に大量に出力するタスクは `haiku` に委譲しサマリのみを受け取る
- アーキテクチャレビュー/セキュリティレビュー/コードレビューは必ず実装者とは別のエージェントに委譲する

## Suggested Tools

- Use `rg` instead of `grep` for filtering command output in Bash.
- Use `fd` instead of `find` for file searching.

## 推論スタイル

- **deprecated な CLI コマンド・設定キーをユーザーに案内しない**。現行の方法を確認してから推奨する。
  - 理由: 過去のドキュメントに残った旧機能 (例: `/output-style` スラッシュコマンド) を勧めると、ユーザーの環境で実行できず混乱を招く。
  - 対処: `/help` 出力・プラグインの README・現行の settings スキーマで現在のインターフェースを確認する。
- **観測した個別現象に飛びついて診断を続けない**。ユーザーが本当に解決したい問題を 1 度言葉で確認する。
  - 理由: 提示されたサンプルの**ある側面**(例: Markdown の `**強調**` 崩れ)に注目したまま、ユーザーの本来の論点(例: 段落内の改行が多い)を取り違えて長時間続行する事故が起きやすい。
  - 対処: 最初のサンプルが提示された段階で「直したいのは X ですか、それとも Y ですか？」と簡潔に確認する。
- **`2>/dev/null` で stderr を隠したまま再試行を繰り返さない**。
  - 理由: ファイルやディレクトリの不在を確かめるつもりで `ls foo 2>/dev/null` を打つと、`No such file` というまさに必要な情報が捨てられる。同じ場所を別フラグで叩き続けるループに入りやすい。
  - 対処: 存在確認は `ls -la <path> 2>&1` か `[ -e <path> ] && ...` に切り替え、不在が確定したら別パスを試す前にユーザーに尋ねる。1 回失敗したら次の Bash の前に観察結果を 1 行で言語化する。

## Markdown 文章スタイル

Markdown ファイルを書き込む際は以下を守る。チャット応答にも同じ方針を適用する。

- **文内にむやみに改行を入れない**。1 行（1文）は長くなっても **1 行で書く**。句点を基準にして改行すること。意味単位での改行 (semantic line breaks) は使わない。
  - 理由: このリポは `.markdownlint-cli2.jsonc` / `.rumdl.toml` で `MD013` (行長制限) を無効化している。行長は自由なので、segments を 1 行に保った方が soft-wrap 表示・diff・強調記号 `**...**` の整合性すべてに有利。
  - ❌ 悪い例 (1 文を複数行に分割):

    ```markdown
    APM を採用。prompts / skills / commands を**ツール非依存の primitive** として
    扱い、deploy 時に各ツールのネイティブ配置先へ展開する。
    ```

  - ✅ 良い例 (段落 = 1 行):

    ```markdown
    APM を採用。prompts / skills / commands を**ツール非依存の primitive** として扱い、deploy 時に各ツールのネイティブ配置先へ展開する。
    ```

- 段落の区切りは **空行** で表現する (Markdown の通常の段落ルール)。
- 箇条書きの 1 項目内でも改行しない。複数文に分けたい場合は項目自体を分割する。
- 強調記号 `**...**` を改行や空行で分断しない。`**` の内側に空白を入れない (`** 強調 **` は強調として認識されない)。
