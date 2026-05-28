# APM instructions primitive の落とし穴と作法

skills と違い `instructions` primitive は **命名・frontmatter・配備モデルが厳格**で、
踏むと silent に配備失敗する。`commit-message` package の実装で踏んだ罠と正解を記録する。

最終更新: 2026-05-28

---

## 1. 結論 (TL;DR)

instructions package を作るときは必ず以下を守る:

1. ファイル名は **`<name>.instructions.md`** (`.instructions.md` suffix 必須)
2. frontmatter に **`description` (必須) + `applyTo` (必須)** を書く
3. push 前に **`apm compile --validate`** で `N instructions` が認識されることを確認
4. Claude/Cursor 等は file 配備されるが、**Codex/Gemini は `apm compile` 必須** (install では配備されない)

---

## 2. 踏んだ罠 (commit-message package, 2026-05-28)

### 症状

`commit-message#main` を apm.yml に追加して `apm install -g` しても
`~/.claude/rules/commit-message.md` が配備されなかった。エラーは一切出ない。

### 原因 1: ファイル名 suffix 欠落

```text
誤: packages/commit-message/.apm/instructions/commit-message.md
正: packages/commit-message/.apm/instructions/commit-message.instructions.md
```

APM は `.instructions.md` suffix で instruction primitive を識別する。suffix が無いと
**primitive として認識されず** (`apm compile --validate` が `0 instructions`)、
`apm install` の deployed_files がゼロになる。

### 原因 2: frontmatter に `description` 欠落

```markdown
---
description: 日本語コミットメッセージの記法ルール (...)   # ← 必須。欠けると認識されない
applyTo: "**"                                              # ← 必須。適用 glob
---
```

- `description`: 一行要約 (必須)
- `applyTo`: 適用する glob パターン (必須)。全ファイル対象なら `"**"`

### silent failure の罠

`apm install` は instruction が認識されなくても **エラーを出さず黙って配備ゼロ**になる。
lock の該当 package に `deployed_files:` が無ければ「認識失敗」のサイン:

```yaml
# 認識失敗 (deployed_files 無し)
- virtual_path: packages/commit-message
  content_hash: sha256:...
  # deployed_files が無い ← 配備されていない

# 認識成功 (deployed_files あり)
- virtual_path: packages/create-issue
  deployed_files:
  - .claude/skills/create-issue
```

---

## 3. 配備モデル (target 別、skills と大きく異なる)

| Target | instructions 配備先 | 機構 |
|---|---|---|
| **claude** | `~/.claude/rules/<n>.md` | `apm install` で file 配備。`applyTo` → `paths:` に自動変換 |
| **cursor** | `~/.cursor/rules/<n>.mdc` | `apm install`。`applyTo` → `globs:` 変換 |
| **copilot** | `.github/instructions/<n>.instructions.md` | ただし **user-scope では非対応** (install -g 出力で "copilot (prompts, instructions)" が non-supported) |
| **windsurf** | `~/.codeium/windsurf/...` | user-scope では instructions 非対応 |
| **codex** | `AGENTS.md` に統合 | **`apm compile` 必須** (install では配備されない) |
| **gemini** | `GEMINI.md` に統合 | **`apm compile` 必須** |
| **opencode** | `AGENTS.md` に統合 | `apm compile` 必須 |

### 重要な含意

- **skills は全 CLI に file 配布で枯れている**が、instructions は target で配備機構が割れる
- Claude/Cursor は file 配備 (install で OK)、Codex/Gemini は memory file への compile 統合

### ★ 配備決定: instructions は Claude 専用 (Codex/Gemini は非対応, 2026-05-28)

**commit-message instruction は Claude (`~/.claude/rules/`) のみに配備する。Codex/Gemini には配備しない。**
これはバグや配備漏れではなく **意図的な決定** (将来「Codex で効かない」と誤認して再調査しないこと)。

理由 (Codex/Gemini への instructions 配備を見送る根拠):

1. **`apm compile` に `-g`/`--global` が無い** — instructions の AGENTS.md 統合は project-local
   compile のみ。skills の `apm install -g` のような user-scope 配備ルートが存在しない。
2. **`~/.codex/AGENTS.md` / `~/.gemini/GEMINI.md` は link.sh の symlink → dotfiles** —
   compile がそこに書くと dotfiles 汚染 + 手書き内容の上書き事故。
3. **AGENTS.md / GEMINI.md は手書き資産** — `apm compile` は AGENTS.md を生成 (上書き) する
   設計で、手書きの memory file と衝突する。
4. **commit-message は安定した個人ルール** — Codex で多少効かなくても実害が小さく、
   2 ソース管理 (APM instruction + 手書き AGENTS.md) の drift コストに見合わない。

将来 Codex/Gemini にも instructions を効かせたくなった場合の選択肢 (未採用):

- **B-lite**: `apm compile --target codex` の出力を mise task で dotfiles AGENTS.md に
  合成する半自動 sync を組む
- **B**: AGENTS.md / GEMINI.md 全体を APM compile 生成に移行 (手書きスケルトンも primitive 化)
- いずれも `apm compile` の project-local + symlink 問題の解決が前提

---

## 4. dotfiles での運用 (commit-message の例)

### 配備フロー

```text
upstream: agent-package-basic/packages/commit-message/.apm/instructions/commit-message.instructions.md
  │ apm install -g  (instructions は file-deploy target のみ)
  ▼
~/.claude/rules/commit-message.md  (real dir, applyTo → paths: 変換)
```

### link.sh との関係 (重要)

- `~/.claude/rules/` は以前 `claude/mise/scripts/link.sh` が dotfiles へ symlink していた
- APM が instructions を `~/.claude/rules/` に配備するようになったため **symlink と衝突**
  (symlink 越し書き込みで dotfiles 汚染)
- 解決: link.sh の `symlink_targets` から **`rules` を除去** + `migrate.sh` で
  `~/.claude/rules` symlink を Trash 退避 → APM が real dir として書けるようにした
- dotfiles 側の `claude/profiles/*/rules/commit-message.md` は **削除** (APM が正本)

---

## 5. 新しい instruction package を作る手順

```bash
# 1. パッケージ雛形
mkdir -p packages/<name>/.apm/instructions

# 2. frontmatter 付きで作成 (ファイル名 suffix に注意)
cat > packages/<name>/.apm/instructions/<name>.instructions.md <<'EOF'
---
description: 一行要約 (必須)
applyTo: "**"
---

- 箇条書きでルールを書く
- パスは `バッククォート` で囲む
EOF

# 3. apm.yml
cat > packages/<name>/apm.yml <<'EOF'
name: <name>
version: 0.1.0
description: ...
author: Caromaf
includes: auto
dependencies:
  apm: []
  mcp: []
EOF

# 4. ★ 認識確認 (これを怠ると silent fail)
cd packages/<name> && apm compile --validate
#   → "N instructions" が出れば OK。"0 instructions" なら suffix/frontmatter を疑う

# 5. commit + push → consumer 側 apm.yml に追加 → mise run install
```

---

## 6. 関連

- skills の配備 flag 戦略 (default `apm install -g --frozen`): `../../ONBOARDING.md` §5.8
  または `sync-guide.md`
- migrate.sh の legacy symlink cleanup (rules 含む): `agents/mise/tasks/migrate.sh`
- custom-config 依存問題 (OSS 化 prerequisite): ONBOARDING.md §5.9
