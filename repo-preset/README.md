# repo-preset

既存の git repo に、lint/format 設定や mise タスクなどの「プリセット」を領域単位で導入するための素材置き場です。

導入ツールの本体は `mise/scripts/repo-preset/` にあり、`mise run repo-preset-install` から呼び出します。
この `repo-preset/components/` はそのツールが読み込むデータソース（設定ファイル・メタデータ・断片）を提供します。

## 設計方針

- **mise 中心**: 依存ツールのバージョンは各コンポーネントの `mise.fragment.toml` の `[tools]` に集約し、導入時に 1 つの `mise.toml` へマージする。lint/format も mise タスクとして実行する。
- **rust ベース優先**: dprint / rumdl / taplo / typos / shfmt など高速な rust 製ツールを優先採用する。node 依存 (markdownlint-cli2 / cspell / textlint) は `js` 基盤コンポーネント経由で導入する。
- **領域単位のコンポーネント**: python / markdown / toml / yaml / shell / spell / github などの領域ごとに分割し、必要なものだけを選ぶ。
- **推移的依存の自動解決**: 各コンポーネントは `DEPENDS_ON` で他コンポーネントへの依存を宣言する。例えば `markdown` を選ぶと node/pnpm 基盤の `js` が自動で引き込まれる。

## クイックスタート

```bash
# 対話選択 (TTY + fzf) でカレントの git repo に導入
mise run repo-preset-install

# 領域を明示指定
mise run repo-preset-install --components markdown,shell,toml

# 別ディレクトリを対象に
mise run repo-preset-install --target ./my-repo --components python,github

# main への commit/push を禁止する pre-commit を採用
mise run repo-preset-install --components shell --main-guard

# 何が起きるかだけ確認 (書き込みなし)
mise run repo-preset-install --components markdown --dry-run
```

`mise run repo-preset-install --help` で全フラグを確認できます。

## フラグ

| フラグ                 | 内容                                                                    |
| ---------------------- | ----------------------------------------------------------------------- |
| `--target <dir>`       | 導入先。デフォルトはカレントディレクトリ                                |
| `--components <csv>`   | 導入する領域をカンマ区切りで指定 (非対話)                               |
| `--all`                | 選択可能な全コンポーネントを導入                                        |
| `--main-guard`         | pre-commit の guard 版 (main への commit/push 禁止) を採用              |
| `--dry-run`            | 書き込みを一切行わず、予定を表示する                                    |
| `--force`              | 既存ファイルがあっても上書きする (デフォルトは skip)                    |
| `--offline`            | `mise install` / `uv add` / `pnpm add` などネットが必要な処理を省略     |
| `--no-install`         | ファイル生成のみ行い、`mise install` / post_scaffold の実行系をスキップ |
| `--github-user <name>` | プレースホルダ `{{github_user}}` に使う値                               |

対象は既存 git repo である必要があります (pre-commit / git-secrets が git を必須とするため)。
非 git ディレクトリを指定するとエラーで停止します。

## コンポーネント一覧

| コンポーネント | 依存 (`DEPENDS_ON`) | 内容                                                         |
| -------------- | ------------------- | ------------------------------------------------------------ |
| `_common`      | `pre-commit`        | `.editorconfig` / `.gitattributes` / `.gitignore` (常に導入) |
| `pre-commit`   | —                   | pre-commit + git-secrets。lint/format/secret scan を束ねる   |
| `python`       | —                   | uv + ruff + mypy + pytest                                    |
| `markdown`     | `js`                | dprint + rumdl + markdownlint-cli2                           |
| `textlint`     | `markdown`, `js`    | 日本語文章の lint (opt-in)                                   |
| `toml`         | —                   | taplo                                                        |
| `yaml`         | —                   | yamllint                                                     |
| `shell`        | —                   | shfmt + shellcheck                                           |
| `spell`        | `js`                | typos + cspell                                               |
| `github`       | —                   | CODEOWNERS / dependabot                                      |
| `js`           | — (`HIDDEN`)        | node + pnpm 基盤。単独では選べず依存として引き込まれる       |
| `claude`       | —                   | AGENTS.md / CLAUDE.md                                        |
| `devcontainer` | —                   | `.devcontainer/devcontainer.json`                            |

## 導入時の処理フロー

1. コンポーネント選択 (fzf 対話 / `--components` / `--all`)
2. `DEPENDS_ON` を推移的に辿って最終的なコンポーネント集合を確定 (`_common` は常に先頭)
3. 各コンポーネントの設定ファイルを target にコピー
4. `.gitignore` を基底 + 各コンポーネントの `.gitignore.append` で合成
5. `mise.fragment.toml` をマージして `mise.toml` を生成 (`[tools]` 統合 + 領域タスク連結 + 統合 `lint`/`fix` タスクの生成)
6. `github` 選択時は `dependabot.yml` を各領域の `dependabot.fragment.yml` から合成
7. pre-commit config を選択 (`--main-guard` で guard 版を採用)
8. プレースホルダ (`{{project_name}}` / `{{project_slug}}` / `{{github_user}}`) を置換
9. `mise install` と各コンポーネントの `post_scaffold.sh` を実行 (`mise exec` で PATH を通す)

## ディレクトリ構成

```text
repo-preset/
├── README.md
└── components/
    ├── _common/      .editorconfig / .gitattributes / .gitignore / README / .vscode
    ├── pre-commit/   .pre-commit-config.yaml (+guard版) / git-secrets 初期化
    ├── python/       pyproject.overlay.toml / uv 初期化
    ├── markdown/     dprint.json / .rumdl.toml / .markdownlint-cli2.jsonc
    ├── textlint/     .textlintrc.json
    ├── toml/         taplo.toml
    ├── yaml/         .yamllint.yml
    ├── shell/        .shfmtrc
    ├── spell/        .typos.toml / .cspell.json / .cspell/
    ├── github/       .github/CODEOWNERS / .github/dependabot.yml
    ├── js/           node + pnpm 基盤 (HIDDEN)
    ├── claude/       AGENTS.md / CLAUDE.md
    └── devcontainer/ .devcontainer/
```

各コンポーネントが持ちうるファイル:

| ファイル                  | 役割                                                                       |
| ------------------------- | -------------------------------------------------------------------------- |
| `meta.sh`                 | `DESCRIPTION` / `DEPENDS_ON` / `HIDDEN` を定義                             |
| `mise.fragment.toml`      | `[tools]` と領域タスク (`<領域>:lint` 等) を宣言。マージで `mise.toml` に  |
| 各種設定ファイル          | そのままコピーされる (`dprint.json`, `.rumdl.toml`, `taplo.toml` など)     |
| `.gitignore.append`       | `_common/.gitignore` に追記される行                                        |
| `post_scaffold.sh`        | コピー後に実行されるフック。`uv add` / `pnpm init` / pre-commit 初期化など |
| `pyproject.overlay.toml`  | python 専用。`pyproject.toml` 末尾に追記される設定                         |
| `dependabot.fragment.yml` | `dependabot.yml` の `updates:` に合成される 1 エントリ断片                 |

## コンポーネントの追加方法

1. `components/<name>/` を作る
2. `meta.sh` に `DESCRIPTION` / `DEPENDS_ON` / (必要なら) `HIDDEN=1` を書く
3. コピーしたい設定ファイルをそのまま配置する
4. 依存ツールがあれば `mise.fragment.toml` に `[tools]` と `<name>:lint` などのタスクを書く
5. 必要なら `.gitignore.append` / `post_scaffold.sh` / `dependabot.fragment.yml` を置く
6. `mise/scripts/repo-preset/tests/lib_test.sh` にテストケースを追加する

コンポーネントは `repo-preset/components/` から自動的に discover されるため、ツール本体を触る必要はありません。

## テスト

```bash
bash mise/scripts/repo-preset/tests/lib_test.sh
```

ネット接続不要なオフライン単体テストです (依存解決・設定合成・コピーの検証)。

## ツール本体の構成

```text
mise/
├── tasks/
│   └── repo-preset-install.sh   # mise run のエントリ (薄いラッパ)
└── scripts/repo-preset/
    ├── install.sh               # オーケストレーター
    ├── lib.sh                   # 純粋関数 (依存解決 / 合成 / コピー)
    ├── select.sh                # コンポーネント選択 (fzf / csv / all)
    ├── preview.sh               # fzf プレビュー (依存の可視化)
    └── tests/lib_test.sh        # 単体テスト
```
