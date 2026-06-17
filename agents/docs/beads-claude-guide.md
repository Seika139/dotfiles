# beads + Claude Code 運用ガイド

最終確認: 2026-06-17
対象マシン: `hm-m1-mac`, `xsv-linux-1`

[beads](https://github.com/gastownhall/beads) は、AI coding agent 向けの distributed graph issue tracker である。CLI 名は `bd`。Dolt を内部 DB として使い、Markdown の TODO / PLAN ではなく、依存関係付き issue graph と永続メモリを agent に渡す。

このドキュメントは、Claude Code は日常的に使っているが beads は初めて、という前提で、導入から通常作業までをまとめる。Codex 版ガイド ([beads-codex-guide.md](beads-codex-guide.md)) との最大の違いは統合方式で、beads の Claude Code 統合は **skill を使わず `SessionStart` hook + `bd prime` で context を注入する**。この差が §2 以降の判断をすべて左右する。

> このマシン (現在の作業環境) には beads を入れない。このガイドは `hm-m1-mac` / `xsv-linux-1` など別マシンで使うための準備である。

## 1. beads が担当するもの

beads は「作業状態」を持つ。

- `bd ready`: 依存が解けていて今着手できる issue を出す
- `bd show <id>`: issue の詳細、受け入れ条件、履歴を見る
- `bd update <id> --claim`: assignee を自分にし status を in_progress にして atomically claim する (複数 agent の衝突回避、冪等)
- `bd close <id>`: 完了を記録する
- `bd remember "..."`: 次回以降の agent session に渡すプロジェクト記憶を残す
- `bd dolt pull` / `bd dolt push`: Dolt remote 経由で issue DB を同期する

Claude Code は「実装 worker」として動き、beads は「work queue / memory / dependency graph」として働く。`agmsg` が agent 間メッセージ transport なら、beads は loop engineering の状態管理レイヤである。

## 2. dotfiles の Claude 設定管理との関係 (最重要)

ここが Codex 版と判断が分かれる箇所なので先に押さえる。

beads の Claude 統合は、`bd setup claude` で **`SessionStart` hook を入れて起動時に `bd prime` を実行させる** のが本体である。Codex 版のように `.agents/skills/beads/` を作る skill 配備ではないため、APM が管理する `~/.agents/skills/` との drift 衝突は起きない。

代わりに衝突点が `settings.json` に移る。`bd setup claude` は **デフォルトで global インストール**で、`~/.claude/settings.json` を直接書き換える。ところがこの dotfiles では `~/.claude/settings.json` は `claude/profiles/<machine>/settings.json` から配置 (link) して管理する実ファイルである。global 版で hook を足しても、次回の profile 再配置や drift 検出で **その hook が消える / 上書きされる**。

したがって Claude では以下を推奨する。

- `bd` CLI はマシンに通常インストールする
- 各 repository では `bd init` と **`bd setup claude --project`** を使う (project scope = `.claude/settings.local.json` に hook が入り、`~/.claude/settings.json` を触らない)
- `bd setup claude` (引数なし = global) は最初は使わない
- global hook をどうしても常用したくなったら、`bd setup claude --check` で生成される `SessionStart` hook 定義を読み取り、**`claude/profiles/<machine>/settings.json` 側に手で取り込む** (profile が source of truth なので、そこに書かないと再配置で消える)

`bd setup claude --project` は repository 内に閉じるので、dotfiles の profile 管理 (= APM の責務範囲表で「APM が引き受けない / 各ツール link.sh の責務」とされる `settings.json` 領域) と干渉しない。まずはこちらを使う。

## 3. インストール (`bd` CLI)

### macOS

Homebrew が一番単純。

```bash
brew install beads
bd version
```

dotfiles 側の mise に寄せたい場合は GitHub release backend を使う。mise の org/repo path は `gastownhall/beads`。

```bash
mise install github:gastownhall/beads
mise use -g github:gastownhall/beads
bd version
```

### Linux

Linuxbrew が使えるなら mac と同じ。

```bash
brew install beads
bd version
```

Homebrew を入れない場合は mise を使う。

```bash
mise install github:gastownhall/beads
mise use -g github:gastownhall/beads
bd version
```

npm エコシステムに寄せるなら npm package もある (package 名は `@beads/bd`)。

```bash
npm install -g @beads/bd
bd version
```

公式 install script もあるが、curl pipe bash は供給網リスクが上がるため、通常運用では Homebrew か mise を優先する。

```bash
curl -fsSL https://raw.githubusercontent.com/gastownhall/beads/main/scripts/install.sh | bash
bd version
```

install script は release archive を `checksums.txt` で検証する設計だが、手動 install の場合は release の `checksums.txt` で自分で検証する。

> 補足: `go install` で入れる場合、module path は repository の表示名 `gastownhall/beads` ではなく **`github.com/steveyegge/beads/cmd/bd@latest`** である (embedded Dolt を使うなら `CGO_ENABLED=1 GOFLAGS=-tags=gms_pure_go`)。混乱しやすいので Homebrew / mise を優先する。

## 4. repository 初期化

対象 repository で一度だけ実行する。

```bash
cd /path/to/repo
bd init
bd setup claude --project
bd setup claude --check
```

`bd init` は `.beads/` を作成する。通常は embedded Dolt mode になり、外部 server は不要。git remote `origin` がある repo では Dolt remote も自動設定される。

`bd setup claude --project` は Claude Code 向けに以下を作る (project scope)。

- `.claude/settings.local.json` に `SessionStart` hook を追加 (session 開始時・resume 時・compaction 後に `bd prime` を実行して ~1-2k token の workflow context を注入する)
- project root の `CLAUDE.md` に最小限の beads セクションを追記 (`bd prime` を読むよう促す。安全な再更新のため hash / version マーカー付き)

skill や slash command は作らない (beads の Claude 統合は CLI + hook 方式を採り、skill / MCP server は冗長として明示的に使わない)。

既に Claude Code session を開いている場合は、setup 後に session を再起動して hook を読み込ませる。

確認・撤去のフラグ。

```bash
bd setup claude --check     # 導入状態を確認
bd setup claude --remove    # hook を撤去
bd setup claude --stealth   # flush のみ、git 操作なし
```

## 5. 新しい作業を beads に登録する

人間が issue を作る場合。

```bash
bd create "Fix login redirect after token expiry" -t bug -p 1 \
  --description "Token expiry after Microsoft login can redirect to a blank page." \
  --acceptance "Expired-token login returns to /login and preserves next URL."
```

agent が扱いやすい issue には、以下を入れる。

- `title`: 1 つの成果物が分かる短いタイトル
- `description`: 背景と現象
- `acceptance`: 完了条件
- `design`: 実装方針がある場合だけ
- `notes`: 調査メモ、制約、リンク

依存関係がある場合。

```bash
bd create "Add token expiry regression test" -t task -p 2
bd dep add <child-id> <parent-id>
```

この関係により、`parent-id` が open の間は `child-id` が `bd ready` に出なくなる。

## 6. Claude Code session の基本フロー

`bd setup claude --project` を入れた repo では、session 開始時に hook が `bd prime` を自動実行する。Codex 版のように「まず bd prime を読んで」と毎回指示する必要はない。残るのは pull / 選択 / claim / close の運用だけなので、最小プロンプトはこうなる。

```text
この repo は beads を使っています。
remote sync している repo なら最初に bd dolt pull してください。
bd ready --json で次に実行可能な issue を 1 件選び、
bd show <id> --json を確認してから bd update <id> --claim してください。
実装と検証が終わったら bd close で状態を更新してください。
Markdown TODO は作らず、追加作業は bd create で登録してください。
```

Claude が実際に行う流れ。

```bash
bd dolt pull        # remote sync している repo の場合
# SessionStart hook が bd prime を実行済み。手動で見たいときだけ:
bd prime
bd ready --json
bd show <id> --json
bd update <id> --claim

# 実装、lint、test

bd close <id> "Implemented and verified"
bd remember "この repo では API tests は mise run test:api で実行する"
bd dolt push        # remote sync している repo の場合
```

作業途中で新しい問題を見つけた場合は、手元の Markdown に残さず beads に入れる。

```bash
bd create "Add missing validation for empty title" -t bug -p 2 \
  --description "Found while working on <parent-id>." \
  --acceptance "Empty title returns 400 and regression test exists."
bd dep add <new-id> <parent-id>
```

## 7. worktree / multi-agent での使い方

複数 agent を並列に動かす場合、beads の claim を lock として扱う。Claude Code には既存の `delegate-worktrees` / `solve-issue` skill があるので、これらと beads issue ID を接続する。

1. 親 agent が `bd ready --json` で候補を出す
2. 各 worker が自分の issue を `bd update <id> --claim` する
3. worker ごとに git worktree / branch を分ける (`delegate-worktrees` の作業単位を beads issue ID に揃える)
4. 完了時に `bd close <id>` する
5. 親 agent が PR / merge / sync 状態を確認する

`solve-issue` skill は GitHub Issue 起点のワークフローだが、beads を導入した repo では source of truth が二重になる。beads issue を細かい worker task の source of truth にし、外部共有が必要な大きい単位だけ GitHub Issue / PR に出すのが扱いやすい。loop engineering の Worker (`ai-auto` + `loop-approved` の自動処理) を beads queue で回す場合も、`bd ready --json` を入口にして `solve-issue` 相当の実装〜PR を回す形にする。

## 8. sync とバックアップ

beads の source of truth は Dolt DB である。`.beads/issues.jsonl` は viewer / migration / interchange 用の export であり、完全な backup ではない。

通常の同期。

```bash
bd dolt pull
bd dolt push
```

新しい clone で Dolt history を取得する (CI / 非対話なら `--yes`)。

```bash
bd bootstrap
bd bootstrap --yes      # 確認プロンプトを飛ばす
```

backup が必要な場合。

```bash
bd backup init /path/to/backup
bd backup sync
```

`hm-m1-mac` と `xsv-linux-1` で同じ repo を触るなら、session 開始時に `bd dolt pull`、終了時に `bd dolt push` を習慣化する。

## 9. よく使うコマンド一覧

```bash
bd init                         # repo に beads DB を作る
bd setup claude --project       # project-level Claude Code integration を入れる
bd setup claude --check         # integration の状態確認
bd setup claude --remove        # hook を撤去
bd prime                        # agent workflow context と memory を出す (hook が自動実行)
bd ready                        # 今着手できる issue を出す
bd ready --json                 # agent 用 JSON 出力
bd show <id>                    # issue 詳細
bd show <id> --json             # agent 用 JSON 出力
bd create "Title" -t task -p 2  # issue 作成
bd update <id> --claim          # assignee=自分・status=in_progress で claim (冪等)
bd update <id> --notes "..."    # 調査メモ追記
bd close <id> "Done"            # 完了
bd remember "..."               # project memory を保存
bd dep add <child> <parent>     # parent が child を block する
bd dolt pull                    # Dolt remote から issue DB を pull
bd dolt push                    # Dolt remote へ issue DB を push
bd bootstrap                    # fresh clone で Dolt history を取得
```

AI agent では `bd edit` を使わない。interactive editor が開くため、`bd update` の flags を使う。

## 10. 導入判断

まず beads + `bd setup claude --project` だけで十分である。beads の Claude 統合は hook + `bd prime` で完結し、skill を必要としない設計なので、APM package を新設して beads の使い方を再説明するのは二重管理になる。

それでも APM skill を作るなら、責務を以下の薄い bridge に絞る。

- `.beads/` がある repo でだけ発火する
- 着手前に `bd update <id> --claim` する
- 完了時に `bd close` / `bd remember` / `bd dolt push` を促す
- `solve-issue` / `delegate-worktrees` と beads issue ID を接続する

`bd prime` 注入は hook が担うので、bridge skill で prime を再実装しないこと。global hook を常用したい場合だけ、§2 の通り `claude/profiles/<machine>/settings.json` への手取り込みを検討する。

## 参考

- beads README: <https://github.com/gastownhall/beads>
- beads docs: <https://gastownhall.github.io/beads/>
- Agent / IDE setup: <https://github.com/gastownhall/beads/blob/main/docs/SETUP.md>
- Claude Code integration: <https://github.com/gastownhall/beads/blob/main/docs/CLAUDE_INTEGRATION.md>
- Installing bd: <https://github.com/gastownhall/beads/blob/main/docs/INSTALLING.md>
- CLI reference: <https://github.com/gastownhall/beads/blob/main/docs/CLI_REFERENCE.md>
- Sync concepts: <https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md>
