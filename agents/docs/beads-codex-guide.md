# beads + Codex 運用ガイド

最終確認: 2026-06-17
対象マシン: `hm-m1-mac`, `xsv-linux-1`

[beads](https://github.com/gastownhall/beads) は、AI coding agent 向けの distributed graph issue tracker である。CLI 名は `bd`。Dolt を内部 DB として使い、 Markdown の TODO / PLAN ではなく、依存関係付き issue graph と永続メモリを agent に渡す。

このドキュメントは、Codex は使ったことがあるが beads は初めて、という前提で、導入から通常作業までをまとめる。Claude Code で同じことをする場合は統合方式が異なる (skill ではなく `SessionStart` hook + `bd prime`) ので、[beads-claude-guide.md](beads-claude-guide.md) を参照する。

## 1. beads が担当するもの

beads は「作業状態」を持つ。

- `bd ready`: 依存が解けていて今着手できる issue を出す
- `bd show <id>`: issue の詳細、受け入れ条件、履歴を見る
- `bd update <id> --claim`: 作業を claim し、複数 agent の衝突を避ける
- `bd close <id>`: 完了を記録する
- `bd remember "..."`: 次回以降の agent session に渡すプロジェクト記憶を残す
- `bd dolt pull` / `bd dolt push`: Dolt remote 経由で issue DB を同期する

Codex は「実装 worker」として動き、beads は「work queue / memory / dependency graph」として働く。`agmsg` が agent 間メッセージ transport なら、beads は loop engineering の状態管理レイヤである。

## 2. dotfiles/agents との関係

この dotfiles では APM が user-scope の `~/.agents/skills/` を管理している。
beads の `bd setup codex --global` も `~/.agents/skills/beads/` を作るため、そのまま使うと APM の drift 検出と衝突する可能性がある。

当面の推奨は以下。

- `bd` CLI はマシンに通常インストールする
- 各 repository では `bd init` と `bd setup codex` を使う
- `bd setup codex --global` は最初は使わない
- global setup を使いたくなったら、APM 側で `beads` を外部 tool として扱うか、beads 用 APM package / bridge skill を別途設計する

project install の `bd setup codex` は repository 内の `.agents/skills/beads/` と `AGENTS.md` / `.codex/` を更新する。これは dotfiles の user-scope APM 管理とは別なので、まずはこちらを使う。

## 3. インストール

### macOS

Homebrew を使うのが一番単純。

```bash
brew install beads
bd version
```

dotfiles 側の mise に寄せたい場合は、beads 公式 docs にある GitHub release backend でもよい。

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

Homebrew を入れない場合は mise か install script を使う。

```bash
mise install github:gastownhall/beads
mise use -g github:gastownhall/beads
bd version
```

公式 install script もあるが、curl pipe bash は供給網リスクが上がるため、通常運用では Homebrew か mise を優先する。

```bash
curl -fsSL https://raw.githubusercontent.com/gastownhall/beads/main/scripts/install.sh | bash
bd version
```

beads の install script は release checksum を検証する設計だが、手動 install の場合は release の `checksums.txt` で検証する。

## 4. repository 初期化

対象 repository で一度だけ実行する。

```bash
cd /path/to/repo
bd init
bd setup codex
bd setup codex --check
```

`bd init` は `.beads/` を作成する。通常は embedded Dolt mode になり、外部 server は不要。
git remote `origin` がある repo では、Dolt remote も自動設定される。

`bd setup codex` は Codex 向けに以下を作る。

- `.agents/skills/beads/SKILL.md`
- `.agents/skills/beads/agents/openai.yaml`
- project `AGENTS.md` の beads 管理セクション
- `.codex/config.toml`
- `.codex/hooks.json` などの hook 設定

既に Codex session を開いている場合は、setup 後に Codex を再起動する。

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

## 6. Codex session の基本フロー

Codex に渡す最小プロンプト例。

```text
この repo は beads を使っています。
まず bd prime を読んで、bd dolt pull が必要なら実行してください。
bd ready --json で次に実行可能な issue を 1 件選び、
bd show <id> --json を確認してから bd update <id> --claim してください。
実装と検証が終わったら bd close か bd update で状態を更新してください。
Markdown TODO は作らず、追加作業は bd create で登録してください。
```

Codex が実際に行う流れ。

```bash
bd dolt pull        # remote sync している repo の場合
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

複数 agent を並列に動かす場合、beads の claim を lock として扱う。

1. 親 agent が `bd ready --json` で候補を出す
2. 各 worker が自分の issue を `bd update <id> --claim` する
3. worker ごとに git worktree / branch を分ける
4. 完了時に `bd close <id>` する
5. 親 agent が PR / merge / sync 状態を確認する

`delegate-worktrees` skill と併用する場合、beads issue ID を worker の作業単位にする。
GitHub Issue を使う既存フローとは排他ではないが、状態の source of truth が二重になる。
beads を導入した repo では、細かい worker task は beads に寄せ、外部共有が必要な大きい単位だけ GitHub Issue / PR に出すのが扱いやすい。

## 8. sync とバックアップ

beads の source of truth は Dolt DB である。`.beads/issues.jsonl` は viewer / migration / interchange 用の export であり、完全な backup ではない。

通常の同期。

```bash
bd dolt pull
bd dolt push
```

新しい clone で Dolt history を取得する。

```bash
bd bootstrap
```

backup が必要な場合。

```bash
bd backup init /path/to/backup
bd backup sync
```

hm-m1-mac と xsv-linux-1 で同じ repo を触るなら、session 開始時に `bd dolt pull`、終了時に `bd dolt push` を習慣化する。

## 9. よく使うコマンド一覧

```bash
bd init                         # repo に beads DB を作る
bd setup codex                  # project-level Codex integration を入れる
bd setup codex --check          # Codex integration の状態確認
bd prime                        # agent workflow context と memory を出す
bd ready                        # 今着手できる issue を出す
bd ready --json                 # agent 用 JSON 出力
bd show <id>                    # issue 詳細
bd show <id> --json             # agent 用 JSON 出力
bd create "Title" -t task -p 2  # issue 作成
bd update <id> --claim          # 作業を claim
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

まず beads だけで十分である。追加の APM skill を作るなら、beads の使い方を再説明するものではなく、この dotfiles の loop worker に合わせた薄い bridge にする。

bridge skill を作る場合の責務は以下に絞る。

- `.beads/` がある repo でだけ発火する
- session 開始時に `bd prime` と `bd ready --json` を読む
- 着手前に `bd update <id> --claim` する
- 完了時に `bd close` / `bd remember` / `bd dolt push` を促す
- `solve-issue` / `delegate-worktrees` と beads issue ID を接続する

最初から大きい skill を作ると beads 公式 setup と二重管理になる。まずは project ごとに `bd init` + `bd setup codex` で使い、実運用で足りない部分だけ bridge 化する。

## 参考

- beads README: <https://github.com/gastownhall/beads>
- beads docs: <https://gastownhall.github.io/beads/>
- Agent / IDE setup: <https://github.com/gastownhall/beads/blob/main/docs/SETUP.md>
- Installing bd: <https://github.com/gastownhall/beads/blob/main/docs/INSTALLING.md>
- Sync concepts: <https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md>
