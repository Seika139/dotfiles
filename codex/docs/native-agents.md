# Native Codex agents

この package の `agents/*.toml` が Codex の native agent 定義です。Codex の agent loader が symlink を確実に発見できないため、各 TOML は `~/.codex/agents/<name>.toml` に通常ファイルとして反映します。配備済みファイル名は `~/.codex/.codex-dotfiles-native-agents.manifest` で管理し、別の管理元が置いた agent は残します。

メインセッションの `AGENTS.md` がオーケストレーターです。実装には `implementor`、長いテスト出力の要約には `output-summarizer`、設計・コード・セキュリティの確認には各 reviewer を選択して委譲します。reviewer は読み取り専用です。各 profile の `max_threads = 4` と `max_depth = 1` は過剰な並列実行と再帰を防ぎます。

この package は APM の agent integration を使いません。APM の共通 agent Markdown を最小限の Codex TOML に変換するだけでは、Codex native の `model`、`model_reasoning_effort`、sandbox/approval semantics を忠実に保持できません。また `Agent(...)`、`EnterWorktree`、Claude 固有の tool 指示は portable ではありません。そのため Codex 用の名前、モデル、推論強度、developer instructions をここで明示管理します。

定義を更新したら `mise run check --prof <profile>` で検証し、必要な環境への反映は `mise run link --prof <profile>` で行います。初回に同名の通常ファイルがある場合は `.backup.YYYYMMDD_HHMMSS` として退避し、以後はマニフェストに記録された package 管理ファイルだけを安全に更新します。配備は一時ファイルへのコピー後に atomic rename するため、コピーに失敗しても既存ファイルを保持します。マニフェストに記録された旧ファイルだけが stale cleanup の対象で、未管理の通常ファイル・symlink・agent は保持します。
