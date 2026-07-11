# agent-team パッケージの consumer 手順

`Caromaf/agent-package-basic/packages/agent-team` を Claude Code の user scope (`~/.claude/agents/`) に配布するための手順。
このパッケージは **Orchestrator / Implementor / OutputSummarizer** の 3 サブエージェントを APM `agents` primitive で配信する。

最終更新: 2026-07-10 (dependency object form による Claude 専用 target 制限へ移行)

---

## 前提と設計判断

### 1. agent-team は Claude Code 専用である

agent-team の各 agent は `EnterWorktree` / `EnterPlanMode` / `Agent(type)` などの Claude Code 固有機能に依存する。
同じ定義を Codex や Copilot 向けに変換すると、Claude 固有の本文は残る一方で frontmatter の `model` / `effort` / `tools` / `memory` は Codex agent の設定として保持されないため、正しい実行契約にならない。

APM の dependency object form で `targets: [claude]` を指定し、profile 全体では複数 target を有効にしたまま agent-team だけを Claude に限定する。
APM が実際に配布する範囲は profile の有効 target と dependency の `targets` の積集合になるため、agent-team は `~/.claude/agents/*.md` にのみ配布され、`~/.codex/agents/*.toml` や `~/.copilot/agents/*.agent.md` には配布されない。

### 2. Orchestrator はメインスレッド起動する

```bash
claude --agent Orchestrator
```

サブエージェントとして (`Agent(Orchestrator)`) 呼ぶと `EnterWorktree` / `EnterPlanMode` / `Agent(type)` 制限が無効化されるため、必ず `--agent` でメインスレッド起動する。
詳細は `Caromaf/agent-package-basic/packages/agent-team/.apm/agents/orchestrator.md` の先頭コメントを参照する。

### 3. Implementor は Orchestrator の worktree を共有する

Implementor に `isolation: worktree` は付けていない。
別 worktree にすると Implementor の commit が Orchestrator の作業ブランチへ自動で取り込まれず、重量級モノレポでは依存再構築のコストも増えるため、Orchestrator の worktree を共有して逐次実行する。
詳細は `implementor.md` の先頭コメントを参照する。

---

## profile 設定

公開 profile の `dependencies.apm` に次の object form を置く。
private overlay には追加しない。

```yaml
- git: Caromaf/agent-package-basic
  path: packages/agent-team
  ref: main
  targets: [claude]
```

対象 profile は `cg-m2-mac` / `hm-m1-mac` / `win-15034` / `wsl-ubuntu` / `xsv-linux-1`。
他の共有 package は従来どおり profile 全体の target へ配布される。

## lock 更新と deploy

string form から object form へ変更した直後は既存の `apm.lock.yaml` が古いため、対象マシンで `mise run update` を実行して lock を再生成し、user scope を再 deploy する。

```bash
cd ~/dotfiles/agents
mise run update
```

通常運用では `mise run install` (`--frozen`) を使用し、manifest の変更や ref 更新時だけ `mise run update` を使用する。

## 確認

```bash
mise run status
ls ~/.claude/agents/
test ! -e ~/.codex/agents/implementor.toml
test ! -e ~/.codex/agents/orchestrator.toml
test ! -e ~/.codex/agents/output-summarizer.toml
test ! -e ~/.copilot/agents/implementor.agent.md
test ! -e ~/.copilot/agents/orchestrator.agent.md
test ! -e ~/.copilot/agents/output-summarizer.agent.md
claude --agent Orchestrator
```

`~/.claude/agents/` には `implementor.md` / `orchestrator.md` / `output-summarizer.md` が存在し、過去の全 target 配布で生成された同名ファイルは Codex / Copilot 側に存在しないことを確認する。

## 旧配布ファイルの cleanup

`mise run update` 後も過去に生成されたファイルが Codex / Copilot 側へ残っている場合は、内容とファイル名を確認したうえで agent-team 由来の次の 6 ファイルだけを削除する。

```bash
rm ~/.codex/agents/implementor.toml
rm ~/.codex/agents/orchestrator.toml
rm ~/.codex/agents/output-summarizer.toml
rm ~/.copilot/agents/implementor.agent.md
rm ~/.copilot/agents/orchestrator.agent.md
rm ~/.copilot/agents/output-summarizer.agent.md
```

ディレクトリ全体は削除しない。他の package や手動管理の agent が同居している可能性がある。

## uninstall

全公開 profile の `apm.yml` から agent-team の object entry を削除し、`mise run update` で lock と user scope を更新する。
更新後も `~/.claude/agents/` に上記 3 ファイルが残る場合は、内容を確認して agent-team 由来のファイルだけを削除する。
