# git worktree

stash せずとも他ブランチに切り替えられる

## 基本

```bash
git worktree [subcommand]
g wk [subcommand]        # エイリアス
```

## リスト表示

```bash
git worktree list
gwl               # エイリアス
```

ワークツリーを `ワークツリーへのパス コミットハッシュ 追加情報` の形式で一覧表示する。

### 追加情報

- チェックアウトされているブランチ名（存在しない場合は detached HEAD と表示される）
- locked（ワークツリーがロックされている場合）
- prunable（ワークツリーが prune コマンドで削除できる場合）

## 作成

```bash
git worktree add <path> [<commit-ish>]
```

path にワークツリーを作成し、commit-ish（commit id やブランチ名）をチェックアウトする。
commit-ish を省略すると、新しいワークツリーは $(basename <path>) にちなんで名付けられたブランチに関連付けられる。
関連するブランチがない場合は HEAD に基づくブランチが自動的に作成される。

## 削除

```bash
git worktree remove [-f/--force] <worktree>
```

worktree を削除する。`-f` を使うと追跡されているファイルに変更がある場合や、新規の未追跡ファイルがある場合でも削除する。

## prune

```bash
git worktree prune
```

rmコマンドなどで物理的に削除されたワークツリーを git worktree の管理から削除する。

## 作業中にプルリクレビューがきたときの例

- `git worktree add review branch_name` で ./review 内に branch_name が展開される。
- `cd review` でディレクトリの移動とともにブランチも移動する。
- review 内のファイルを見てコードレビューする。
- `git worktree remove review` で不要になったワークツリーを消す。

## 作業中に別のブランチを作る場合の例

- `git worktree add -b new_branch dir base_branch` で ./dir 内に base_branch からチェックアウトされた new_branch が展開される。
  base_branch を省略すると自動的に HEAD からチェックアウトされる。

**参考**

- <https://git-scm.com/docs/git-worktree>
- <https://runebook.dev/ja/docs/git/git-worktree>
