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
save -k / --keep-index  # スタッシュしてもステージの状態はそのままにする
save "message"          # メッセージをつけてスタッシュする
```

## スタッシュを表示する

`stash@{N}` でスタッシュ番号を示す。`N` だけでも同義

```bash
git stash list    # 退避した作業の一覧を見る
gsl               # 自作エイリアス
show stash@{N}    # N番目にスタッシュしたファイルの一覧を表示
show -p stash@{N} # N番目にスタッシュしたファイルの変更差分を表示
```

## スタッシュを適用・削除する

```bash
apply stash@{N}         # stash@{N} の作業をもとに戻す
apply stash@{N} --index # stage して退避した作業は stage されたまま戻る
drop stash@{N}          # stash@{N} の作業を消す stash@{N} を省略するとスタッシュの一番上を削除する
pop stash@{N}           # stash@{N} の作業をもとに戻すと同時に、退避作業の中から削除
clear                   # stash のリストを全て削除(要注意!)
```

## diff stash

```bash
git diff stash@{N}        # HEADとstashの差分を確認する
git diff stash@{N} [file] # ファイルの指定も可能
```
