# Migration Checklist: 各 PC で APM 移行を完走させる手順

追加 PC / 再セットアップ時に「dotfiles 旧 skill/command/prompt の物理削除」までを
完走させるための**コピペ可能なチェックリスト**。1 PC = 1 セッションで完走できる粒度に分解してある。

> **本ドキュメントの性質**: 各 PC で**順番にコピペすれば終わる手順書**。
> 全体方針・転換ログは [migration-plan.md](./migration-plan.md) を、
> 日常の同期運用は [sync-guide.md](./sync-guide.md) を、
> 設計上の決定事項・方針転換ログは [migration-plan.md](./migration-plan.md) を参照。

---

## 0. PC 別 進捗 (2026-05-29 時点)

| PC          | apm.yml 配置 | mise install 検証 | 旧 dotfiles 削除 | 備考                                       |
| ----------- | ------------ | ----------------- | ---------------- | ------------------------------------------ |
| wsl-ubuntu  | ✅           | ✅                | ⚪ 不要           | dotfiles 内に旧 skill/command 無し         |
| hm-m1-mac   | ✅           | ✅ (実機)          | ✅ (2026-05-29)    | claude/codex/gemini profile + sync_prompt_skills.py を削除 (59 件) |
| xsv-linux-1 | ✅           | ✅ (2026-05-29)    | ✅ (2026-05-29)    | respond-pr 系 5 件削除済                   |
| cg-m2-mac   | ✅           | ✅ (2026-05-28)    | ⚪ 不要           | §1.1–§1.7 完走、削除対象なしで完了         |
| win-15034   | ✅           | ✅ (2026-05-29)    | ✅ (2026-05-29)    | repo 上の旧 46 件削除済、実機 install 完了 |

⚪ = そもそも対象なし、❌ = 未実施、✅ = 実施済み。

---

## 1. 共通: 各 PC で踏む手順

追加 PC / 再セットアップ時は、その PC のローカルで以下を**順番に**実行する。

### 1.1 dotfiles を最新化

```bash
cd ~/dotfiles
git pull
```

### 1.2 mise を信頼

```bash
cd ~/dotfiles/agents
mise trust mise.toml
```

### 1.3 旧 link.sh が貼った symlink を Trash 退避

`~/.claude/{commands,skills}` `~/.gemini/commands` `~/.codex/skills/*` 内の
dotfiles 行き symlink、および `~/.agents/skills/*` を Trash に退避する。
**冪等で reversible**。

```bash
mise run migrate
```

### 1.4 mise.local.toml を生成

```bash
mise run check_env
```

`agents/mise.local.toml` ができるので、エディタで開いて
`DEFAULT_AGENTS_PROFILE` (プロファイル名) を埋める。

例 (xsv-linux-1):

```toml
[env]
DEFAULT_AGENTS_PROFILE = "xsv-linux-1"
```

例 (wsl-ubuntu):

```toml
[env]
DEFAULT_AGENTS_PROFILE = "wsl-ubuntu"
```

> **Note**: `agents/` は OS による処理分岐が無いため `WSL_AGENTS_PROFILE` は廃止済。
> `claude/`・`codex/`・`gemini/` は `link.sh` レベルで OS 依存の挙動があるので
> 当該 dir ではまだ `WSL_<TOOL>_PROFILE` を保持している。

### 1.5 APM packages を install

```bash
mise run install
```

`profile/apm.yml` を `~/.apm/apm.yml` にシンクして `apm install -g` を実行する。
`profile/apm.lock.yaml` が既にあれば `--frozen` で再現性のある install になる。

### 1.6 link.sh で残りの設定を配備

```bash
cd ~/dotfiles/claude && mise run link
cd ~/dotfiles/codex && mise run link
cd ~/dotfiles/gemini && mise run link
```

`settings.json` / `CLAUDE.md` / `config.toml` / `AGENTS.md` / `GEMINI.md` /
`rules` / `custom-config` 等の APM 対象外資産を symlink する
(skill/command/prompt 部分は §1.3 で外したので APM が書く)。

### 1.7 動作検証 (1 つ動けば OK)

```bash
ls ~/.claude/skills/ | head -5
ls ~/.agents/skills/ | head -5
```

任意のプロジェクトで Claude Code を起動して `/respond-pr` などの slash command が
出ることを確認 (PS package のみ、-S package は auto-trigger なので CLI 起動だけでは
表示されない)。

### 1.8 旧 dotfiles の物理削除 (PC 別、§2)

§2 の「該当 PC のブロック」を上から順にコピペ。
win-15034 は repo 上では削除済みのため、実機側では最新化後に対象 directory が残っていないことを確認するだけでよい。

### 1.9 dotfiles を commit

```bash
cd ~/dotfiles
git status
# 削除 diff を目視確認
git add -A claude/profiles/<pc>/ codex/profiles/<pc>/
git commit -m "<pc> で APM 移管済み skill/command/prompt を削除"
```

commit message のルール (`commit-message.md`):

- 50 文字以内・25 文字目安
- Conventional Commits prefix なし、絵文字なし
- 動詞で終える、コード参照はバッククォート

例 (PC 名で差し替え):

```text
xsv-linux-1 で APM 移管済み skill を削除
hm-m1-mac で APM 移管済み skill と command を削除
win-15034 で APM 移管済み 46 件を削除
```

---

## 2. PC 別 削除コマンド

各 PC のローカルで実行する `rm -rf` ブロック。`mise run install` の成功確認後に走らせる。

### 2.1 xsv-linux-1 (5 件)

```bash
rm -rf \
  ~/dotfiles/claude/profiles/xsv-linux-1/skills/respond-to-pr-reviews \
  ~/dotfiles/claude/profiles/xsv-linux-1/commands/respond-pr.md \
  ~/dotfiles/codex/profiles/xsv-linux-1/skills/respond-pr \
  ~/dotfiles/codex/profiles/xsv-linux-1/skills/respond-to-pr-reviews \
  ~/dotfiles/codex/profiles/xsv-linux-1/prompts/respond-pr.md

# 親 dir が空になったら削除 (空でなければエラー無視)
rmdir ~/dotfiles/claude/profiles/xsv-linux-1/skills 2>/dev/null
rmdir ~/dotfiles/claude/profiles/xsv-linux-1/commands 2>/dev/null
rmdir ~/dotfiles/codex/profiles/xsv-linux-1/skills 2>/dev/null
rmdir ~/dotfiles/codex/profiles/xsv-linux-1/prompts 2>/dev/null
```

### 2.2 cg-m2-mac (削除対象なし)

skills / commands / prompts ディレクトリは既に空。`rm` 実行不要。
`mise run install` が成功すれば §1 で完走扱い。

### 2.3 hm-m1-mac (59 件、2026-05-29 実施済み)

repo 上では 2026-05-29 に claude/codex/gemini profile と
`sync_prompt_skills.py` を削除済み。再実行しても対象は存在しない想定。

#### claude side (17 件)

```bash
rm -rf \
  ~/dotfiles/claude/profiles/hm-m1-mac/skills/breaking_change_in_php_framework \
  ~/dotfiles/claude/profiles/hm-m1-mac/skills/codex-review \
  ~/dotfiles/claude/profiles/hm-m1-mac/skills/framework_changelog \
  ~/dotfiles/claude/profiles/hm-m1-mac/skills/gh-link-subissues \
  ~/dotfiles/claude/profiles/hm-m1-mac/skills/gh-unlink-subissue \
  ~/dotfiles/claude/profiles/hm-m1-mac/skills/respond-to-pr-reviews \
  ~/dotfiles/claude/profiles/hm-m1-mac/commands/close-issue.md \
  ~/dotfiles/claude/profiles/hm-m1-mac/commands/create-issue.md \
  ~/dotfiles/claude/profiles/hm-m1-mac/commands/discover.md \
  ~/dotfiles/claude/profiles/hm-m1-mac/commands/release \
  ~/dotfiles/claude/profiles/hm-m1-mac/commands/respond-pr.md \
  ~/dotfiles/claude/profiles/hm-m1-mac/commands/review-design-doc.md \
  ~/dotfiles/claude/profiles/hm-m1-mac/commands/review-pr.md \
  ~/dotfiles/claude/profiles/hm-m1-mac/commands/scaffold.md \
  ~/dotfiles/claude/profiles/hm-m1-mac/commands/solve-issue.md \
  ~/dotfiles/claude/profiles/hm-m1-mac/commands/ux-review.md \
  ~/dotfiles/claude/profiles/hm-m1-mac/commands/worktree.md

rmdir ~/dotfiles/claude/profiles/hm-m1-mac/skills 2>/dev/null
rmdir ~/dotfiles/claude/profiles/hm-m1-mac/commands 2>/dev/null
```

#### gemini side (4 件、migration-plan.md §9.5 gemini target 副作用の解消)

`~/dotfiles/gemini/profiles/hm-m1-mac/commands/` の `.toml` 4 件は APM catalog の prompt から
`~/.gemini/commands/<n>.toml` に再生成されるため、dotfiles 側の物理コピーは削除する。

```bash
rm -rf \
  ~/dotfiles/gemini/profiles/hm-m1-mac/commands/review-pr.toml \
  ~/dotfiles/gemini/profiles/hm-m1-mac/commands/review-design-doc.toml \
  ~/dotfiles/gemini/profiles/hm-m1-mac/commands/release

rmdir ~/dotfiles/gemini/profiles/hm-m1-mac/commands 2>/dev/null
```

#### codex side

repo 上では削除済み。`~/dotfiles/codex/profiles/hm-m1-mac/{skills,prompts}/` は
存在しない想定。

### 2.4 win-15034 (claude 16 + codex 30 = 46 件、2026-05-29 実施済み)

repo 上では 2026-05-29 に削除済み。再実行しても対象は存在しない想定。

#### claude side

```bash
rm -rf \
  ~/dotfiles/claude/profiles/win-15034/skills/breaking_change_in_php_framework \
  ~/dotfiles/claude/profiles/win-15034/skills/codex-review \
  ~/dotfiles/claude/profiles/win-15034/skills/framework_changelog \
  ~/dotfiles/claude/profiles/win-15034/skills/gh-link-subissues \
  ~/dotfiles/claude/profiles/win-15034/skills/gh-unlink-subissue \
  ~/dotfiles/claude/profiles/win-15034/commands/aws-auth.md \
  ~/dotfiles/claude/profiles/win-15034/commands/close-issue.md \
  ~/dotfiles/claude/profiles/win-15034/commands/create-issue.md \
  ~/dotfiles/claude/profiles/win-15034/commands/discover.md \
  ~/dotfiles/claude/profiles/win-15034/commands/login-microsoft.md \
  ~/dotfiles/claude/profiles/win-15034/commands/release \
  ~/dotfiles/claude/profiles/win-15034/commands/review-design-doc.md \
  ~/dotfiles/claude/profiles/win-15034/commands/review-pr.md \
  ~/dotfiles/claude/profiles/win-15034/commands/scaffold.md \
  ~/dotfiles/claude/profiles/win-15034/commands/solve-issue.md \
  ~/dotfiles/claude/profiles/win-15034/commands/ux-review.md \
  ~/dotfiles/claude/profiles/win-15034/commands/worktree.md

rmdir ~/dotfiles/claude/profiles/win-15034/skills 2>/dev/null
rmdir ~/dotfiles/claude/profiles/win-15034/commands 2>/dev/null
```

#### codex side

```bash
rm -rf \
  ~/dotfiles/codex/profiles/win-15034/skills/aws-auth \
  ~/dotfiles/codex/profiles/win-15034/skills/breaking_change_in_php_framework \
  ~/dotfiles/codex/profiles/win-15034/skills/close-issue \
  ~/dotfiles/codex/profiles/win-15034/skills/codex-review \
  ~/dotfiles/codex/profiles/win-15034/skills/create-issue \
  ~/dotfiles/codex/profiles/win-15034/skills/discover \
  ~/dotfiles/codex/profiles/win-15034/skills/framework_changelog \
  ~/dotfiles/codex/profiles/win-15034/skills/gh-link-subissues \
  ~/dotfiles/codex/profiles/win-15034/skills/gh-unlink-subissue \
  ~/dotfiles/codex/profiles/win-15034/skills/login-microsoft \
  ~/dotfiles/codex/profiles/win-15034/skills/release-execute \
  ~/dotfiles/codex/profiles/win-15034/skills/release-prepare \
  ~/dotfiles/codex/profiles/win-15034/skills/review-design-doc \
  ~/dotfiles/codex/profiles/win-15034/skills/review-pr \
  ~/dotfiles/codex/profiles/win-15034/skills/scaffold \
  ~/dotfiles/codex/profiles/win-15034/skills/solve-issue \
  ~/dotfiles/codex/profiles/win-15034/skills/ux-review \
  ~/dotfiles/codex/profiles/win-15034/skills/worktree \
  ~/dotfiles/codex/profiles/win-15034/prompts/aws-auth.md \
  ~/dotfiles/codex/profiles/win-15034/prompts/close-issue.md \
  ~/dotfiles/codex/profiles/win-15034/prompts/create-issue.md \
  ~/dotfiles/codex/profiles/win-15034/prompts/discover.md \
  ~/dotfiles/codex/profiles/win-15034/prompts/login-microsoft.md \
  ~/dotfiles/codex/profiles/win-15034/prompts/release \
  ~/dotfiles/codex/profiles/win-15034/prompts/review-design-doc.md \
  ~/dotfiles/codex/profiles/win-15034/prompts/review-pr.md \
  ~/dotfiles/codex/profiles/win-15034/prompts/scaffold.md \
  ~/dotfiles/codex/profiles/win-15034/prompts/solve-issue.md \
  ~/dotfiles/codex/profiles/win-15034/prompts/ux-review.md \
  ~/dotfiles/codex/profiles/win-15034/prompts/worktree.md

rmdir ~/dotfiles/codex/profiles/win-15034/skills 2>/dev/null
rmdir ~/dotfiles/codex/profiles/win-15034/prompts 2>/dev/null
```

---

## 3. 完走判定

各 PC で以下が**全て** true になったら完走:

- [ ] `mise run install` が exit 0
- [ ] `~/.claude/skills/` に basic catalog 21 件が見える
  (custom catalog 7 件は wsl-ubuntu のみ)
- [ ] `~/.agents/skills/` に同じ skill が cross-tool 共有として見える
- [ ] `dotfiles/{claude,codex,gemini}/profiles/<pc>/{skills,commands,prompts}/` に
  APM 移管対象が残っていない (gemini は hm-m1-mac のみ profile が存在)
- [ ] dotfiles に削除 commit が積まれている

---

## 4. ロールバック

万一 `mise run install` が壊れて作業 PC で skill が使えなくなった場合:

### 4.1 Trash から symlink を戻す

migrate.sh は **冪等で reversible**。`~/.local/share/Trash/files/`
(linux) や `~/.Trash/` (mac) から退避された symlink を戻せる。

### 4.2 `apm install -g --refresh --force` で再 deploy

```bash
cd ~/dotfiles/agents
mise run update
```

### 4.3 ロールバック後の検証

```bash
ls -la ~/.claude/skills/ | head -10
mise run status
```

---

## 5. 発展 (将来の作業)

- **`#main` 恒常運用** (旧 `v0.1.0` tag 案は撤回、migration-plan.md §9): upstream は
  自作物のため常に最新を取り込む。破壊的変更を入れる時のみ semver tag を検討する。
- **§5.9 解消後**: `custom-config/<n>.json` 依存が消えたら、basic catalog を真の
  OSS として他人にも勧められる状態になる。
