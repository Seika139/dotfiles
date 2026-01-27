# 容量が大きいファイル・ディレクトリを探す

CLI で容量の大きいファイル・ディレクトリを探す場合は `du` コマンドや `find` コマンドを使うことが多い。

## du コマンド

`du` コマンドは、指定したディレクトリ以下のファイルやサブディレクトリのサイズを表示するコマンド。

```bash
du [オプション] [ディレクトリまたはファイル]
```

### よく使うオプション

- `-h` : 人間が読みやすい形式でサイズを表示する（例: KB, MB, GB）。
- `-s` : 指定したディレクトリの合計サイズのみを表示する。指定しない場合はディレクトリ内のディレクトリを再帰的に表示する。
- `-a` : ディレクトリ内のファイルも含めてサイズを表示する。 `s` と `a` は同時に指定できないので注意。

## find コマンド

`hlp_find` で [./find.md](./find.md) の内容を表示できるのでそちらも参照すべし。

## 直下のディレクトリのサイズを調べる

```bash
# .git のような隠しディレクトリが表示されない
du ./* -sh

# BSD系の du コマンドの場合
find . -depth 1 -type d -exec du -sh {} \;
find . -depth 1 -type d  | xargs -n 1 du -sh
find . -depth 1 -type d  | xargs -i du -sh {}

# GNU系の du コマンドの場合 -depth オプションが存在しないので冗長になる
find . -maxdepth 1 -mindepth 1 -type d -exec du -sh {} \;
find . -maxdepth 1 -mindepth 1 -type d  | xargs -n 1 du -sh
find . -maxdepth 1 -mindepth 1 -type d  | xargs -i du -sh {}
```

それぞれ

```bash
コマンド | sort -rh
```

でソートするとサイズの大きい順に表示される。

```bash
head -n 10
```

で上位 10 件を表示することができる。
