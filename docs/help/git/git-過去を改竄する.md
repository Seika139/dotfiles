# git で一度コミットしたものを修正する

## checkout

パスに含まれるファイルを指定したコミットIDの状態にする。
一部のファイルを元に戻したいときに有効。

```bash
git checkout [commit-id] [path]
```

## revert

指定したコミットIDの内容と逆の内容をコミットする。
リモートにプッシュ済みのコミットでも安全に差分を元に戻すことができる。

```bash
git revert [commit-id]
```

## reset

HEAD(現在のコミットid)の位置を過去のコミットidに戻す。
reset はリモートに push した後の状態では基本的に使わない。

```bash
git reset [option] [commit-id]
```

### オプション

**--soft**

HEAD の状態を戻す。作業ディレクトリ/ワーキングツリーとステージングエリア/インデックスはそのまま。

```bash
git reset --soft @^
```

直前のコミット内容を修正するときに使える。直前のコミット差分はステージングエリアに残る。

**--mixed**

HEAD とステージングエリアの状態を戻す。作業ディレクトリはそのまま。
option を省略した場合は --mixed と解釈される

```bash
git reset --mixed @
```

HEAD とステージングエリアの状態を HEAD に戻す。
つまりステージングエリアのファイルが作業ディレクトリに戻るのでaddを取り消したいときに使える。
なお HEAD も省略できるので `git reset` だけで良い。

**--hard**

HEAD、ステージングエリア、作業ディレクトリの全ての状態を戻す。つまりコミットしていない変更差分は全て消えてなくなるので注意

**特定のファイルのaddを取り消す**

```bash
git reset [file-name]
```

reset すると HEAD の位置が過去に戻るので、リモートに push した後で reset するとリモートの方が差分が進んだ状態になる。
そのため基本的にはリモートの差分を pull してから出ないと push できない。
`git push -f / --force` で無理矢理ローカルの状態を push できるが、リモートの変更差分も完全に消えてしまう。
そうすると他の人のブランチにも影響が生じる。これが「reset は危ない」と言われる所以。
したがって「複数人が開発するブランチに対して push 済みのコミットを reset しない」ようにすること。

**参考**

- <https://www.r-staffing.co.jp/engineer/entry/20191129_1>
- <https://qiita.com/forest1/items/f7c821565a7a7d64d60f>

## reflog

HEADの履歴(自分が撮った操作履歴)を表示する。git reflog show HEAD のショートカット。

```bash
git reflog
```

- `--date=iso-local` : オプションがないと時間の情報がないので --date オプションをつけておくと良い。
- `--all` : reflog は HEAD 以外の履歴も記録している。全ての完全なrefを見るときはこのオプションを使う

`reflog` は HEAD の動き（自分自身が行った行動）を履歴にしたもの。
具体的には、次のものが履歴として残る。

- 新規コミット（コミット、マージ、プル、リバートなど）
- ブランチの切り替え（チェックアウト）
- 履歴の書き換え（リセット、リベースなど）

reset したコミットを元に戻す、削除したブランチを元に戻す、などができる。
やり方はこの記事を参照 → <https://toronavi.com/git-reflog>

**参考**

- <https://www.r-staffing.co.jp/engineer/entry/20191227_1>
