# git hook tools

git を使った開発では特定のコマンド（commit や push）を実行する際に、任意の処理を自動で実行する「フック」を `.git/hooks/` に設定できる。
これを利用して、コミットやプッシュの前に自動でチェックを実行することができるが、複数のマシンで共有したい際に `.git/hooks/` が git 追跡対象外のため、リポジトリにフックを置くことができない。
そこで、git hook の設定をリポジトリ内で管理するためのツールが複数存在する。

| ツール                                                 | 言語    |
| :----------------------------------------------------- | :------ |
| [pre-commit](https://github.com/pre-commit/pre-commit) | Python  |
| [husky](https://github.com/typicode/husky)             | Node.js |
| lint-staged                                            | Node.js |
| [lefthook](https://github.com/evilmartians/lefthook)   | Go      |
| overcommit                                             | Ruby    |
| prek                                                   | Rust    |

ネットで調べた所感では husky が最も人気があるように見えるが、 Node.js 依存があったり lint-staged との組み合わせをするなど、設定が複雑になりがちであることから、lefthook に移行する人が多い印象を受けた。
python を使う Project なら pre-commit が候補になる。

## pre-commit

uv を使うプロジェクトなら以下のように設定する。

```bash
uv add pre-commit --dev
```

を実行し dev group に pre-commit を追加する。

```toml
[dependency-groups]
dev = ["pre-commit"]
```

`.pre-commit-config.yaml` をプロジェクトルートに作成し、フックの設定を記述する。

<details>
<summary>.pre-commit-config.yaml</summary>
<div>

```yaml
repos:
  # Basic repository hygiene checks.
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      # main への直接 commit を禁止する (変更はブランチを切って PR で行う)
      - id: no-commit-to-branch
        args: [--branch, main]
      - id: check-merge-conflict
      - id: check-added-large-files
        args: [--maxkb=10240]
      - id: check-json
        exclude: ^\.devcontainer/devcontainer\.json$
      - id: check-toml
      - id: detect-private-key
      - id: end-of-file-fixer
      - id: trailing-whitespace

  # Ruff: lint + format（Rust 製で高速）
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.16.0
    hooks:
      - id: ruff-check
        args: [--fix]
        exclude: ^apps/frontend/
      - id: ruff-format
        exclude: ^apps/frontend/

  # Ty: 型チェック（Rust 製で高速、member dir 単位で実行）
  - repo: local
    hooks:
      - id: ty
        name: ty
        entry: mise run ty
        language: system
        pass_filenames: false
        types: [python]
        exclude: ^apps/frontend/

  # YAML lint
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.38.0
    hooks:
      - id: yamllint

  # Shell script チェック
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.9.0.6
    hooks:
      - id: shellcheck
        args: [-x, -P, SCRIPTDIR]

  # Markdown lint（.markdownlint-cli2.jsonc の gitignore: true を活かすため local hook で実行）
  - repo: local
    hooks:
      - id: markdownlint-cli2
        name: markdownlint-cli2
        entry: markdownlint-cli2 --config .markdownlint-cli2.jsonc
        language: system
        types: [markdown]

  # 他にもローカルに置いたフックを追加する場合は以下のようにする。
  - repo: local
    hooks:
      - id: some-local-hook
        name: some-local-hook
        entry: >-
          bash -c 'echo "some-local-hook" && echo "$@"' --
        language: system
        pass_filenames: false
```

</div>
</details>
<br>

以下のようにして、`.pre-commit-config.yaml` の設定を `.git/hooks/` に反映させる。

```bash
uv run pre-commit install --hook-type pre-commit
uv run pre-commit validate-config # 設定ファイルの文法チェック
```

`mise.toml` などでプロジェクト初期化時のセットアップ処理に組み込むと、開発者が個別に設定する必要がなくなる。

```toml
[tasks.init]
description = "Initialize project"
quiet = true
run = '''
print_red() { printf '\e[31m%s\e[0m' "$*"; }
print_green() { printf '\e[32m%s\e[0m' "$*"; }
# Git hooks are local to each clone, so install the pre-commit launcher during
# init instead of relying on the checked-in .pre-commit-config.yaml alone.
uv run pre-commit install --hook-type pre-commit >/dev/null
uv run pre-commit validate-config >/dev/null
PRE_COMMIT_HOOK_PATH="$(git rev-parse --git-path hooks/pre-commit)"
if [ ! -x "$PRE_COMMIT_HOOK_PATH" ]; then
  print_red "✗ pre-commit hook のインストール確認に失敗しました"$'\n'
  exit 1
fi
print_green "✓ "
echo "pre-commit hook をインストールしました (${PRE_COMMIT_HOOK_PATH})"
print_green "✓ "
echo "pre-commit 設定を検証しました"
'''
```

<!-- TODO: 以下は実際に使うときに書く -->

## husky

## lefthook
