# wc コマンド

使い方: `wc [オプション] [ファイル]`

## `[オプション]`

- -c : バイト数
- -m : 文字数
- -l : 行数
- -w : 単語数

オプションをつけないと `行数 単語数 バイト数` が表示される

## `[ファイル名]`

**ワイルドカードで指定もできる**

```bash
# 指定したファイルの行数を出力する
$ wc -l docs/help/linux/*.md
       9 docs/help/linux/alias.md
      20 docs/help/linux/complete.md
      52 docs/help/linux/find_large_directory.md
      69 docs/help/linux/find.md
      71 docs/help/linux/grep.md
      50 docs/help/linux/history.md
      37 docs/help/linux/kill.md
      37 docs/help/linux/less.md
      48 docs/help/linux/lsof.md
     165 docs/help/linux/rsync.md
      41 docs/help/linux/sed.md
      38 docs/help/linux/set.md
      33 docs/help/linux/wc.md
      25 docs/help/linux/wild_card.md
      77 docs/help/linux/xargs.md
      11 docs/help/linux/カーソル移動.md
     783 total
```

**標準出力の行数を調べる**

```bash
$ ls -al | wc -l
15
```
