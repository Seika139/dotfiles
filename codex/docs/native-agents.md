# Native Codex agents

この package の `agents/*.toml` が Codex の native agent 定義です。Codex の agent loader が symlink を確実に発見できないため、各 TOML は `~/.codex/agents/<name>.toml` に通常ファイルとして反映します。配備済みファイル名は `~/.codex/.codex-dotfiles-native-agents.manifest` で管理し、別の管理元が置いた agent は残します。

メインセッションの `AGENTS.md` がオーケストレーターです。agent はモデル名ではなく、次の役割名で選択します。

| 作業                                                     | agent                   |
| -------------------------------------------------------- | ----------------------- |
| コード検索、関連ファイルの特定、既存実装と影響範囲の調査 | `cheap-researcher`      |
| 実装と必要なテスト                                       | `implementor`           |
| 長い `test`、`lint`、`build` 出力の実行と要約            | `output-summarizer`     |
| アーキテクチャレビュー                                   | `architecture-reviewer` |
| コードレビュー                                           | `code-reviewer`         |
| セキュリティレビュー                                     | `security-reviewer`     |

調査担当と reviewer は読み取り専用です。`sandbox_mode = "read-only"` は filesystem の強制境界ですが、agent ごとの network 強制設定はサポートを確認できていないため、`cheap-researcher` の instructions で外部ネットワークと workspace 外の情報源へのアクセスを禁止します。各 profile の `max_threads = 4` と `max_depth = 1` は過剰な並列実行と再帰を防ぎます。

この package は APM の agent integration を使いません。APM の共通 agent Markdown を最小限の Codex TOML に変換するだけでは、Codex native の `model`、`model_reasoning_effort`、sandbox/approval semantics を忠実に保持できません。また `Agent(...)`、`EnterWorktree`、Claude 固有の tool 指示は portable ではありません。そのため Codex 用の名前、モデル、推論強度、developer instructions をここで明示管理します。

agent TOML の `model` と `model_reasoning_effort` は実行時への要求値であり、実際に選択されたモデルの保証ではありません。軽量モデルの利用を受入条件とする rollout では、対象の同一 child session の JSONL に記録された `turn_context.model` を一次情報として requested model と observed model を照合します。`ccusage` は複数セッションをまとめる補助的な利用量集計として使い、通常タスクごとの確認は要求しません。

定義を更新したら、`mise run check --prof <profile>` で source を検証し、`mise run link --prof <profile>` で必要な環境へ反映し、`mise run status --prof <profile>` で managed match、managed drift、unmanaged collision、missing を診断します。その後、モデル選択が受入条件となる rollout だけ runtime acceptance として child session JSONL を確認します。

初回に同名の通常ファイルがある場合は `.backup.YYYYMMDD_HHMMSS` として退避し、以後はマニフェストに記録された package 管理ファイルだけを安全に更新します。`~/.codex/agents` 自体が symlink に置き換わっていた場合はリンク先を追跡せず、symlink を sibling backup へ退避して実 directory を再作成します。管理対象の agent が directory や symlink など通常ファイル以外に置き換わっていた場合も、異常な target をバックアップして通常ファイルへ修復します。配備は一時ファイルへのコピー後に atomic rename するため、コピーに失敗しても既存ファイルを保持します。マニフェストに記録された旧ファイルだけが stale cleanup の対象で、未管理の通常ファイル・symlink・agent は保持します。
