# git チートシート

## エイリアスの設定

[.gitconfig](../../../.gitconfig) と [bash/public/12_git_alias](../../../bash/public/12_git_alias.bash) に設定している。

## gitignore

```bash
git status --ignored       # ignore されているファイルが表示される
git check-ignore -v [path] # path が ignore されている原因となる設定の場所が分かる。(複数値可)
```

### gitignore.io

<gitignore.io> を利用してエイリアスから簡単に gitignore を作成する。

```bash
gi macos,python,visualstudiocode,windows > .gitignore
```

## HEAD とは

現在のコミットの場所を指すポインタ。エイリアスとして `@` が使用できる。
HEAD やブランチの概念は参考の記事がわかりやすい。

**参考**

- <https://qiita.com/ymzkjpx/items/00ff664da60c37458aaa>
- <https://nebikatsu.com/6367.html/>
- <https://www.r-staffing.co.jp/engineer/entry/20201225_1>

## 過去のコミットの表し方

### チルダ `~` はn世代前の親を表す

- `@~` : HEAD の親(1世代前)
- `@~~` / `@~2` : HEAD の親の親(2世代前)
- `@~n` : n世代前

### キャレット `^` はn番目の親を表す

ブランチをマージすると親が複数になるのでその時に使用する。
`man git-rev-parse` でドキュメントが表示されるのでそれを見ると良い。

**参考**

- <https://www.chihayafuru.jp/tech/index.php/archives/2535>
- <https://qiita.com/chihiro/items/d551c14cb9764454e0b9>
- <https://masuyama13.hatenablog.com/entry/2020/08/21/231120>
- <https://git-scm.com/book/ja/v2/Git-%E3%81%AE%E3%83%96%E3%83%A9%E3%83%B3%E3%83%81%E6%A9%9F%E8%83%BD-%E3%83%96%E3%83%A9%E3%83%B3%E3%83%81%E3%81%A8%E3%81%AF>

## man git コマンド

各 git コマンドの man を調べるときは `man git-[command]` とする。(例) `man git-grep`

## git remote

```bash
gr # 自作エイリアス
git remote show origin            # remoteブランチを単純参照
git remote -v                     # 登録されているリモートリポジトリを確認する
git remote prune --dry-run origin # remoteブランチでは削除されているが、ローカルに参照が残っているブランチを表示
git remote prune origin           # すでに削除されているremoteブランチのローカル参照を削除してきれいにする
grpo # git remote prune origin のエイリアス
```

## 日付形式

`--date=[option]` は git log や git stash list などで日付を表示するときに使う

| [option]                         |                                      例                                      |
| :------------------------------- | :--------------------------------------------------------------------------: |
| local                            |                           Mon Nov 23 21:26:47 2020                           |
| iso-local                        |                          2020-11-23 21:26:47 +0900                           |
| relative                         |                                 4 months ago                                 |
| format-local:'%Y/%m/%d %H:%M:%S' | `2020/11/23 21:26:47` -> カスタム表示、localをつけないと世界標準時になりうる |

## git add

```bash
git add [option] [filename]
```

- `-u` / `--update` : 既にバージョン管理されている変更があったファイルをaddする。新規作成されたファイルはaddされない
- `-A` / `--all` : 変更があった全てのファイル
- `-n`/ `--dry-run` : 実行内容を表示するだけで実際には実行しない
- `.` : カレントディレクトリ以下のファイル
- `*.html *.py` : このようにワイルドカードでの指定もできる

## ブランチを削除/変更する

```bash
git branch -D [branch_name]                       # ローカルのブランチを削除
git branch -m [old_branch_name] [new_branch_name] # ローカルのブランチ名を変更
git branch -m [new_branch_name]                   # 現在のローカルブランチ名を変更する
git push origin :[branch_name]                    # リモートのブランチを削除
```

## コンフリクトしたとき

```bash
git merge --abort            # マージを中止する
git checkout --ours [file]   # チェックアウトしているブランチ側の変更を反映する
git checkout --theirs [file] # マージさせたいブランチ側の変更を反映する
```
