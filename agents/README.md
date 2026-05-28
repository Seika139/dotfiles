# dotfiles/agents

複数 AI agent ツール (Claude Code / Codex CLI / Cursor 等) で共通利用する **prompts / skills / instructions / agents / commands** を、[APM (Agent Package Manager)](https://microsoft.github.io/apm/) で集約管理するための dotfiles サブディレクトリ。

このディレクトリには **consumer 側の設定だけ** を置く。パッケージの本体は別の repo で管理している。

## レイアウト

```text
dotfiles/agents/
├── README.md
├── mise.toml                 # 共通 env (IS_WSL 等) のみ
├── mise.local.toml           # 各 PC のローカル設定 (.gitignore、自動生成)
├── mise/
│   └── tasks/                # install / update / status / list / check_env / migrate
└── profiles/
    ├── <machine>/
    │   ├── apm.yml           # 当該マシンで install するパッケージの宣言
    │   └── apm.lock.yaml     # install 後に生成。commit して再現性を確保
    └── private/              # 任意の overlay (詳細は §4)
        ├── apm.sample.yml    # 雛形。git-tracked
        ├── apm.yml           # active profile に重ねる private dependencies (gitignored)
        └── apm.lock.yaml     # private 込みのマージ後 lock (gitignored)
```

## 設計原則

### 1. APM 専管 dir は実 dir に保つ (重要)

これまで `~/dotfiles/{claude,codex,gemini}/` から symlink で `~/.claude/`, `~/.codex/`, `~/.cursor/` に skills などを展開していたが、本サブディレクトリで実現する apm 対応によって **APM 専管領域は symlink ではなく実ディレクトリで管理する**。

理由: APM は symlink を辿って書き込むため、`~/.claude/commands` を dotfiles 配下への symlink にしていると `apm install -g` が **dotfiles repo を直接書き換える事故** が起きるからである。

### 2. consumer manifest は dotfiles で版管理

`profiles/<machine>/apm.yml` で「このマシンに何を install するか」だけを宣言する。パッケージ本体は書かない。

### 3. 参照は外部 repo の remote ref で

```yaml
dependencies:
  apm:
    - Caromaf/agent-package-basic/packages/review-pr#main
```

絶対パス参照も技術的には可能だが、マシン横断の再現性が下がるため通常運用では使わない。

## クイックスタート (新マシン)

> 前提: `uv` (Python 環境) が導入済。merge スクリプト (PEP 723 inline metadata) を
> `uv run` 経由で実行するため必須。未導入なら:
> `curl -LsSf https://astral.sh/uv/install.sh | sh`

```bash
# 1) APM CLI を導入
# https://microsoft.github.io/apm/quickstart/#1-install-apm を参照
curl -sSL https://aka.ms/apm-unix | APM_INSTALL_DIR="$HOME/.local/bin" sh

# 2) このマシンで使う profile を決める
#    profiles/ にディレクトリが無ければ既存を雛形に作る:
#      cp -r ~/dotfiles/agents/profiles/wsl-ubuntu ~/dotfiles/agents/profiles/<machine>
#    そして dotfiles 共通の active profile を書く (check_env が読む):
echo "<machine>" > ~/dotfiles/.active-profile

# 3) APM 専管 dir (~/.claude/{commands,skills}, ~/.codex/{prompts,skills},
#    ~/.cursor/commands, ~/.gemini/skills 等) を実 dir として用意する
cd ~/dotfiles/agents && mise trust && mise run migrate

# 4) (任意) private overlay を有効化したい場合
#    cp profiles/private/apm.sample.yml profiles/private/apm.yml
#    詳細は §4

# 5) install 実行 (~/.apm/apm.yml を profile/apm.yml と同期 → apm install -g)
mise run install
```

`mise run install` は内部で:

1. `check_env` が `mise.local.toml` を必要なら自動生成 (`.active-profile` から `DEFAULT_AGENTS_PROFILE` を埋める)
2. profile の `apm.yml` / `apm.lock.yaml` を `~/.apm/` に **コピー** (symlink ではない)
3. `apm install -g [--frozen]` を user scope で実行
4. 新規生成された lock を profile/ にコピーバックして commit 候補に

を一気通貫で行う。

### 状態確認・更新

```bash
mise run status                # 現在の profile と install 状況を表示
mise run list                  # 利用可能 profile 一覧
mise run update                # apm install -g --refresh --force で最新 ref に再解決
mise run install --prof <m>    # 別 profile を一時的に当てる
```

## 4. private overlay (任意)

`profiles/private/apm.yml` を作ると、`mise run install` / `mise run update` 実行時に
**active profile の `apm.yml` に重ねて** user scope へ install できる。GitHub に push できない
private repo の package、評価用の一時 package、PC 固有の package などをここに置く。

`profiles/private/apm.yml` と `apm.lock.yaml` は `agents/.gitignore` で除外。
**`apm.sample.yml` のみ git-tracked** で、新マシンの初期化雛形として残る。

### 4.1 初期化 (PC ごと、必要なら)

```bash
cd ~/dotfiles/agents
cp profiles/private/apm.sample.yml profiles/private/apm.yml
$EDITOR profiles/private/apm.yml      # 必要な private dependencies を書く
mise run install                      # base + private がマージされて install される
```

### 4.2 仕様

`apm.yml` は overlay なので `dependencies` だけで十分:

```yaml
dependencies:
  apm:
    - <owner>/<private-repo>/packages/<pkg>#main
  mcp: []
```

挙動:

- マージ範囲は `dependencies.apm` と `dependencies.mcp` のみ。`name` / `targets` /
  `includes` 等のメタは active profile 側の値が常に優先される
- 重複 ref (完全一致) は base 側を残して dedupe される
- private 有効時、`apm.lock.yaml` は **`profiles/private/apm.lock.yaml`** にコピーバック
  される。git-tracked な `profiles/<machine>/apm.lock.yaml` には触らない (= public 側に
  private ref が漏れない)
- private を撤去したいときは `rm profiles/private/apm.yml profiles/private/apm.lock.yaml`
  してから `mise run install`。`~/.apm/apm.yml` が public 側だけのマニフェストに戻る

`mise run status` で base/overlay の dependencies が分けて表示される。

## APM の責務範囲

| APM が引き受ける                                                       | APM が引き受けない (= 各ツール側 `link.sh` の責務として残る)    |
| ---------------------------------------------------------------------- | --------------------------------------------------------------- |
| prompts / skills / agents / instructions / commands の各ツールへの展開 | `settings.json` (Claude Code) / `config.toml` (Codex)           |
| バージョン pin (`apm.lock.yaml`) と再現性                              | `CLAUDE.md` / `AGENTS.md` / `rules/` の配置                     |
| security scan (hidden Unicode 等)                                      | プロファイル選択 (`~/dotfiles/.active-profile` または `--prof`) |

## 参考

- 公式: <https://microsoft.github.io/apm/>
- Quickstart: <https://microsoft.github.io/apm/quickstart/>
- Manifest schema: <https://microsoft.github.io/apm/reference/manifest-schema/>
- Producer guide: <https://microsoft.github.io/apm/producer/>
