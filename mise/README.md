# mise

dotfiles 全体で使う mise の設定、タスク、補助スクリプトを置くディレクトリです。ここにあるファイルの役割と、読み込まれる経路をまとめます。

## ディレクトリ構成

| パス                   | 役割                                                                                    |
| :--------------------- | :-------------------------------------------------------------------------------------- |
| `profiles/`            | PC ごとのグローバルツール定義。選んだ 1 つが `~/.config/mise/conf.d/` にリンクされる    |
| `tasks/`               | `mise run` で実行できるタスク。mise が `mise/tasks/` を自動で読み込む                   |
| `scripts/repo-preset/` | `repo-preset-install` タスクの実装。コンポーネントを選んで別の git リポジトリへ導入する |

リポジトリ直下の `mise.toml` は、dotfiles リポジトリ自身の開発用ツールとタスク(`dot-init`、`dot-upgrade`、`install-git-secrets`)を定義します。`mise/` 配下のファイルはそれとは別で、PC 全体に効くツール定義と、`tasks/` と `scripts/` に置いたタスクの実装を受け持ちます。

## profiles/

PC ごとに、グローバルへ入れる mise のツールとバージョンを書いた TOML です。バージョンは固定で記載しており、更新は依存関係の更新 PR で行われてきた履歴があります。

| ファイル           | 対象                                                                   |
| :----------------- | :--------------------------------------------------------------------- |
| `default.toml`     | プロファイル未指定の環境。コメントのみで、グローバルツールを管理しない |
| `cg-m2-mac.toml`   | Mac                                                                    |
| `hm-m1-mac.toml`   | Mac                                                                    |
| `win-15034.toml`   | Windows                                                                |
| `wsl-ubuntu.toml`  | WSL の Ubuntu                                                          |
| `xsv-linux-1.toml` | Linux                                                                  |

### 選択とリンクの仕組み

1. `bash/daily/.env` の `DAILY_PROFILE=<名前>` で、使うプロファイルを決めます。未指定なら `default` になります。
2. ルートの `install.sh` が `mise/profiles/<名前>.toml` を `~/.config/mise/conf.d/dotfiles-profile.toml` へシンボリックリンクします。
3. mise は `conf.d/*.toml` を、どのディレクトリでも読み込むグローバル設定として扱います。そのため、プロファイルに書いたツールはユーザーのどの場所でも有効になります。ただしプロジェクト側の `mise.toml` があれば、その配下ではプロジェクトの指定が優先されます。
4. `unlink.sh` は、dotfiles が作ったこのリンクだけを削除します。

`install.sh` は次の場合、プロファイルを変更・導入せずに警告だけを出します。

- `DAILY_PROFILE` が 2 つ以上書かれている、または `[A-Za-z0-9_-]+` に合わない
- 指定した名前の `profiles/<名前>.toml` が存在しない、またはシンボリックリンクになっている
- `dotfiles-profile.toml` が、dotfiles 以外の場所を指すリンクや通常ファイルになっている

古い `conf.d/dotfiles-managed.toml`(`mise/global.toml` へのリンク)があれば、新しいリンクを張れたあとに削除されます。

### ツールを追加するとき

対象 PC のプロファイルの `[tools]` に追記します。別の PC に同じツールを入れたい場合は、その PC のプロファイルにも書きます。Python や Go のようにプロファイルへ書かず、`~/.config/mise/config.toml` に直接書かれているツールもあるため、実際に有効な定義は `mise config ls` で確認してください。

## tasks/

`mise/tasks/` 配下のシェルスクリプトは、ファイル名から拡張子を除いた名前のタスクになります。設定の記述は、スクリプト先頭の `#MISE` と `#USAGE` コメントで行います。

| ファイル                 | タスク名              | 役割                                                                     |
| ------------------------ | --------------------- | ------------------------------------------------------------------------ |
| `dot-format.sh`          | `dot-format`          | Markdown、シェル、TOML、YAML を自動整形する。`-t` で textlint も実行する |
| `dot-lint.sh`            | `dot-lint`            | 上記の検査だけを行い、ファイルは変更しない。`-t` で textlint も実行する  |
| `initialize.sh`          | `initialize`          | 依存の初期化。現在は `pnpm install` を実行する。一覧には表示されない     |
| `repo-preset-install.sh` | `repo-preset-install` | `scripts/repo-preset/install.sh` を呼び出す入口                          |
| `common.sh`              | `common`              | 他のタスクが `source` する共通関数。一覧には表示されない                 |

`common.sh` には、色付きの出力関数、TTY 判定(`is_tty`)、fzf の存在確認(`require_fzf`)、fzf による Yes/No 選択(`binary_choice`)があります。

`dot-format` と `dot-lint` は、途中で 1 つのチェックが失敗しても残りを続けるため、`set -e` を使っていません。シェルスクリプトの検査対象には、この `mise/tasks/` も含まれます。

新しいタスクを足す場合は、`mise/tasks/` にスクリプトを置き、実行権限を付けます。リポジトリ直下の `mise run dot-init` は、`mise/tasks/*.sh` へ実行権限を付けたうえで `initialize` を実行します。

## scripts/repo-preset/

`repo-preset-install` の実装です。選んだコンポーネントを既存の git リポジトリへ導入します。導入する素材(設定ファイルや `mise.fragment.toml` など)は `repo-preset/components/` にあり、使い方とフラグは [repo-preset/README.md](../repo-preset/README.md) にあります。

| ファイル            | 役割                                                                                            |
| ------------------- | ----------------------------------------------------------------------------------------------- |
| `install.sh`        | 全体の進行役。引数の解釈、対象リポジトリの確認、コンポーネントの選択、導入までを行う            |
| `select.sh`         | 導入するコンポーネント名を標準出力に返す。`--all`、`--components`、fzf による対話選択に対応する |
| `preview.sh`        | fzf のプレビュー欄に、コンポーネントの説明と依存を表示する                                      |
| `lib.sh`            | 副作用のない関数のライブラリ。直接は実行せず `source` して使う                                  |
| `tests/lib_test.sh` | `lib.sh` の単体テスト                                                                           |

呼び出しの流れは次のとおりです。

```text
mise run repo-preset-install
  → tasks/repo-preset-install.sh
    → scripts/repo-preset/install.sh
      → select.sh (コンポーネントの選択。対話時は preview.sh を使う)
      → lib.sh (依存の解決、mise.toml の合成、ファイルのコピー、プレースホルダの置換など)
```

`lib.sh` の主な関数は次のとおりです。

| 関数                                                 | 内容                                                                                  |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `rp_discover_components`、`rp_selectable_components` | コンポーネントの一覧を返す。後者は非表示のものを除く                                  |
| `rp_meta_field`、`rp_depends_on`、`rp_is_hidden`     | 各コンポーネントの `meta.sh` から説明、依存、非表示フラグを読む                       |
| `rp_resolve_closure`                                 | `DEPENDS_ON` をたどって、導入する全コンポーネントを決める。`_common` は常に先頭になる |
| `rp_merge_mise_toml`、`rp_generate_aggregate_tasks`  | 各コンポーネントの断片を 1 つの `mise.toml` に合成し、まとめて実行するタスクを作る    |
| `rp_copy_component`、`rp_substitute_placeholders`    | ファイルのコピーと、`{{github_user}}` などの置換                                      |
| `rp_merge_gitignore`、`rp_compose_dependabot`        | `.gitignore` と Dependabot の設定を合成する                                           |

テストは次のコマンドで実行します。

```bash
bash mise/scripts/repo-preset/tests/lib_test.sh
```

## 関連ファイル

- `bash/daily/.env`: `DAILY_PROFILE` を書く場所
- `install.sh`、`unlink.sh`: プロファイルのリンクを作成・削除する
- `mise.toml`、`mise.lock`: dotfiles リポジトリ自身のツールとタスク
- `repo-preset/`: `repo-preset-install` が導入する素材

`mise.lock` と、それが参照する `.mise/locks/` の sidecar は一緒に Git 管理します。lockfile の形式によっては古い mise で読み込めないため、エラーが出た場合は mise を更新してください。
