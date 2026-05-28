# Sync Guide: APM パッケージのマシン間同期と日常運用

複数の APM パッケージリポジトリを、複数マシン間で **同期して使う** ための運用手順。

> **本ドキュメントのスコープ**: APM パッケージの**導入と更新の同期**のみ。
> 旧 dotfiles からの移行手順と失敗事例は [migration-plan.md](./migration-plan.md) を参照。

---

## 1. 二層モデル

APM は 2 つの導入スコープを持つ。**この 2 層は混ぜない**ことが運用の肝。

| スコープ        | コマンド                | 展開先                                                  | 何を入れるか                                      |
| --------------- | ----------------------- | ------------------------------------------------------- | ------------------------------------------------- |
| **user-global** | `apm install -g`        | `~/.claude/commands/`, `~/.codex/prompts/` 等           | 全プロジェクトで使う汎用 + 非公開用               |
| **per-project** | `apm install` (in repo) | `<project>/.claude/commands/`, `<project>/apm_modules/` | そのプロジェクト固有のもの, **MCP server** (必須) |

### なぜ二層なのか (APM の制約)

- prompts / skills / agents / instructions は `-g` で user-global 可
- **MCP server は `-g` だと Copilot CLI / Codex CLI のみ対応**。Claude Code / Cursor 用の
  MCP は per-project install が必須 ([APM CLI ref](https://microsoft.github.io/apm/reference/cli/install/))
- **codex は user-scope で partial support**。`prompts` / `instructions` type は `-g` で
  展開されない (= `~/.codex/prompts/` には何も書かれない)

### 配布元のマッピング

| 種類                       | 配布元                                        | 導入スコープ | 例                                          |
| -------------------------- | --------------------------------------------- | ------------ | ------------------------------------------- |
| 公開可能な汎用             | `Caromaf/agent-package-basic` (public)        | user-global  | `review-pr`, `solve-issue`, `codex-review`  |
| 非公開版                   | `gi/agent-package-custom`                     | user-global  | `aws-auth`, `login-microsoft`, `project-up` |
| 将来のプロジェクト切り出し | `<owner>/<project>-apm-packages` (option、§3) | per-project  | (現状未使用、§3.1 参照)                     |

> **公開汎用 repo を `Caromaf` 配下に置く理由**: この PC からは push できない作業アカウント分離設計のため。push は別 PC で行う。

---

## 2. user-global の導入と同期

### 2.0 設計前提: なぜ `~/.apm/apm.yml` を symlink にするのか

`apm install -g` の挙動:

- マニフェストは **`~/.apm/apm.yml` 固定**で読まれる (CWD は無視される)
- lockfile は `~/.apm/apm.lock.yaml` に書かれる

したがって dotfiles で profile 別 manifest を版管理するには、`~/.apm/apm.yml` を
**`dotfiles/agents/profiles/<machine>/apm.yml` への symlink** にするしかない。

```text
~/.apm/apm.yml         → ~/dotfiles/agents/profiles/wsl-ubuntu/apm.yml      (symlink)
~/.apm/apm.lock.yaml   → ~/dotfiles/agents/profiles/wsl-ubuntu/apm.lock.yaml (symlink) [option]
~/.apm/apm_modules/    (実ディレクトリ、APM のキャッシュ)
~/.apm/config.json     (実ファイル、`{"default_client": "vscode"}` 等)
```

### 2.0.1 [重要] APM 専管 dir は実 dir に保つ

`~/.claude/commands/`, `~/.codex/prompts/`, `~/.cursor/commands/` は **絶対に symlink に
してはいけない** ([README.md §設計原則](../README.md) 参照)。新マシンセットアップ前に必ず
確認する:

```bash
ls -la ~/.claude/commands ~/.codex/prompts ~/.cursor/commands 2>/dev/null
# → "drwx..." なら OK (実 dir)
# → "lrwx..." (-> ...) なら symlink。即座に削除して mkdir し直す:
#   rm ~/.claude/commands && mkdir ~/.claude/commands
```

### 2.1 各マシンで初回セットアップ

```bash
# 1) dotfiles を clone (既存運用)
cd ~ && git clone <dotfiles-url>

# 2) APM CLI を導入
curl -sSL https://aka.ms/apm-unix | APM_INSTALL_DIR="$HOME/.local/bin" sh
apm --version

# 3) APM 専管 dir を実 dir として用意
for d in ~/.claude/commands ~/.codex/prompts ~/.cursor/commands; do
  [ -L "$d" ] && rm "$d"
  mkdir -p "$d"
done

# 4) ~/.apm/apm.yml を当該マシンの profile への symlink に
mkdir -p ~/.apm
ln -sfn ~/dotfiles/agents/profiles/wsl-ubuntu/apm.yml ~/.apm/apm.yml

# 5) gh 認証 (private repo install のため)
gh auth status     # repo scope を含むトークンが要る
                   # 無ければ: gh auth login --scopes "repo,read:org"

# 6) install
cd ~/.apm && apm install -g
```

### 2.2 プロファイル `apm.yml` の書き方

`dotfiles/agents/profiles/<machine>/apm.yml`:

```yaml
name: <machine>-profile
version: 0.1.0
description: APM profile for <machine>
author: User Name
includes: auto

dependencies:
  apm:
    # 公開汎用 (basic) — Phase 1 完了後に追加していく
    - Caromaf/agent-package-basic/packages/review-pr#main
    # ... 他の汎用パッケージ

    - gi/agent-package-custom/packages/aws-auth#main
    - gi/agent-package-custom/packages/login-microsoft#main
    - gi/agent-package-custom/packages/project-up#main
    - gi/agent-package-custom/packages/project-status#main
    - gi/agent-package-custom/packages/project-browse#main
    - gi/agent-package-custom/packages/project-investigate-logs#main
    - gi/agent-package-custom/packages/project-aws-rule#main
  mcp: [] # MCP は per-project で扱う
```

> **`#main` か `#vX.Y.Z` か**: 現状は `#main` で運用 (常に最新)。タグ運用に切り替える
> なら `#v0.1.0` 等を pin する。タグ運用は再現性が上がる代わりに、毎回 push 後にタグを
> 切る作業が増える。

### 2.3 lockfile の扱い

`apm install -g` は `~/.apm/apm.lock.yaml` を生成する。これは:

- パッケージごとに `resolved_commit` (sha) と `deployed_file_hashes` (sha256) を記録
- `--frozen` で install すると、lockfile と manifest が一致しない場合に失敗する
  (= マシン間で完全に同じ commit を強制できる)

lockfile を dotfiles で版管理するか:

| パターン                                     | メリット                             | デメリット                                    |
| -------------------------------------------- | ------------------------------------ | --------------------------------------------- |
| `~/.apm/apm.lock.yaml` を版管理しない (現状) | 運用が軽い。`#main` 参照と相性が良い | マシン間で resolved_commit がずれる可能性あり |
| dotfiles に symlink して版管理               | `--frozen` で完全な再現性            | tag を切らないと毎 push で lock 更新が必要    |

現状は前者。タグ運用に切り替えるタイミングで後者へ移行する想定。

### 2.4 パッケージを更新する

#### 公開汎用 (basic) の更新

この PC からは push 不可。別 PC で:

```bash
cd <別 PC>/agent-package-basic
$EDITOR packages/review-pr/.apm/prompts/review-pr.prompt.md
git add packages/review-pr
git commit -m "`review-pr` の手順 3 を補足"
git push origin main
```

この PC では:

```bash
cd ~/.apm && apm install -g       # main を再 fetch
```

#### 非公開版 (custom) の更新

この PC で:

```bash
cd ~/programs/apm/agent-package-custom
$EDITOR packages/aws-auth/.apm/prompts/aws-auth.prompt.md
git add packages/aws-auth
git commit -m "`aws-auth` で SSO プロファイル例を追加"
git push origin main
cd ~/.apm && apm install -g
```

---

## 3. per-project の導入と同期 (将来の選択肢)

### 3.1 現状: project は user-global に同梱

現状、project プロジェクト用の 5 packages (`project-up`, `project-status`, `project-browse`,
`project-investigate-logs`, `project-aws-rule`) は `agent-package-custom` に同梱されており、
**user-global で常時有効** な状態。project プロジェクトの外でも `/project-up` 等が見える。

これは小規模な間は問題ないが、将来:

- project 以外のプロジェクトでも APM 化したいパッケージ群が増える
- project 用 MCP server を導入したい (= per-project 必須)
- project 用 skill のバージョンをプロジェクト側で pin したい

といった要件が出たとき、project を per-project に切り出す。

### 3.2 切り出し手順 (将来案)

```bash
# 1) project 専用 repo を作る (private)
gh repo create github-user/project-apm-packages --private \
  --description "APM packages for project"

# 2) custom から project 関連を移植
cd ~/programs/apm
git clone git@github.com:gi/project-apm-packages.git
cd project-apm-packages
mkdir packages
mv ~/programs/apm/agent-package-custom/packages/project-* packages/
git add packages
git commit -m "`project` 関連パッケージを `agent-package-custom` から移管"
git tag v0.1.0
git push origin main --tags

# 3) custom 側から project を削除
cd ~/programs/apm/agent-package-custom
git rm -r packages/project-*
git commit -m "`project` 関連を `project-apm-packages` へ切り出し"
git push

# 4) dotfiles の profile から project を外す
$EDITOR ~/dotfiles/agents/profiles/wsl-ubuntu/apm.yml
# project-* の 5 行を削除

# 5) project プロジェクト側に apm.yml を作る (詳細は §3.3)
```

### 3.3 プロジェクト側の apm.yml

```yaml
name: sample-project
version: 1.0.0
description: sample project agent setup

dependencies:
  apm:
    - github-user/project-apm-packages/packages/project-up#v0.1.0
    - github-user/project-apm-packages/packages/project-browse#v0.1.0
    - github-user/project-apm-packages/packages/project-investigate-logs#v0.1.0
    - github-user/project-apm-packages/packages/project-status#v0.1.0
    - github-user/project-apm-packages/packages/project-aws-rule#v0.1.0
  mcp:
    # project で使う MCP server があればここで宣言 (per-project だから可能)
    # - microsoft/mcp-something#v1.0.0

includes: auto
```

### 3.4 per-project の install と展開先

```bash
cd ~/programs/project
apm install --frozen
```

展開先:

- `<project-repo>/.claude/commands/project-up.md` 等
- `<project-repo>/.codex/prompts/project-up.md` 等
- `<project-repo>/apm_modules/` (キャッシュ、gitignore)
- `<project-repo>/apm.lock.yaml` (commit する)

> Claude Code は project-local の `.claude/commands/` を user-global の `~/.claude/commands/` より**優先して読む**。同名 command があれば project-local が勝つので、特定のプロジェクトでだけ独自版に差し替え可能。

---

## 4. マシン間の同期チェックリスト

新しいマシンを生やす、または pull したあとに走らせる流れ:

```bash
# (1) dotfiles 同期
cd ~/dotfiles && git pull

# (2) APM 専管 dir が実 dir であることを確認
ls -la ~/.claude/commands ~/.codex/prompts ~/.cursor/commands 2>/dev/null
# symlink になっていれば: rm + mkdir で実 dir に直す

# (3) ~/.apm/apm.yml の symlink を確認
file ~/.apm/apm.yml
# "symbolic link to ..." なら OK

# (4) user-global を再展開
cd ~/.apm && apm install -g

# (5) per-project があれば各プロジェクトで
cd ~/programs/<proj> && git pull && apm install --frozen
```

---

## 5. コマンド早見表

| やりたいこと                           | コマンド                                                |
| -------------------------------------- | ------------------------------------------------------- |
| user-global を install / 更新          | `cd ~/.apm && apm install -g`                           |
| 完全な再現性で install                 | `cd ~/.apm && apm install -g --frozen`                  |
| 何が install されるか事前確認          | `cd ~/.apm && apm install -g --dry-run`                 |
| ドリフト (lockfile vs manifest) を確認 | `apm install -g --frozen` が失敗すれば食い違いあり      |
| キャッシュを無視して再取得             | `apm install -g --refresh`                              |
| `~/.apm/apm.yml` が symlink か確認     | `file ~/.apm/apm.yml`                                   |
| 展開先が実 dir か symlink か確認       | `ls -la ~/.claude/commands ~/.codex/prompts`            |
| user-scope の対応状況を見る            | `apm install -g --dry-run` 実行時の警告メッセージを読む |

---

## 6. トラブルシュート

### 6.1 [最重要] `apm install -g` 後に dotfiles repo に diff が出る

**症状**: `apm install -g` 実行後、`cd ~/dotfiles && git status` で
`claude/profiles/.../foo.md` が modified になる、または `Untracked files` に
APM パッケージのファイルが現れる。

**原因**: `~/.claude/commands/` などの APM 専管 dir が **dotfiles 配下への symlink** に
なっており、APM が symlink を辿って dotfiles repo を直接書き換えている。

**対処**:

```bash
# 1) dotfiles の汚染を復旧
cd ~/dotfiles
git restore <汚染されたファイル>
rm <APM が新規作成した未追跡ファイル>

# 2) symlink を削除して実 dir として作り直す
rm ~/.claude/commands
mkdir ~/.claude/commands
# (~/.codex/prompts, ~/.cursor/commands も同様に確認)

# 3) APM の install state をクリア
rm ~/.apm/apm.lock.yaml
rm -r ~/.apm/apm_modules

# 4) 再 install
cd ~/.apm && apm install -g
```

実例は [migration-plan.md §Phase 5](./migration-plan.md) を参照。

### 6.2 collision エラーで `apm install -g` が止まる

**症状**: `Error: file already exists at ~/.claude/commands/foo.md`

**原因**: 既存ファイルが APM の展開先と衝突している。

**対処**: 一時退避してから install。**ただし symlink でないことを確認してから `mv` する**
(symlink 相手に `mv` すると symlink 先 = dotfiles を書き換えてしまう):

```bash
ls -la ~/.claude/commands/foo.md   # symlink でないことを確認
mv ~/.claude/commands/foo.md{,.bak}
cd ~/.apm && apm install -g
# 動作確認後、不要なら .bak を削除
rm ~/.claude/commands/foo.md.bak
```

### 6.3 codex の `~/.codex/prompts/` に何も展開されない

**症状**: `apm install -g` は成功するが `~/.codex/prompts/` が空。

**原因**: APM の仕様。`prompts` / `instructions` type は **codex の user-scope では
partial support** で、deploy 対象外。

**対処**: codex で動かしたい場合は per-project install (`cd <project> && apm install`)
に回すか、codex 側の primitive type を `skills` (= `<name>/SKILL.md` 形式) に変える。

### 6.4 `~/.apm/apm.yml` が symlink ではなく実ファイルになっている

**症状**: dotfiles で `apm.yml` を編集しても `apm install -g` の挙動が変わらない。

```bash
file ~/.apm/apm.yml
# "symbolic link to ~/dotfiles/agents/profiles/.../apm.yml"  → OK
# "ASCII text"                                                → 異常
```

**対処**:

```bash
# 必要なら実ファイル側の変更を dotfiles 側にマージ
diff -u ~/dotfiles/agents/profiles/wsl-ubuntu/apm.yml ~/.apm/apm.yml

# 退避してから symlink を張り直す
mv ~/.apm/apm.yml{,.bak}
ln -sfn ~/dotfiles/agents/profiles/wsl-ubuntu/apm.yml ~/.apm/apm.yml
file ~/.apm/apm.yml
```

### 6.5 user-scope partial support 警告について

`apm install -g` 実行時に出る:

```text
[!] User-scope primitives are fully supported by claude, gemini, agent-skills, copilot-cowork, copilot-app.
    Partially supported: copilot, cursor, opencode, codex, windsurf.
Some primitives are not supported: copilot (prompts, instructions); cursor (instructions);
    opencode (hooks); windsurf (instructions); codex (prompts, instructions)
```

- `claude` は **full support** (= 全 primitive が user-scope で展開される)
- `codex` は `prompts` / `instructions` が落ちる → §6.3 の対処
- `cursor` は `commands` 系 (= `prompts` でラベル付けされたもの) は通る、`instructions` は落ちる

---

## 7. MCP server の所有権ルール (旧 ONBOARDING §5.5 から移設)

APM 0.13 の `apm mcp install` は **self-defined エントリを公式サポート**:
`apm mcp install <name> -- <stdio-command>` または `--transport http --url <URL>`。
MCP server をどこの apm.yml に書くかは **3 層所有権ルール**で決める。

| スコープ         | 例                                    | 配置先                                           | 配備手段                                |
| ---------------- | ------------------------------------- | ------------------------------------------------ | --------------------------------------- |
| プロジェクト固有 | `tlb-investment/server/mcp_stdio.py`  | `<project>/apm.yml` (per-project)                | `cd <project> && apm install`           |
| ユーザー global  | Gmail, Calendar, fetch, GitHub MCP 等 | `dotfiles/agents/profiles/<pc>/apm.yml`          | `mise run install` (= `apm install -g`) |
| OSS catalog      | (含めない)                            | `Caromaf/agent-package-basic/packages/*/apm.yml` | `dependencies.mcp: []` 固定             |

### upstream catalog に MCP を含めない理由

- skill は OS 中立だが MCP server は実行環境 (Python/Node/binary) に依存し、OSS で配布すると依存解決が複雑化する。
- secrets/設定の組織依存度が高く、汎用化の利益が薄い。
- 現 catalog 全 package は `dependencies.mcp: []` (検証済)。

### secrets 取扱いの運用ルール (apm.yml は git commit されるため)

1. **apm.yml に key/token を直書きしない**。`--env KEY=VALUE` で値を埋め込む形も避ける
   (downstream apm.yml も dotfiles に commit される)。
2. **MCP server 側で外部から自力読み取り** する設計に統一: `~/.config/<server>/`、
   macOS Keychain、`secret-tool` (Linux)、1Password CLI 等。
3. apm.yml には server 起動コマンドと transport だけ書く。
   例: `apm mcp install gmail -- /path/to/gmail-mcp-server`
   (token は server が `~/.config/gmail-mcp/token.json` から読む)。

### プロジェクト固有 MCP を user-global に格上げしない

同名 server を複数 project で使う場合でも、各 project の apm.yml に独立して書く。
MCP server の per-project スコープが Claude Code / Cursor の唯一サポート形態 (§1)。

---

## 関連ドキュメント

- [README.md](../README.md) — 登場人物と設計原則
- [migration-plan.md](./migration-plan.md) — 旧設計からの移行記録、失敗事例
- [apm-behavior-reference.md](./apm-behavior-reference.md) — APM の実挙動リファレンス
- 公式 install ref: <https://microsoft.github.io/apm/reference/cli/install/>
- 公式 consumer guide: <https://microsoft.github.io/apm/consumer/install-packages/>
