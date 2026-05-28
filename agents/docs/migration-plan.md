# Migration Plan: 旧 dotfiles 分散 → 新 APM 集約 (移行記録)

旧設計 (`dotfiles/{claude,codex,gemini}/` に同概念が 3 ヶ所重複) から、新設計 (外部 2 repo + APM consumer manifest) への移行記録。

> **本ドキュメントの性質**: 計画書ではなく **完了記録**。Phase 0-2 と Phase 5 は完了済み、
> Phase 3-4 は進行中 (basic 18 packages の構築)。日常運用は [sync-guide.md](./sync-guide.md) を参照。

---

## 0. 当初の課題

### 旧設計の問題点

`dotfiles/claude/`, `dotfiles/codex/`, `dotfiles/gemini/` に同じ概念が**形式違いで 3 重に
存在**していた:

| 概念         | claude                    | codex                         | gemini                    |
| ------------ | ------------------------- | ----------------------------- | ------------------------- |
| review-pr    | `commands/review-pr.md`   | `prompts/review-pr.md`        | `commands/review-pr.toml` |
| solve-issue  | `commands/solve-issue.md` | `skills/solve-issue/SKILL.md` | (なし)                    |
| codex-review | `skills/codex-review/...` | `skills/codex-review/...`     | (なし)                    |

1 つ修正するために 3 ヶ所編集する状態 → **1 個書けば 3 ツールに展開** したい。

### 解決手段の選定

[Microsoft APM (Agent Package Manager)](https://microsoft.github.io/apm/) を採用。
prompts / skills / commands / agents / instructions を**ツール非依存の primitive** として
扱い、deploy 時に各ツールのネイティブ配置先 (`.claude/commands/`, `.codex/prompts/` 等)
へ展開する。

---

## 1. 設計の試行錯誤

### 1.1 当初設計 (廃案)

最初の構想:

- `dotfiles/agents/packages/<name>/` に汎用パッケージを **dotfiles 同梱**
- profile manifest から `../../packages/<name>` (相対パス) で参照
- 公開汎用 repo は作らず、必要になるまで dotfiles に集約

### 1.2 Phase 0 プローブで判明した制約 (2026-05-27)

`~/.apm/apm.yml` を `~/dotfiles/agents/profiles/wsl-ubuntu/apm.yml` への symlink にし、
`dependencies.apm` に `../../packages/_smoke` (相対パス) を書いて `apm install -g` を実機実行:

```text
[x] ../../packages/_smoke -- relative local paths are not supported at user
    scope (--global). Use an absolute path or a remote reference (owner/repo)
    instead
```

**user-scope では相対パスのローカル参照は禁止**。これで「dotfiles 同梱 + 相対パス参照」案
が成立しないことが確定した。

さらに `--dry-run` だと**この validation が走らず**、install 計画を返してしまうため、
**dry-run の通過は信用できない** (= 必ず非 dry-run で実機展開まで確認する必要がある) も
判明。

### 1.3 確定した新設計

| repo / dir                    | 公開          | 役割                                   |
| ----------------------------- | ------------- | -------------------------------------- |
| `Caromaf/agent-package-basic` | public        | 公開可能な汎用パッケージ               |
| `github-user/agent-package-*` | private       | private repo で非公開な内容を扱う      |
| `dotfiles/agents/`            | dotfiles 同梱 | consumer manifest のみ。本体は持たない |

参照は **remote ref** (`<owner>/<repo>/packages/<name>#<ref>`) で行う。

---

## 2. パッケージ仕分け (確定)

### 2.1 `agent-package-basic` (public、20 個、構築済み)

claude commands / codex skills / 既存 dotfiles の各所から集約。全 20 package が
`Caromaf/agent-package-basic` の `setup` ブランチに 1 commit/package で揃っており、
別 PC で main へ push する作業のみが残っている (この PC からは Caromaf に push しない方針)。

| name                             | 旧 type (claude / codex) | 備考                                                                                                    |
| -------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------- |
| close-issue                      | command / skill          | claude prompt と codex skill の二系統を持つ                                                             |
| create-issue                     | command / skill          | `~/.claude/custom-config` → `~/.codex/custom-config` の portable fallback で設定 JSON を共有            |
| discover                         | command / skill          |                                                                                                         |
| release-prepare                  | command / skill          | `release/prepare.md` 由来。`## [Unreleased]` セクションのみを更新する                                   |
| release-execute                  | command / skill          | `release/execute.md` 由来。`release-prepare` で更新済の前提でタグ作成・push まで一貫実行                |
| review-design-doc                | command / skill          |                                                                                                         |
| review-pr                        | command / skill          | **PoC 対象**。後に `solve-issue` 同型へ規範化                                                           |
| scaffold                         | command / skill          |                                                                                                         |
| solve-issue                      | command / skill          | claude+codex 両対応 package の **規範テンプレート**                                                     |
| ux-review                        | command / -              | prompt は claude 表現 (`claude mcp add` / `Claude Code` 再起動)、SKILL は codex 表現を保持              |
| worktree                         | command / -              | prompt は `EnterWorktree`/`ExitWorktree` 専用ツール、SKILL は素の `git worktree` コマンドを使用         |
| codex-review                     | skill / skill            | 主語を "the agent" に統一。CLI 名としての `codex` 呼び出し (`codex review`/`codex exec`) は維持         |
| gh-link-subissues                | skill / skill            | `create-issue-config.json` を `~/.claude/custom-config` → `~/.codex/custom-config` の探索順で参照       |
| gh-unlink-subissue               | skill / skill            |                                                                                                         |
| breaking-change-in-php-framework | - / skill                | 判定ルール skill                                                                                        |
| framework-changelog              | - / skill                | 判定ルール skill                                                                                        |
| frontend-aesthetics              | - / skill                | デザイン指針 skill                                                                                      |
| mise-tasks                       | skill / -                | 判定ルール skill                                                                                        |
| use-interesting-fonts            | - / skill                | タイポグラフィ指針 skill                                                                                |
| with-codex-skills                | skill / -                | **multi-file skill**: SKILL.md + `references/workflows.md` + `scripts/{codex-exec.sh,codex-manager.sh}` |

### 2.2 `agent-package-custom` (private、7 個、構築済み)

| name                     | 旧 type         | primitive    | 備考                      |
| ------------------------ | --------------- | ------------ | ------------------------- |
| aws-auth                 | command / skill | prompt+skill | AWS 認証                  |
| login-microsoft          | command / skill | prompt+skill | Entra ID を使ったログイン |
| project-up               | - / skill       | skill        |                           |
| project-status           | - / skill       | skill        |                           |
| project-browse           | command / skill | prompt+skill |                           |
| project-investigate-logs | command / skill | prompt+skill |                           |
| project-aws-rule         | command / skill | prompt+skill |                           |

> project / work 系を **`agent-package-custom` 1 catalog に集約**する方針で確定 (2026-05-28)。

汎用ルール (`commit-message` 等の instructions) は **basic catalog に配置** する方針
(`agent-package-basic/packages/commit-message`)。理由は OSS 適合性: ツール/環境/組織非依存で他人にも使ってもらえる汎用資産は basic に置き、private 固有のもののみをcustom に残す。詳細は §8 を参照。

---

## 3. Phase 1 PoC 結果 (2026-05-27, `review-pr` 1 個)

### 試したこと

`agent-package-basic/packages/review-pr/` を絶対パスで `~/.apm/apm.yml` に書き、
`apm install -g` を実機実行 (= dry-run ではない)。

### 確認できた事実

1. **絶対パスは user-scope で受理される** (相対パスのみ禁止)
2. **`.apm/prompts/<name>.prompt.md` → `~/.claude/commands/<name>.md`** という写像が動く
   (= APM の `prompts` が claude では `commands` として展開される)
3. **`mode: agent` frontmatter は claude / cursor で不要**、APM が dropped と警告
   - サポート対象 keys (claude command): `allowed-tools`, `argument-hint`, `description`, `input`, `model`
4. **`Active global targets` は auto-detect** で決まる (`~/.claude/`, `~/.cursor/`, `~/.copilot/`,
   `~/.codex/` がディレクトリ存在で active 化)
   - `apm.yml` の `targets:` は **絞り込めない** — auto-detect が prepend されるだけ
   - 確実に絞るには CLI `--target claude` か、不要な dir を消す
5. **lockfile が `~/.apm/apm.lock.yaml` に生成され**、`deployed_file_hashes` (sha256) を含む
6. **dry-run の副作用**: `~/.apm/apm.yml` が無いと**自動生成**される (dry-run でも書かれる) →「Phase 0 で空 manifest を symlink → dry-run」案は**そのままだと不可**
7. **CWD 汚染**: `apm install -g` は **CWD に `.gitignore` (`apm_modules/` 行)** を作る。
   `/tmp` で走らせると `/tmp/.gitignore` が生まれる → `/tmp` のような共用 dir で実行しないこと
8. **既存ファイルとの collision**: `~/.claude/commands/review-pr.md` が既存だと衝突。
   PoC では事前に `.bak` 退避で回避

### 確定した PoC 構造

```text
agent-package-basic/
├── README.md
└── packages/
    └── review-pr/
        ├── apm.yml                          # name, version, description, includes: auto
        └── .apm/
            └── prompts/
                └── review-pr.prompt.md      # claude では `~/.claude/commands/review-pr.md` に展開
```

frontmatter は claude 互換キーのみ:

```yaml
---
description: "..."
argument-hint: "..."
allowed-tools: ...
---
```

(`mode: agent` は **書かない** — APM が警告 + drop する)

---

## 4. Phase 2 実機展開結果 (2026-05-27, custom 7 packages)

### 実行内容

`~/dotfiles/agents/profiles/wsl-ubuntu/apm.yml` で 7 packages 全てを `#main` で個別参照
→ `~/.apm/apm.yml` に symlink → `cd ~/.apm && apm install -g`。

### 結果

- 全 7 packages の git fetch 成功 (resolved_commit `2c1b7851`)
- `~/.claude/commands/<name>.md` 7 ファイル生成、`~/.cursor/commands/<name>.md` 7 ファイル生成 (= 14 デプロイ)
- `~/.apm/apm.lock.yaml` 生成 (sha256 hash + commit pin 記録)
- harness の skill 一覧に新フラット名 (`/aws-auth` など) が即時登場

### 観察事項

1. **codex には展開されない**: `Some primitives are not supported: codex (...)` の警告通り、`prompts` type は user-scope では codex が受けない
2. **partial clone 警告 6 回**: `Partial clone (--filter=blob:none) failed` が連発するが
   全て自動リトライで成功。複数 deps が同じ repo を **個別に clone** しているため。
   root 参照 1 行に変えれば fetch 1 回で済むはず
3. **cursor への二重展開**: `~/.cursor/` 存在で auto-detect が cursor を targets に含めた
4. **既存ファイルの退避必要**: claude `aws-auth.md`, `login-microsoft.md` と codex 同等を
   `.bak` 退避してから install (PoC と同じ手順)

---

## 5. Phase 5: symlink 事故と APM 専管化 (2026-05-27、最重要)

### 5.1 発覚した事故

Phase 2 完了直後、`cd ~/dotfiles && git status` で以下を発見:

```text
modified:   claude/profiles/wsl-ubuntu/commands/aws-auth.md
deleted:    codex/profiles/wsl-ubuntu/prompts/aws-auth.md
Untracked:  claude/profiles/wsl-ubuntu/commands/project-up.md
Untracked:  claude/profiles/wsl-ubuntu/commands/project-browse.md
... (他多数)
```

### 5.2 根本原因

`~/.claude/commands` と `~/.codex/prompts` が **dotfiles 配下への symlink** だった:

```text
~/.claude/commands  → ~/dotfiles/claude/profiles/wsl-ubuntu/commands
~/.codex/prompts    → ~/dotfiles/codex/profiles/wsl-ubuntu/prompts
```

これは旧 link.sh 設計の名残。APM は **symlink を辿って書き込む** ため、`apm install -g` が dotfiles repo を直接書き換えていた。

### 5.3 副次的な事故: `mv` で symlink を辿った

衝突解消のために実行した:

```bash
mv ~/.claude/commands/aws-auth.md{,.bak}     # ← これが事故
mv ~/.codex/prompts/aws-auth.md{,.bak}        # ← これも
```

`mv` は symlink 経由で **target (= dotfiles 配下のファイル) を rename** する。結果として
dotfiles repo の `claude/.../aws-auth.md` を `aws-auth.md.bak` にリネームしてしまい、
git では `deleted: aws-auth.md` + `Untracked: aws-auth.md.bak` として現れた。

### 5.4 採用した対処 (Option A: APM 専管化)

dotfiles と APM の責務を完全分離する方針を採用:

```bash
# Phase 1: dotfiles の汚染を復旧
cd ~/dotfiles
git restore claude/profiles/wsl-ubuntu/commands/aws-auth.md \
            claude/profiles/wsl-ubuntu/commands/login-microsoft.md \
            codex/profiles/wsl-ubuntu/prompts/aws-auth.md \
            codex/profiles/wsl-ubuntu/prompts/login-microsoft.md
rm claude/profiles/wsl-ubuntu/commands/project-{aws-rule,browse,investigate-logs,status,up}.md \
   claude/profiles/wsl-ubuntu/commands/aws-auth.md.bak \
   claude/profiles/wsl-ubuntu/commands/login-microsoft.md.bak \
   codex/profiles/wsl-ubuntu/prompts/aws-auth.md.bak \
   codex/profiles/wsl-ubuntu/prompts/login-microsoft.md.bak

# Phase 2: APM install state を消す
rm ~/.apm/apm.lock.yaml
rm -r ~/.apm/apm_modules
rm -r ~/.apm/apm_modules.bak

# Phase 3: symlink を削除して実 dir として作り直す (rm に -r を付けないこと)
rm ~/.claude/commands
mkdir ~/.claude/commands
rm ~/.codex/prompts
mkdir ~/.codex/prompts

# Phase 4: 再 install
cd ~/.apm && apm install -g
```

### 5.5 確認できた事実

1. **`~/.claude/commands/` が実 dir として確立** — `ls -la` で `->` 記号なし
2. **dotfiles はクリーン** — `git status` から今回起因の差分が完全消滅
3. **lockfile 再生成** — `resolved_commit: 2c1b785...` (Phase 2 と同 pin)
4. **旧 namespace `/project:up` 消滅** — symlink 解除で `~/.claude/commands/project/` が見えなくなり、フラット `/project-up` のみが残った
5. **UI 動作確認 OK** — Claude Code から `/aws-auth` を実行、APM が deploy した本体が正しく応答することを確認

### 5.6 教訓 (今後の APM 運用で必須)

#### 教訓 1: APM 専管 dir は実 dir に保つ

`~/.claude/commands`, `~/.codex/prompts`, `~/.cursor/commands` 等を **symlink にしない**。
新マシンセットアップでは必ず確認:

```bash
ls -la ~/.claude/commands ~/.codex/prompts ~/.cursor/commands 2>/dev/null
# "lrwx..." (-> ...) なら symlink。即削除して mkdir し直す
```

#### 教訓 2: `mv link target` は symlink を辿る

`mv ~/.claude/commands/foo.md{,.bak}` のような退避でも target 側 (= dotfiles 配下) を改変してしまう。退避前に必ず `ls -la` で **symlink かどうかを確認** する習慣を持つ。

#### 教訓 3: symlink 削除には `rm -r` を使わない

```bash
rm ~/.claude/commands       # OK: symlink 自体を削除
rm -r ~/.claude/commands    # NG: symlink 先 (= dotfiles 配下) を再帰削除する可能性
```

これらの教訓は [sync-guide.md §6.1](./sync-guide.md) のトラブルシュートにも反映済み。

### 5.7 Phase 5 再発と恒久対策 (2026-05-27 追補)

Phase 5 で `~/.claude/commands` を実 dir 化した直後、**custom 7 packages に skill を追加して再 install** したところ、同種の事故が `~/.claude/skills` 側で再発した。

#### 5.7.1 再発の原因

dotfiles の link.sh (`~/dotfiles/claude/mise/scripts/link.sh`) が、profile 適用のたびに **`commands` と `skills` を symlink_targets として symlink を再生成**していた:

```bash
# (旧) link.sh
symlink_targets=(CLAUDE.md commands skills custom-config rules)
```

つまり Phase 5 で手動で実 dir 化しても、**次回 `mise run link` を走らせた瞬間に
symlink が復活**する構造だった。codex 側 link.sh も同じく `~/.codex/skills/<APM 7 件>` を `dotfiles/codex/profiles/<prof>/skills/` への symlink として再生成していた。

#### 5.7.2 恒久対策: link.sh から APM 専管 primitive を除外

両 link.sh を改修して APM が引き受ける primitive を symlink_targets から外した:

- `~/dotfiles/claude/mise/scripts/link.sh`: `symlink_targets=(CLAUDE.md custom-config rules)`
  に変更 (`commands` / `skills` を削除)。
- `~/dotfiles/codex/mise/scripts/link.sh`: skills ループの "Skipping skill because target already exists" 経路で APM 製の実 dir を skip する設計を**意図として明文化** (loop 自体は既に正しく動いていたため logic 変更なし、ヘッダコメントで運用ルールを宣言)。

これに加え、**dotfiles 側 `profiles/<prof>/skills/` から APM 専管名 (`aws-auth`,
`login-microsoft`, `project-*` 等) を削除**することで、衝突源そのものを断った。

#### 5.7.3 教訓 4: dotfiles link.sh と APM の責務境界を明示する

旧 link.sh は「dotfiles で管理する設定全部を symlink」する素朴な設計だった。APM 移行後は **APM 専管 dir** (`~/.claude/{commands,skills}`, `~/.codex/skills/<APM 専管 name>`, `~/.agents/skills/`) を symlink_targets から**明示的に外す**必要がある。link.sh のヘッダコメントに APM 共存方針を書いておくと、未来の編集者 (= 自分) が再発させない。

#### 5.7.4 教訓 5: `apm install` と `apm install -g` は別モード

user-scope (= HOME 直下の `~/.claude/`, `~/.codex/` 等への deploy) を狙うなら **`-g` 必須**。
`-g` 抜きで実行すると、APM は **CWD を project root とみなして deploy** する:

| モード           | 実 deploy 先                                     | 用途                                    |
| ---------------- | ------------------------------------------------ | --------------------------------------- |
| `apm install -g` | `~/.claude/...`, `~/.codex/...`, `~/.agents/...` | user-global (dotfiles の責務領域と並ぶ) |
| `apm install`    | `<CWD>/.claude/...`, `<CWD>/.codex/...`          | per-project (リポジトリ同梱)            |

`~/.apm/` を CWD にしても `-g` 抜きだと `~/.apm/.claude/`, `~/.apm/.agents/` のような **隔離 dir** に書かれるだけで HOME には何も deploy されない (実体験あり)。`-g` 忘れた場合の症状: `[i] Installing to user scope` ではなく **harness auto-detect が CWD で走る** ため、`No harness detected` エラーや、CWD 隔離 dir への deploy になる。

#### 5.7.5 教訓 6: Codex の skill 正規 deploy 先は `~/.agents/skills/`

APM 公式仕様 (`docs/concepts/primitives-and-targets.md`):

> **codex** -- Codex CLI. Agents and hooks use TOML; skills use the cross-tool `.agents/` directory.

つまり Codex の skill 配置先は **`~/.codex/skills/` ではなく `~/.agents/skills/`**。
この `.agents/skills/` は cross-tool portable な領域で、Codex CLI が直接読む設計。
install ログに `1 skill(s) integrated -> .agents/skills/, .claude/skills/` と出るのは正常 (claude target と codex target が共に skill を引き受けた結果)。

なお、dotfiles の codex profile が `~/.codex/skills/<dotfiles 由来の symlink 18 件>` に配置している既存スキルとは **dir が分離**しているため、両者は orthogonal に共存する。
Codex CLI 0.x は `~/.codex/skills/` と `~/.agents/skills/` の両方を skill として認識する。

---

## 6. 進行中タスク (2026-05-27 時点)

| #     | 状態 | 内容                                                                                                                                                                                                     |
| ----- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 18    | done | 既存 commands/skills を 3 バケットに仕分け                                                                                                                                                               |
| 19    | done | `agent-package-basic` に `review-pr` 1 個で PoC、構造を確定 (commit `eec0544`)                                                                                                                           |
| 20    | done | `agent-package-custom` を 7 個で初期構築、`github-user/agent-package-custom` を private repo として GitHub 作成済み                                                                                      |
| 21    | done | `agent-package-basic` の残り全 packages を `setup` ブランチに commit 済 (子タスク #30-#48 に分割、計 20 packages)                                                                                        |
| 22    | done | custom 7 packages を `apm install -g` で実機展開、`~/.claude/commands/` を APM 専管化、`/aws-auth` の UI 動作確認済み                                                                                    |
| 23    | done | sync-guide / migration-plan / README を新設計で書き直し (本ドキュメント)                                                                                                                                 |
| 24    | done | custom 7 packages に Codex 用 `.apm/skills/<name>/SKILL.md` を追加 (claude / codex 両 target で skill native 配信が可能に)                                                                               |
| 25    | done | dotfiles claude link.sh から `commands` / `skills` を除外 (§5.7.2 恒久対策)                                                                                                                              |
| 26    | done | dotfiles codex link.sh の APM 共存性確認、ヘッダコメントで運用ルール明文化                                                                                                                               |
| 27    | done | `~/.codex/skills/<APM 7 件 + dangling release symlinks>` を整理                                                                                                                                          |
| 28    | done | `apm install -g` で lockfile 再生成 (`b76c616`) と skills を `~/.{claude,agents}/skills/<7件>` に deploy                                                                                                 |
| 29    | done | 本ドキュメント §5.7 として Phase 5 再発と恒久対策 (教訓 4-6) を追加                                                                                                                                      |
| 30    | done | `review-pr` PoC を `solve-issue` 同型へ規範化 (`solve-issue` を template として確立)                                                                                                                     |
| 31-39 | done | claude+codex 両対応 9 packages (`close-issue`, `create-issue`, `discover`, `review-design-doc`, `scaffold`, `ux-review`, `worktree`, `release-execute`, `release-prepare`) を量産                        |
| 40-46 | done | codex-only 7 packages (`breaking-change-in-php-framework`, `codex-review`, `framework-changelog`, `frontend-aesthetics`, `gh-link-subissues`, `gh-unlink-subissue`, `use-interesting-fonts`) を basic 化 |
| 47-48 | done | dotfiles claude 由来 2 packages (`mise-tasks` 単一 SKILL、`with-codex-skills` multi-file SKILL) を basic 化                                                                                              |

### 残 Phase: basic 20 packages の push と展開検証

`Caromaf/agent-package-basic` への push は **この PC からは行わない方針**のため、
別 PC で `setup` ブランチを fetch → main に merge → push する作業のみが残る:

1. 別 PC で `git fetch origin setup && git merge --ff-only origin/setup` (または PR 経由で main へ)
2. `dotfiles/agents/profiles/<machine>/apm.yml` の `dependencies.apm` に
   `Caromaf/agent-package-basic/packages/<name>#main` を 20 件分追加
3. `apm install -g` で展開、lockfile に 20 packages 全件が記録されることを確認
4. UI から `/<command>` および skill retrieval を抜き取りで動作確認

#### 量産で確立した recipe

`#30-#48` を通じて以下のパターンが固まった (今後 basic に新規 package を加える際の手順):

1. `agent-package-basic/packages/<name>/apm.yml` (`name`, `version: 0.1.0`, `description`, `author`, `includes: auto`, 空の `dependencies`)
2. claude 起源なら `.apm/prompts/<name>.prompt.md` (frontmatter は `description`, `argument-hint`, `allowed-tools` のみ。`mode: agent` は書かない)
3. codex 起源なら `.apm/skills/<name>/SKILL.md` (frontmatter は `name` (= ディレクトリ名) と `description` (使用シーンを「〜が必要なときに使用する」形式) のみ。`metadata:` や `<!-- codex-profile-generated-from-prompt -->` 等の wrapper は削除)
4. 両系統存在する場合は **本文を `the agent` 主語で統一**、CLI 固有表現は各 target に
   合わせて分岐 (例: `ux-review` の `claude mcp add` ↔ `codex mcp add`)
5. multi-file skill は `.apm/skills/<name>/{references,scripts}/...` をディレクトリごと配置し、SKILL.md 内の参照パスを **deploy 後の実パス** (`~/.claude/skills/<name>/...`) に揃える (`with-codex-skills` の例)
6. portable な設定参照は `~/.claude/custom-config/<file>` → `~/.codex/custom-config/<file>` の探索順 fallback で claude/codex どちらに deploy されても動くようにする(`create-issue`, `gh-link-subissues` の例)
7. 1 commit/package を厳守 (Subject に対象 package 名をバッククォートで含めると `git log --oneline` がそのまま basic の目次になる)

---

## 7. 旧ファイル削除 (将来の Phase 6)

`#21` 完了後、`dotfiles/{claude,codex,gemini}/profiles/<x>/{commands,skills,prompts}` のうち APM が引き受けたものを削除する。

### 削除前の確認

```bash
# APM 由来になっているか全件確認
for cmd in $(ls ~/dotfiles/claude/profiles/wsl-ubuntu/commands/*.md 2>/dev/null); do
  basename=$(basename "$cmd")
  target="$HOME/.claude/commands/$basename"
  if [ -L "$target" ]; then
    echo "STILL SYMLINK: $target"
  elif [ -f "$target" ]; then
    echo "OK (APM 由来): $target"
  else
    echo "MISSING: $target"
  fi
done
```

全て "OK (APM 由来)" になっていることを確認してから削除。

### link.sh の symlink_targets を更新 (§5.7.2 で **実施済み**)

```bash
# 旧: symlink_targets=(CLAUDE.md commands skills custom-config rules)
# 現: symlink_targets=(CLAUDE.md custom-config rules)         # claude link.sh
```

`commands` / `skills` は APM が引き受けたため link.sh の責務外。`CLAUDE.md` /
`custom-config` / `rules` は引き続き link.sh が管理 (Phase 6 で `rules` を APM
`instructions` primitive 化する場合は同様に外す)。

codex link.sh は skills loop が APM 製の実 dir を skip する設計のため symlink_targets の変更は不要 (ヘッダコメントで APM 共存方針を明文化のみ)。

---

## 8. `rules/` の APM `instructions` primitive 化 (進行中: 着手 2026-05-28)

`dotfiles/claude/profiles/*/rules/commit-message.md` は 5 PC で同一内容を複製しており、APM 化の DRY 整理候補。APM 公式は `instructions` primitive を提供しており、Claude target には `.claude/rules/<name>.md` として配備される
([author-primitives/instructions-and-agents](https://microsoft.github.io/apm/producer/author-primitives/instructions-and-agents/))。
§7 末尾で予告された Phase の deepening。

### 8.1 deploy mapping

| Target   | 出力先                                        | 形式                |
| -------- | --------------------------------------------- | ------------------- |
| Claude   | `.claude/rules/<name>.md`                     | `paths:` field 付き |
| Cursor   | `.cursor/rules/<name>.mdc`                    | `globs:` field      |
| Windsurf | `.windsurf/rules/<name>.md`                   | `trigger: glob`     |
| Copilot  | `.github/instructions/<name>.instructions.md` | inline              |
| Codex    | **`AGENTS.md` に fold**                       | per-file dir 無し   |
| Gemini   | **`GEMINI.md` に fold**                       | per-file dir 無し   |

frontmatter の必須フィールドは `applyTo: "<glob>"` (省略すると本体ファイルに混入)。

### 8.2 着手条件と移行手順

1. `agent-package-basic` (public) に `commit-message` instructions package を新設:
   - `packages/commit-message/apm.yml` (空の `dependencies`、`includes: auto`)
   - `packages/commit-message/.apm/instructions/commit-message.md`
     (frontmatter `applyTo: "**"`、本文は現 `rules/commit-message.md` を移植)
   - **配置先を basic にする理由**: 汎用ルール (組織/ツール/環境非依存) は OSS 適合性を持つため public catalog 配置が適切。private は custom に残し、汎用は basic に移すという責務分離を明確化する。
2. **配信戦略**: `commit-message` は **public profile 経由で 5 PC 全部**に配信(= `profiles/<pc>/apm.yml` の `dependencies.apm:` に `Caromaf/agent-package-basic/packages/commit-message#main` を追加)。dotfiles に commitされるため git 経由で 5 PC 同期される。
3. `mise run install` で `~/.claude/rules/commit-message.md` が APM 配備されることを確認 (push 完了後の別 PC、または basic を直接ローカル参照する一時手順で検証)
4. **dotfiles 側 cleanup**:
   - `dotfiles/claude/profiles/*/rules/commit-message.md` を 5 PC 分削除 (= 5 ファイル)
   - `dotfiles/claude/mise/scripts/link.sh` の `symlink_targets=(CLAUDE.md custom-config rules)` から `rules` を除外
   - `dotfiles/claude/mise.toml` `[tasks.create_profile]` の `mkdir -p "$PROFILE_PATH/rules"` と「rules を編集してね」案内を削除
5. Codex/Gemini で `AGENTS.md`/`GEMINI.md` に commit-message ルールが fold される位置と量を実機確認 (本文先頭に追加されるか、末尾か、separator が入るか)

### 8.3 target 別の挙動差への配慮

- Claude/Cursor/Windsurf は **per-file `rules/` dir** で配備されるので、既存の workflow (commit 時に Claude が rules を参照する流れ) は無修正で動く。
- Codex/Gemini は **本体 `AGENTS.md`/`GEMINI.md` に inline fold** されるため、ファイルサイズが膨らむ。複数 instructions package を入れた場合の競合や order 問題は実機で要検証。
- 当面は **`commit-message` 1 件のみ** APM 化し、副作用が少ないことを確認してから他のルール (将来追加するもの) も APM 化するか判断。

### 8.4 dependencies

- `#main` 恒常運用方針 (§9 ADR) と独立。
- custom catalog 統合 (project/work/respond-pr の所属確定) と独立 (custom には入れず basic に置くため)。
- PS package drift 防止 (drift-prevention-plan.md) と無関係 (instructions は prompt+skill 両建て構造ではない)。

### 8.5 進捗 (2026-05-28)

| step                                                | 状態                                                                      |
| --------------------------------------------------- | ------------------------------------------------------------------------- |
| 1. `agent-package-basic` に `commit-message` 新設   | 別 PC で `124c39e` として origin/main 反映済                              |
| 2. Caromaf へ push                                  | 完了 (別 PC が実施)                                                       |
| 3. 5 PC public profile に `commit-message` 依存追加 | 5 profile (cg-m2-mac/hm-m1-mac/win-15034/wsl-ubuntu/xsv-linux-1) に追加済 |
| 4. `mise run install` で APM 配備検証               | ✅ **完了** (suffix 修正後に成功、§8.6)                                   |
| 5. dotfiles 側 cleanup (5 ファイル削除 + link.sh)   | ✅ **完了** (§8.6)                                                        |
| 6. Codex/Gemini fold 副作用検証                     | **不要** (Codex/Gemini には配備しない決定、§8.6)                          |

### 8.6 真因と解決: filename suffix 欠落だった (2026-05-29 訂正)

> **訂正注記**: 旧 §8.6 は「APM 0.14.2 は user-scope instructions を deploy しない仕様」と結論していたが、これは **誤り**。真因は **catalog package 側の filename / frontmatter 不備**で、修正後は `apm install -g` で Claude に正常 deploy された。以下は訂正後の確定知見。

#### 真因 (2 つ)

1. **instruction file 名の suffix 欠落**: `commit-message.md` だった。APM は instruction primitive を **`.instructions.md` suffix** で識別するため、`commit-message.instructions.md` でないと primitive として認識されず (`apm compile --validate` が `0 instructions`)、`apm install` の `deployed_files` がゼロになる。旧 §8.6 の観測事実 #1 は file 名が `.md` であることを記録していたが、それが原因とは繋げられていなかった。
2. **frontmatter `description` 欠落**: instructions は `description` (必須) + `applyTo` (必須)。
   `description` が無いと認識されない。

#### 修正と確認

- `Caromaf/agent-package-basic` の commit `2620c0b` で `commit-message.md` → `commit-message.instructions.md` に rename + `description` 追加。
- `apm compile --validate` が `1 instructions` を返すことを確認 (rename 前は `0`)。
- 修正後 `apm install -g --frozen` で **`1 rule(s) integrated -> .claude/rules/`** と出力され、`~/.claude/rules/commit-message.md` が real dir に配備された (frontmatter は `applyTo: "**"` → Claude 用 `paths:` 形式に自動変換)。

#### 確定した配備状態

| Target             | commit-message instruction                    | 手段                                                        |
| ------------------ | --------------------------------------------- | ----------------------------------------------------------- |
| **Claude**         | ✅ `~/.claude/rules/commit-message.md` に配備 | `apm install -g` (suffix 修正後)                            |
| **Codex / Gemini** | ❌ 配備しない (**意図的決定**)                | compile 必須 + AGENTS.md/GEMINI.md symlink 衝突のため見送り |

- §8.5 step 4 (配備検証): ✅ **完了** (suffix 修正後に成功)
- §8.5 step 5 (dotfiles cleanup): ✅ **完了** — `claude/profiles/*/rules/commit-message.md` 5 件削除 + `link.sh` の `symlink_targets` から `rules` 除去 + `create_profile` の `rules/` 作成削除。
- §8.5 step 6 (Codex/Gemini fold 検証): **不要** — 決定により Codex/Gemini には配備しない。

#### Codex/Gemini を見送る理由 (意図的決定)

instructions は Claude/Cursor では `apm install` で file 配備されるが、**Codex/Gemini は `apm compile` で AGENTS.md/GEMINI.md に統合する設計**で、以下の理由から見送った:

1. `apm compile` に `-g`/`--global` が無い (project-local のみ)
2. `~/.codex/AGENTS.md` / `~/.gemini/GEMINI.md` は link.sh の symlink → compile が dotfiles 汚染
3. AGENTS.md / GEMINI.md は手書き資産で、compile (生成・上書き) と衝突
4. commit-message は安定した個人ルールで、2 ソース管理の drift コストに見合わない

→ instructions primitive の詳細な作法・落とし穴は **[instructions-primitive.md](./instructions-primitive.md)** を参照。

---

## 9. 方針転換ログ (ADR)

「過去にどう決めて、何を理由にひっくり返したか」の記録 (旧 ONBOARDING.md §11 から移設)。
再度方針転換する可能性があるので決定の文脈を保存する。設計の試行錯誤の詳細は §1 も参照。

### 9.1 primitive 戦略: Option A (skill 単一化) → ハイブリッド (PS/-S)

- **旧 (Option A)**: 全 command を skill primitive に単一化、`/slash` UI を捨てる。根拠は「APM prompt が Codex に届かない (§instructions) ため Codex カバーには skill 必須。両建ては重複コストなので嫌」。
- **新 (ハイブリッド)**: PS (prompt + skill 両建て) と -S (skill のみ) を併用。
- **転換理由**: 引数を取る `/respond-pr` / `/review-pr` 等、`/slash` 明示起動の UX 価値が「重複コスト」より大きいと再評価。両建ての本文 drift 防止策は drift-prevention-plan.md。

### 9.2 配置場所: dotfiles 内 (`dotfiles/agents/`) → 別 public repo

- **旧**: `dotfiles/agents/` (private、dotfiles 内一体管理)。
- **新**: `Caromaf/agent-package-basic` (public、MIT、独立 repo)。
- **転換理由**: skill catalog は汎用資産で他人にも使ってもらえる / public/private 境界の明確化で secret 流出リスクを構造的に低減 / npm·cargo 型 OSS catalog パターンで GitHub 機能を活用。
- **代償**: 新 PC セットアップが「dotfiles clone + agent-package install」の 2 手順に増える
  (`apm install -g` 1 コマンドなので実害小)。

### 9.3 配備方式: 二段 (mise/symlink) → 一段 (`apm install -g`)

- **旧**:「APM repo-local 生成 → mise/symlink で `~/.claude/skills/` 等に global 配備」の二段。
  根拠は WebFetch 調査時点で `apm install -g` の skill 配備動作が未確認だったため。
- **新**: `apm install -g` 直接 global の一段配備。
- **転換理由**: 実機検証で skill が `~/.claude/skills/` `~/.codex/skills/` に正常配備されることを確認
  (with-codex-skills が絶対パス参照で動作)。二段構成は overengineering と判断。

### 9.4 パッケージ粒度: flat skills dir + profile subset → 1-package-per-skill (monorepo)

- **旧**: `dotfiles/agents/skills/<n>/SKILL.md` を flat に並べ profile apm.yml で subset 宣言。
- **新**: `packages/<n>/{apm.yml, .apm/skills/<n>/...}` — 1 package = 1 skill が独立した APM package。
- **転換理由**: public OSS 化に伴い「単独 install 可能」が要件化 / semver tag を package 単位で切れる
  構造を確保 (現運用は `#main`) / CI·lint·lock の粒度が細かく診断容易。
- **subset 機構**: 廃止せず downstream `profiles/<machine>/apm.yml` の `dependencies.apm:` で表現。

### 9.5 deploy target: auto-detect 任せ → `targets:` 明示

- **旧**: consumer apm.yml で `targets:` 省略、APM の auto-detect (home dir `~/.<tool>/` 存在で検出) に任せる。
- **新**: 5 PC profile すべてで `targets: [claude, codex, gemini, copilot, cursor]` を明示。
- **転換理由**: `mise run update` (= `apm install -g --refresh --force`) 実行時に `targets:` 未指定で
  エラーが出た記録があり明示記法に切替 (当時の挙動。現 APM 版で再現するかは未検証)。
- **副次効果**: profile を読むだけで「この PC はどの CLI 向けか」が宣言的に分かる。

### 9.6 skill 配備 flag: `--legacy-skill-paths --exclude agent-skills` → default

- **旧**: per-tool 配備強制 + cross-tool 抑制で Codex 2 重発火を回避。
- **新**: flag なし (`apm install -g --frozen` のみ)。
- **転換理由**: 再検証で Codex/Gemini が cross-tool (`~/.agents/skills/`) を読むと判明し、
  default でも全員動くと確認。3 段の対症療法が default 化で全部解消。詳細は apm-behavior-reference.md §4。

### 9.7 instructions deploy: 「APM 制約で不可」→ filename 修正で Claude 可能

- **旧 (§8.6 旧版)**: `apm install -g` が user-scope instructions を deploy しない APM の仕様と結論。
- **新**: 真因は package 側の filename suffix (`.instructions.md`) + `description` 欠落。修正後 Claude に配備成功。
- **転換理由**: `apm compile --validate` で `0 instructions` を確認し原因切り分け → filename 修正で `1 instructions`。
  Codex/Gemini は compile 必須 + symlink 衝突のため意図的に見送り (§8.6)。

---

## 関連ドキュメント

- [README.md](../README.md) — 新設計の登場人物と原則
- [sync-guide.md](./sync-guide.md) — 日常運用、マシン間同期、トラブルシュート
- [apm-behavior-reference.md](./apm-behavior-reference.md) — APM の実挙動リファレンス (skill 配備・flag・物理制約)
- [instructions-primitive.md](./instructions-primitive.md) — instructions primitive の作法と落とし穴
- [drift-prevention-plan.md](./drift-prevention-plan.md) — PS package の prompt↔skill drift 防止
