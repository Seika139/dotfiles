# gh stack

Stacked PR は、大きな変更を小さなレビュー可能なプルリクエストの連鎖に分割する。
複数の分割された PR に対して自動的に依存関係を管理し、リベースの維持、適切な PR ベースブランチの設定、レイヤー間のナビゲーションなど、面倒な部分を自動化する。

## 導入

```sh
gh extension install github/gh-stack
```

GitHub CLI (`gh`) v2.0 以上と Git 2.36 以上が必要。GitHub CLI で認証済みで、対象リポジトリへの push 権限が必要。

## Stacked PR の仕組み

スタックは、各ブランチがその下のブランチの上に構築されるブランチの順序付きリストである。
最下段のブランチは幹（trunk）に基づく、（一般的には main ブランチ）、最上段のブランチは最も新しい変更を含む。

```text
frontend      → PR #3 (base: api-endpoints) ← top
api-endpoints → PR #2 (base: auth-layer)
auth-layer    → PR #1 (base: main)          ← bottom
─────────────
main (trunk)
```

## 基本の使い方

`gh stack init` は対話形式で最初のブランチを作成する。そこで変更をコミットし、現在の stack 最上位ブランチ上で `gh stack add` を実行すると、その最上位に新しいブランチを作成して checkout し、次の層として積む。
別のワークツリーで checkout 済みの既存ブランチを指定して stack に取り込むこともできる。最後に `gh stack submit` を実行すると、各ブランチを push して stack の pull request を作成する。

```sh
gh stack init
# 最初の変更を作成してコミット
git add .
git commit -m "Add the first change"

gh stack add api-endpoints
# 次の変更を作成してコミット
git add .
git commit -m "Add API endpoints"

gh stack submit
```

## 下位ブランチを修正したとき

修正するブランチに移動して変更をコミットした後、上位ブランチを追従させて push する。

```sh
gh stack checkout <branch>
# 修正してコミット
gh stack rebase --upstack
gh stack push
```

## trunk 更新後

stack 最下段の pull request がマージされた後は、`gh stack sync` で trunk と残りのブランチを同期する。

```sh
gh stack sync
```

## コマンド

### init

現在のリポジトリに新しいスタックを追加する。

```bash
gh stack init [flags] [branches...]

# develop ブランチを幹としてスタックを初期化し、feature/auth-layer ブランチを最初のレイヤーとして追加する
gh stack init --base develop feature/auth-layer

# feature/base ブランチを幹として、auth-layer ブランチから始まるスタックを初期化する
gh stack init --base feature/base auth-layer
```

### add

現在のスタックの上に新しいブランチを追加する。
既存のスタックに対して、現在の HEAD に新しいブランチを作成し、それをスタックの最上位に追加してチェックアウトする。
スタックの最上位ブランチにいる状態で実行する必要がある。ブランチ名を省略すると通常は入力を求められるが、`-m` を指定した場合はコミットメッセージから自動生成される。

```bash
gh stack add [flags] [branch]
```

| flags              | 説明                                                                     |
| :----------------- | :----------------------------------------------------------------------- |
| -A,--all           | すべての変更をステージする（追跡されていないファイルを含む）。`-m` が必須で、`-u` とは併用できない。 |
| -u,--update        | 追跡対象のみのファイルをステージする。`-m` が必須で、`-A` とは併用できない。                                     |
| -m,--message <msg> | ブランチを作成する前に、このメッセージを含むコミットを作成すること。 |

**例**

```bash
# api-routes ブランチを作成して、現在のスタックの上に追加する
gh stack add api-routes

# 全ての変更をステージしてコミットし、自動で作成されるブランチをスタックに追加する
gh stack add -Am "Add login endpoint"

# 全ての変更をステージしてコミットし、test-layer ブランチを作成してスタックに追加する
gh stack add -Am "Add tests" test-layer
```

別のワークツリーでチェックアウトされている既存のブランチは、どちらのチェックアウトも切り替えずに採用できる。
コミット/ステージングのショートカットを使用して外部所有のブランチを採用することはできず、ステージングまたはスタックメンバーシップの変更前に失敗する。

スタックの一部ではないブランチから対話的に実行した場合、add代わりに新しいスタックを初期化するかどうかを尋ねられる。
指定された、または自動生成されたブランチ名が最初のレイヤーになる。指定がない場合は、標準のinitプロンプトが使用される。

### submit

スタックの全ブランチを push し、各ブランチの pull request を作成または更新して、GitHub 上で Stack として関連付ける。

```bash
gh stack submit [flags]
```

```bash
# スタックの PR を作成または更新する
gh stack submit
```

### sync

GitHub とローカルのスタックを同期する。
GitHub 上で Stack に追加された PR のブランチは、ローカルの stack に取り込まれる。
ローカルと GitHub 上の stack 構成が分岐した場合は、差分が提示され、選択が必要なため同期が中断することがある。
trunk が更新されていれば各ブランチを rebase して push し、PR の状態と Stack の関連付けも同期する。
PR は作成しない。
`--prune` を指定すると、マージ済み PR に対応するローカルブランチを削除する。

```bash
gh stack sync [flags]
```

```bash
# 同期して、マージ済みブランチも削除する
gh stack sync --prune
```

### push

未マージかつ merge queue に入っていないスタックのブランチを、`--force-with-lease` を使って push する。
PR の作成や更新は行わない。
全ブランチを1回の `git push` で送るが、atomic ではないため、lease が通ったブランチだけ更新される場合がある。

```bash
gh stack push [flags]
```

```bash
# スタックのブランチを push する
gh stack push
```

### rebase

スタックのブランチを下位から順に、親ブランチの最新コミット上へ rebase する。
下位ブランチの修正を上位へ反映するには、そのブランチで `--upstack` を指定する。

```bash
gh stack rebase [flags] [branch]
```

```bash
# 現在のブランチから上位を rebase する
gh stack rebase --upstack

# 競合を解消して続行する
git add <file>
gh stack rebase --continue

# rebase を中止する
gh stack rebase --abort
```

### merge

現在のスタック、または指定した PR までの pull request をまとめてマージする。
通常のマージは全件成功するか全件失敗する。
base ブランチで merge queue が有効な場合は、対象 PR を queue に追加する。

```bash
gh stack merge [<stack-number> | <pr-number>] [flags]
```

```bash
# 現在のスタックをマージする
gh stack merge
```

### view

スタック内のブランチ順、PR、各ブランチの最新コミットを表示する。
表示のみで、スタックやブランチは変更しない。

```bash
gh stack view [flags]
```

```bash
# スタックを表示する
gh stack view
```

### unstack

GitHub 上の Stack との関連付けとローカルの追跡情報を解除する。
PR とブランチは削除しない。
`--local` を指定すると、GitHub に接続せずローカルの追跡情報だけを解除する。
マージ済み、マージ処理中、または merge queue 中の PR は Stack から解除されない。
`--local` を指定しない場合、これらの PR が残ると Stack とローカルの追跡情報も維持される。

```bash
gh stack unstack [<stack-number>] [flags]
```

```bash
# 現在のスタックを解除する
gh stack unstack

# ローカルの追跡情報だけを解除する
gh stack unstack --local
```

## 参考

- [Creating stacked pull requests - GitHub Docs](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-stacked-pull-requests)
- [Managing stacked pull requests - GitHub Docs](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/managing-stacked-pull-requests)
- [github/gh-stack](https://github.com/github/gh-stack)
