# git stash

## スタッシュする

変更をスタッシュにプッシュする。
ステージされていない新規ファイル(未追跡ファイルはスタッシュされない)

```bash
git stash save
git stash     # save は省略できる
g ss          # 自作のエイリアス
```

### オプション

```bash
git stash save -u       # untrackファイル(未追跡ファイル)も含めてスタッシュ
git stash save -k / --keep-index  # スタッシュしてもステージの状態はそのままにする
git stash save "message"          # メッセージをつけてスタッシュする
```

## スタッシュを表示する

`stash@{N}` でスタッシュ番号を示す。`N` だけでも同義

```bash
git stash list    # 退避した作業の一覧を見る
gsl               # 自作エイリアス
git stash show stash@{N}    # N番目にスタッシュしたファイルの一覧を表示
git stash show -p stash@{N} # N番目にスタッシュしたファイルの変更差分を表示
```

## スタッシュを適用・削除する

```bash
git stash apply stash@{N}         # stash@{N} の作業をもとに戻す
git stash apply stash@{N} --index # stage して退避した作業は stage されたまま戻る
git stash drop stash@{N}          # stash@{N} の作業を消す stash@{N} を省略するとスタッシュの一番上を削除する
git stash pop stash@{N}           # stash@{N} の作業をもとに戻すと同時に、退避作業の中から削除
git stash clear                   # stash のリストを全て削除(要注意!)
```

## diff stash

```bash
git diff stash@{N}        # HEADとstashの差分を確認する
git diff stash@{N} [file] # ファイルの指定も可能
```
