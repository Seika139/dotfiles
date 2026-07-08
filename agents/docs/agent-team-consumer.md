# agent-team パッケージの consumer 手順

`Caromaf/agent-package-basic/packages/agent-team` を user scope (`~/.claude/agents/`) に配布するための手順。
このパッケージは **Orchestrator / Implementor / OutputSummarizer** の 3 サブエージェントを APM `agents` primitive で配信する。

最終更新: 2026-07-08 (全 profile 追記 + mise run update フローに全面改訂。実配布・動作確認済み)

---

## 前提と設計判断

### 1. これは Claude Code 前提のパッケージである

agent-team の各 agent は Claude Code 固有機能に依存する:

- `EnterWorktree` / `EnterPlanMode` / `Agent(type)` の種類 allowlist (いずれもメインスレッド起動時のみ有効)

APM は `agents` primitive を **claude 以外のターゲットにも展開する**。実配布で確認した展開先:

- `~/.claude/agents/*.md` (frontmatter 付き markdown, これが本命)
- `~/.codex/agents/*.toml` (Codex 用に toml へ変換される)
- `~/.gemini/agents/` は生成されない (Gemini は agents 未対応)

他ツール (Codex 等) に定義ファイルが置かれても、agents は `claude --agent` で明示起動しない限り動かないため実害はない。
skill のように自動発火して誤動作するリスクは agents には無い。この「他ターゲットに無害なファイルが増える」ことを
許容する代わりに、dotfiles の正規フロー (`mise run install` / `mise run update`) に一本化して恒久性を得る方針を採る。

### 2. Orchestrator はメインスレッド起動する

```bash
claude --agent Orchestrator
```

サブエージェントとして (`Agent(Orchestrator)`) 呼ぶと `EnterWorktree` / `EnterPlanMode` / `Agent(type)` 制限が
すべて無効化されるため、必ず `--agent` でメインスレッド起動すること。詳細は
`Caromaf/agent-package-basic/packages/agent-team/.apm/agents/orchestrator.md` の先頭コメント参照。

### 3. Implementor は逐次実行 (isolation: worktree を付けない)

Implementor に `isolation: worktree` は付けていない。別 worktree だと Implementor の commit が Orchestrator の
作業ブランチに取り込まれず成果が宙に浮くため、および重量級モノレポ (例: ligaius は `.venv` が 5.2GB) では
各 worktree の依存再構築コストが並列ゲインを食い潰すため。Orchestrator の worktree を共有して逐次実行する。
詳細は `implementor.md` の先頭コメント参照。

---

## install 手順 (全 profile 追記 + mise run update)

profile の `targets` は全ツール (claude, codex, gemini, copilot, cursor) を含むため、agent-team も全ターゲットに
展開されるが、上記のとおり実害はない。マシン横断で使えるよう **全 profile (private を除く) の `apm.yml` に追記** する。

### 1. 全 profile に依存を追記

`profiles/<machine>/apm.yml` の `dependencies.apm:` 末尾 (basic パッケージ群の最後) に追記する:

```yaml
- Caromaf/agent-package-basic/packages/agent-team#main
```

対象: `cg-m2-mac` / `hm-m1-mac` / `win-15034` / `wsl-ubuntu` / `xsv-linux-1` (private overlay には入れない)。

### 2. lock を再生成して deploy

apm.yml に新パッケージを足した直後は `apm.lock.yaml` が古いため、`mise run install` (`--frozen`) は
「declared in apm.yml but missing from apm.lock.yaml」で失敗する。**`mise run update` で lock を再生成する**:

```bash
cd ~/dotfiles/agents && mise run update
```

`mise run update` は `apm install -g --refresh --force` を実行し、全依存を最新 ref に再解決 + user scope に再 deploy し、
生成した lock を profile (private overlay 有効時は `profiles/private/apm.lock.yaml`) にコピーバックする。

> 以降、apm.yml を変更していない通常運用では `mise run install` (`--frozen`) で足りる。
> 新パッケージ追加や ref 更新をした時だけ `mise run update` を使う。

---

## 確認

```bash
ls ~/.claude/agents/
# implementor.md / orchestrator.md / output-summarizer.md が並ぶ

claude --agent Orchestrator   # メインスレッド起動して動作確認
```

サブエージェントとしての疎通だけ確認したい場合は、別セッションで OutputSummarizer に無害なコマンドを要約させる
(例: `apm --version` の要約) と、定義ロード〜起動〜応答の経路を軽量に検証できる。

---

## uninstall

全 profile の `apm.yml` から `agent-team#main` の行を削除し、`mise run update` で再 deploy する
(lock からも外れ、`~/.claude/agents/` の 3 ファイルも次回同期で削除される)。
