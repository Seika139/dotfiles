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
    └── <machine>/
        ├── apm.yml           # 当該マシンで install するパッケージの宣言
        └── apm.lock.yaml     # install 後に生成。commit して再現性を確保
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

# 4) install 実行 (~/.apm/apm.yml を profile/apm.yml と同期 → apm install -g)
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
