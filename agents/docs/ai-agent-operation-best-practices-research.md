# 生成AIを使ったコード運用のベストプラクティス調査

## 調査の目的

生成AIによるコード変更を、(1) 恒常的なバグ修正、(2) 開発時のコード発散抑制、(3) 既存コードベースの収束、の3ケースに分けて運用する方針が妥当かを、Anthropic と OpenAI の公式資料で確認する。

調査日は 2026-09-11。ここでは Anthropic と OpenAI の一次資料から直接読み取れる内容と、それを今回の運用方針へ適用する際の推論を分けて記載する。

## 結論

「常時適用する発散抑制ルール1つ + 明示的に起動するバグ修正 Skill 1つ + 明示的に起動するコード収束 Skill 1つ」という構成は、Anthropic と OpenAI の公式資料が示す責務分担と整合する。ただし、常時ルールは全セッションに必要な短い原則だけに限定し、ケース固有の手順・詳細な知識・大規模移行の作業計画は Skill や参照ファイルへ分離する。必ず実行したい機械判定可能な検査は Markdown 指示だけに頼らず、hook・lint・test・build などの決定的な仕組みに接続する。

この結論は、Anthropic と OpenAI が、それぞれ `CLAUDE.md` / `AGENTS.md` を広く適用する短い指示の置き場、Skills を必要時に読み込む再利用可能なワークフローの置き場、hooks や既存の検査を決定的な仕組みとして説明していることから導く推論である。

## 公式資料から確認できること

### 常時ルールは短く、広く適用する内容に限定する

Anthropic の Claude Code 公式ベストプラクティスは、`CLAUDE.md` を会話開始時に読み込む永続コンテキストとして位置付け、コマンド、コードスタイル、ワークフロールールを置くよう説明している。同時に、毎回適用されるため短く人間が読める形に保ち、広く適用される内容だけを含め、たまにしか使わないドメイン知識やワークフローは Skill に移すよう勧めている。`CLAUDE.md` に書く各行について「削除したら誤りが増えるか」を問い、そうでなければ削るという基準も示している。

出典: [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices#write-an-effective-claudemd) の「Write an effective CLAUDE.md」節（特に行 184-210）。

同じページは、長すぎる `CLAUDE.md` では重要な指示がノイズに埋もれ、モデルが無視しやすくなると説明し、コードから自明に分かる内容や長いチュートリアルは除外対象としている。また、既に正しくできていることを指示に残さず、必要なら hook に変換するよう案内している。

出典: [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices#avoid-common-failure-patterns) の「The over-specified CLAUDE.md」節。

### Skill は再利用可能なワークフローとして分離し、手動起動を選べる

Anthropic の公式ベストプラクティスは、`.claude/skills/` に `SKILL.md` を置いて、プロジェクト・チーム・ドメイン固有の知識や再利用可能なワークフローを与えられると説明している。Skill は関連時に自動適用でき、`/skill-name` で直接起動もできる。副作用のあるワークフローを明示起動だけに限定したい場合は、frontmatter に `disable-model-invocation: true` を指定する例が示されている。

出典: [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices#create-skills) の「Create skills」節（特に行 252-289）。

このため、バグ修正とコード収束を専用 Skill として分け、ユーザーが意図したときだけ起動する設計は公式の利用モデルに適合する。特にコードベース全体へ影響し得る収束作業は、手動起動と対象範囲の引数を要求する設計が適切である。後半は公式仕様からの適用上の推論である。

### Skill は progressive disclosure と composability を前提にする

Anthropic の Agent Skills 公式記事は、Skill の `SKILL.md` frontmatter にある `name` と `description` が起動時に読み込まれ、関連性を判断した後に本文を読み込む二段階構成を説明している。詳細が大きい場合は、参照資料やスクリプトを Skill ディレクトリに置き、必要時だけ読み込む第三段階以降へ分離できる。記事はこの progressive disclosure を Skills の中核設計原則とし、Skills が composable resources として組み合わせて使えることも説明している。

出典: [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) の「The anatomy of a skill」および「Progressive disclosure」節。

したがって、専用 Skill 本文には起動条件、入力、判断基準、終了条件、検証の接続だけを置き、`diagnosing-bugs`、`ponytail-audit`、レビュー手順などの詳細を無制限に複製しない構成がよい。既存 Skill を組み合わせる方針は composability に沿う。後半は公式の原則を今回の Skill 構成へ適用した推論である。

### 変更は探索・計画・実装・検証を分け、成功判定を外部化する

Claude Code の公式ベストプラクティスは、複数ファイルの変更や不確実な作業では「Explore → Plan → Implement → Commit」の4段階を推奨し、スコープが明確で小さい変更は計画を省略してよいと説明している。探索時は具体的なファイル、症状、制約、期待する修正、テスト条件を指定する例が示されている。

出典: [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices#explore-first-then-plan-then-code) の「Explore first, then plan, then code」節および「Provide specific context in your prompts」節。

同ページは、テスト、build、lint、fixture との差分、スクリーンショットなど、Claude が読める pass/fail の検査を与えると、作業・検証・修正のループを自律化できると説明している。完了時には実行コマンドと結果などの証拠を示させるよう勧めている。例外なく毎回実行したい処理には hook を使い、`CLAUDE.md` の指示は advisory、hook は deterministic と明確に区別している。

出典: [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices#give-claude-a-way-to-verify-its-work) の「Give Claude a way to verify its work」節および「Set up hooks」節。

このため、バグ修正 Skill の終了条件は「原因の説明」だけでなく、再現テストまたは同等の再現可能な検査が修正前に失敗し、修正後に成功し、関連回帰検証も成功したことにする。開発時の発散抑制ルールに含めるべき内容は「検証を実行し証拠を示す」という原則までとし、個別コマンドはプロジェクト固有の `CLAUDE.md`、Skill、hook、CI へ委ねる。後半は公式の検証原則からの推論である。

### 独立したレビューと調査の委譲で、実装者の偏りとコンテキスト消費を抑える

Anthropic の公式ベストプラクティスは、調査を subagent の別コンテキストへ委譲すると、メイン会話をファイル探索の出力で埋めずに済むと説明している。また、完了前に新しいコンテキストの subagent に diff をレビューさせ、要件の抜けを報告させる adversarial review を推奨している。レビュー条件には、要件の実装、エッジケースのテスト、スコープ外変更がないことを含める例がある。一方で、レビューは「欠陥を探す」よう指示すると過剰な finding を返し得るため、正しさや要求に影響する gaps に限定し、スタイル上の好みは追わないよう注意している。

出典: [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices#use-subagents-for-investigation) の「Use subagents for investigation」節および [同ページの「Add an adversarial review step」節](https://code.claude.com/docs/en/best-practices#add-an-adversarial-review-step)。

公式資料は変更規模に応じて計画・検証・独立レビューを使い分ける手順を示しているが、今回の運用では既存 `AGENTS.md` の委譲・独立レビュー方針を維持し、各担当の範囲を必要十分に絞る。レビューの finding は正しさ・要求・スコープに限定する。後半は公式の手順を既存方針へ適用した推論である。

### 大規模移行は小さく試し、結果を見てから広げる

Claude Code の公式ベストプラクティスは、大規模な移行・分析を複数の Claude セッションへ分散できると説明している。ファイル一覧を作成し、最初の 2〜3 ファイルで試し、問題からプロンプトを改善してから全体へ広げる手順が示されている。非対話実行や一括処理では権限を `--allowedTools` で絞ることも勧めている。

出典: [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices#fan-out-across-files) の「Fan out across files」節。

したがって、コード収束 Skill は、対象を列挙して目標状態を測定し、代表的な少数箇所で移行パターンと検証を確立し、その結果をレビューしてから全体へ反映し、最後に旧経路を撤去する段階構成がよい。これは、いきなり全コードベースへ自動変更を広げないための適用上の推論である。

### 指示や Skill の変更自体を評価対象にする

Anthropic の公式 eval 記事は、評価がないと変更後にエージェントの品質が悪化したかを区別できず、推測と手動確認に頼ることになると説明している。評価は初期段階では成功条件を具体化し、後段では一貫した品質基準を維持する。コーディングエージェントでは unit test による正しさ確認と LLM rubric によるコード品質評価が基本で、必要な場合だけ static analysis、state check、tool call、追加メトリクスを組み合わせる。初期の評価セットは実際の失敗から作った 20〜50 件の単純なタスクで始めるのがよいとされている。

出典: [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) の「Why build evaluations?」「Evaluating coding agents」および「How many evals do you need?」節。

さらに、Anthropic の Claude Code 品質報告は、システムプロンプト変更ごとに広いモデル別 eval を実行し、各行の影響を ablation で調べ、変更をレビュー・監査しやすくする tooling を追加し、知能とトレードオフする変更には soak period、広い eval、段階的 rollout を加える方針を示している。

出典: [An update on recent Claude Code quality reports](https://www.anthropic.com/engineering/april-23-postmortem) の「Going forward」節。

今回の方針への適用として、常時ルールと2つの Skill を導入した後は、代表的な依頼を記録した小さな行動評価セットを作り、要求外変更の抑制、適切な Skill の起動、バグ修正の再現・回帰検証、収束作業の旧経路撤去を確認するべきである。評価セットの件数や判定器は、実際の失敗履歴に基づいて増やす。後半は公式の eval 原則からの推論である。

## 3ケースへの適用

### 1. 恒常的なバグ修正

専用 Skill は、症状・期待動作・再現条件・対象範囲を入力として受け取り、探索、再現テストまたは検査、根本原因の特定、必要十分な修正、回帰検証、独立レビュー、証拠付き完了報告を定義する。今回は両 Skill とも自動起動を無効にし、ユーザーの明示起動に限定する `disable-model-invocation: true` と Codex の `policy.allow_implicit_invocation: false` を採用するのが妥当である。

常時ルールは、要求されたバグの修正に必要な範囲を守ること、既存パターンを先に調べること、完了条件と検証結果を示すことを短く指示する。診断、監査、コードレビューなど既存 Skill の本文を複製せず、専用 Skill から必要なものを呼び出す。

### 2. 開発時のコード発散抑制

これは全セッションで読む `AGENTS.md` / `CLAUDE.md` に置く。内容は「要求と対象範囲を先に確認する」「既存の責務・パターン・依存を調べて再利用する」「新しい抽象化・依存・設定は具体的な必要がある場合だけ追加する」「無関係な変更を広げない」「検証可能な証拠を残す」といった、どの開発にも適用される短い原則に限定する。

「毎回必ず実行する検査」や「違反時に停止する制約」は、常時 Markdown ルールだけで保証しない。Anthropic の説明に従い、機械的に判定できるものは hook、lint、test、CI へ移す。プロジェクト別コマンドや設計不変条件は、各プロジェクトの指示ファイルや検査スクリプトで定義する。

### 3. 既存コードベースの収束

専用 Skill は、現状の計測、目標状態、移行単位、互換性とリスク、代表例での試行、段階的な反映、旧経路の撤去、最終計測と独立レビューを管理する。変更範囲が広いので、探索と計画を実装から分離し、対象一覧と完了条件をファイルなどの永続的な成果物にする。

Anthropic の大規模移行手順に合わせ、少数ファイルで移行方法を検証してから全体へ広げる。全体反映後は、新旧経路が併存したまま終わらないよう、旧実装・旧利用箇所・一時的な互換コードの撤去を終了条件に含める。最後の撤去条件は今回の「収束」の定義に基づく推論である。

## 実装時の判断

1. 常時ルールは1つにまとめる方針でよい。ただし、短い原則を超える詳細を詰め込まず、`CLAUDE.md` / `AGENTS.md` の長さと実際の遵守状況を定期的に見直す。
2. バグ修正 Skill とコード収束 Skill を分ける方針でよい。前者は限定された症状に対する再現・原因・回帰を中心にし、後者は目標状態・移行計画・撤去完了を中心にする。
3. 2つの専用 Skill は今回はともに明示起動だけにし、自動起動を無効化する。Skill 間の共通手順は既存 Skill と検証コマンドへ委譲する。
4. 発散抑制を完全にプロンプトだけで実現しない。重要な検査や禁止事項は deterministic な仕組みに接続し、Skill の完了報告にはコマンド・結果・未解決点を残す。
5. 導入後は、実際の失敗例から小さな評価セットを作り、指示・Skill の変更前後で振る舞いを比較する。レビューは要求・正しさ・スコープの gaps に限定し、指摘を増やすこと自体を品質目標にしない。

6. 常時適用の最小化とコード収束は衝突させない。収束時の追加変更は、宣言済みの目標状態・対象範囲・完了条件に必要な場合だけ許容し、無関係な改善は別件へ分離する。
7. 長期の収束作業では、プロジェクト内に再開可能な living plan を置き、対象一覧、進捗、意思決定、検証結果、残作業を正本として更新する。

## OpenAI 公式資料との統合

OpenAI の Codex / ChatGPT 公式資料も、今回の構成を直接指定してはいないが、同じ責務分担を支持する。OpenAI の「Build skills」は、Skill を再利用可能なワークフローとして扱い、各 Skill を1つの仕事に絞り、明確な入力と出力を定義し、instruction-only をまず選び、説明文で起動範囲とトリガーを明確にするよう勧めている。Skills は progressive disclosure で名前・説明を先に読み、必要時に `SKILL.md` 本文を読み込む。Codex では `agents/openai.yaml` の `policy.allow_implicit_invocation: false` により暗黙起動を無効化し、明示起動だけにできる。

出典: [Build skills](https://learn.chatgpt.com/docs/build-skills) の「How ChatGPT and Codex use skills」「Best practices」節。

このため、バグ修正 Skill とコード収束 Skill を分け、前者は再現・原因・回帰、後者は現状計測・移行・撤去という1つの仕事に絞り、明示起動を設定する設計は OpenAI の原則にも適合する。3ケースという分類そのものは OpenAI や Anthropic が公式に定めたものではなく、目的と変更ライフサイクルを分ける今回の設計判断である。

OpenAI の Codex ベストプラクティスは、`AGENTS.md` を自動ロードされる永続的な guidance の置き場とし、Goal、Context、Constraints、Done when を明記すること、短く正確に保ち、長くなったらタスク固有の Markdown や Skill へ分離することを勧めている。テスト、lint、type check、最終挙動、diff review の確認も完了条件に含めるよう説明している。

出典: [Best practices](https://learn.chatgpt.com/guides/best-practices) の「Strong first use: Context and prompts」「Make guidance reusable with `AGENTS.md`」「Improve reliability with testing and review」節。

したがって、常時の発散抑制ルールには全開発に共通する制約と Done の原則だけを置き、バグ修正・収束の具体的手順は専用 Skill に置くという分割が適切である。自動ロードは遵守保証を意味しないため、機械的に検査できる不変条件は既存の test、lint、CI 等へ接続する。後半は公式の guidance と検証の役割からの推論である。

OpenAI の Skill eval 公式記事は、Skill の改善を感覚で判断せず、成功を測定可能に定義してから、実行 trace と成果物を保存し、決定的な checks と rubric で評価する方法を示している。評価軸は outcome、process、style、efficiency に分けるが、必須条件を小さく絞る。最初は単一 Skill につき 10〜20 個程度の代表プロンプトから始め、実際の失敗を追加していく方法が示されている。

出典: [Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills) の「Define success before you write the skill」および「Use a small, targeted prompt set to catch regressions early」節。

今回の導入では、最初から巨大な評価器や新しい hook を必須にせず、3ケースそれぞれの代表タスクを少数用意し、Skill が起動したか、必要な調査・検証を行ったか、スコープ外変更を避けたか、成果物と証拠を残したかを確認するのが妥当である。評価を大きくするのは実際の失敗が現れてからでよい。これは OpenAI の小さな targeted prompt set と Anthropic の実失敗起点の評価方針を統合した推論である。

OpenAI の Exec Plans 公式ガイドは、複数時間に及ぶ作業では living plan を使い、進捗、意思決定、検証結果を継続的に記録する運用を説明している。コード収束のような長期作業では、対象一覧、目標状態、移行単位、各 milestone の独立検証、旧実装を撤去する最後の手順を計画に残す設計が合う。

出典: [Using PLANS.md for multi-hour problem solving](https://learn.chatgpt.com/cookbook/articles/codex_exec_plans)。

## 統合後の採用方針

- 常時適用: `AGENTS.md` / `CLAUDE.md` に、短く具体的な Goal・Constraints・Done の原則と発散抑制ルールを置く。全セッションに必要な内容だけを残し、長い説明やケース固有の手順は置かない。
- 明示起動: バグ修正 Skill とコード収束 Skill は1 Skill 1 job とし、`SKILL.md` に入力、出力、トリガー、終了条件、検証を記載する。Claude では `disable-model-invocation: true`、Codex では `allow_implicit_invocation: false` を使い、両 Skill とも明示起動に限定する。
- 検証: Skill の終了条件には、テストや lint などの結果、変更差分、未解決点を含める。絶対に守る機械的条件は Markdown の指示だけでなく、既存の test・lint・CI 等へ接続する。
- 収束: 大規模移行は計画と living plan を使い、少数の代表箇所で試し、独立検証してから段階的に広げる。移行中だけ必要な互換コードを許容し、完了時には旧経路の撤去を確認する。
- 評価: 導入後は代表タスクの小さな prompt set を作り、起動・手順・成果物・スコープ・検証証拠を評価する。LOC 削減や固定ファイル数など、公式資料にない数値を一般的な成功条件にしない。
- 配布: Codex の `agents/openai.yaml` と Claude の Skill frontmatter は別の設定面として扱い、各環境への配布後に、明示起動・自動起動・ロード結果を個別に確認する。本文と生成器を必ず分離する設計や、初回から新しい hook・巨大な評価器を導入することは必須にしない。

## 参照した公式資料

- [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices)
- [Skills](https://code.claude.com/docs/en/skills)
- [How Claude remembers your project](https://code.claude.com/docs/en/memory)
- [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [An update on recent Claude Code quality reports](https://www.anthropic.com/engineering/april-23-postmortem)
- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Best practices](https://learn.chatgpt.com/guides/best-practices)
- [Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills)
- [Using PLANS.md for multi-hour problem solving](https://learn.chatgpt.com/cookbook/articles/codex_exec_plans)

## 元会話の再精査（2026-09-11）

元会話全7往復を再確認した。前半で出た LOC の負数化、3ファイル・20行制限、single caller の抽象化禁止、縮小だけを評価する Critic は、今回の運用標準には採用しない。これらは対象・言語・設計目標に依存する局所的なヒューリスティックであり、正しさや必要な構造変更を阻害し得るためである。

後半で整理された「正しさ > 保存 > 最小化」の優先順位、global methodology と project contract の分離、目標状態を定義した段階移行・旧経路撤去・機械的 enforcement は採用する。ここでの最小化は、要求と目標状態を満たした後に無関係な変更を加えないという意味であり、収束に必要な移行や撤去を禁止する意味ではない。

実装前に、次の契約を専用 Skill の終了条件へ落とし込む必要がある。

- 未検査を pass や問題なしとして扱わず、未実施・未確認・対象外を区別する。
- 違反数の合計だけで判定せず、新たに追加された違反の集合を不合格条件にする。
- 外部 API、動的参照、設定経由の利用、生成物などを調査せずに旧実装を削除可と判定しない。
- project contract がなければ、既存 docs・CI・テスト・実装パターンから根拠付きで抽出し、重大な不明点は質問または保留にする。
- 緊急回避と根治を区別し、bugfix では再現用テストや最小限の再現用編集を許容する一方、無関係な整理を混ぜない。
- 段階ごとの完了とコードベース全体の完了を区別し、移行途中の一時コードと最終撤去を記録する。
- 既存 Skill の依存・起動条件・副作用を確認し、依頼されていない Issue・PR・コミット・配布範囲を勝手に拡張しない。

これらは、常時の発散抑制ルールへ詳細手順を詰め込むためではなく、バグ修正 Skill とコード収束 Skill の入力・判断・終了条件、および project contract の検証項目へ接続するための実装前確認事項である。

## 実体確認に基づく未解決 preflight

実装前に、次の配布・依存関係を確認する必要がある。Skill の配置元は `source packages/*/.apm/skills/<name>/SKILL.md` と各 `apm.yml`、および root aggregator であり、active profile は `cg-m2-mac` である。`~/.codex/AGENTS.md` は `codex/profiles/cg-m2-mac/AGENTS.md`、Claude は `claude/profiles/cg-m2-mac/CLAUDE.md` の symlink で運用される。

profiles は GitHub の `Caromaf/agent-package-basic#main` 経由で更新されるため、ローカル編集だけでは APM 更新へ反映されない。mise の install/update は profile manifest を `~/.apm` へコピーして `apm install -g` を実行し lock を戻す。`update --refresh --force` は他依存も更新し得るため、実装時は対象範囲を確認する。root aggregator への追加に profile 個別の新規依存は不要と見込まれるが、lock 更新の要否を確認する。

現状、`diagnosing-bugs` と `ponytail-audit` は basic 内に存在せず profile ごとに依存差があるが、`diagnosing-bugs` は `~/.apm/apm.lock.yaml` に記録された `mattpocock/skills#main` からの推移依存として実配布されている。既存 `ponytail` の強い常時適用と新しい発散抑制ルールが重複する可能性があるため、既存の起動条件・副作用・配布実体を確認してから最小変更を決める。未解決の配布確認を理由に自動互換層や無期限の保留を追加せず、重大な不明点だけを実装前に解消する。

codex / claude は各5 profileで環境差があるため、共通原則だけを追加し、全 profile の全文を一律統一しない。5通常 profile すべてで `mattpocock/skills` 依存があり、`~/.agents/skills/diagnosing-bugs/agents/openai.yaml` と Claude 側の対応も実在し、既存配備では interface metadata が保持されている。ただし、今回新規に追加する `policy.allow_implicit_invocation: false` の動作は未検証のため、隔離 fixture を使った実配布テストが必要である。現 mise には未公開 local repo をそのまま global 配布する経路がなく、bundle 方法の global 配布可否も未検証である。
