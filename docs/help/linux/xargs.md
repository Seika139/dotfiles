# xargs コマンド

xargs は高速に並列処理ができるのでとても便利。

## 基本

`コマンド1 | xargs コマンド2`

前のコマンド(コマンド 1)で取得した値(標準出力)を利用して xargs で指定した別のコマンド(コマンド 2)に引数として渡して実行させる

## 例

```bash
$ find ~/notebooks//08_k6  -type f -name '*.md' | xargs ls | head -n 3
~/notebooks//08_k6/1220/index.md
~/notebooks//08_k6/1222/confluence.md
~/notebooks//08_k6/xargs.md
```

## t オプション

xargs で指定されたコマンドの実行内容を表示させるには、`-t` オプションを付与する。
この実行コマンドは標準エラー出力となっているため、実行コマンドのみを `test.cmd`、コマンドの実行結果のみを `test.lst` に出力させる

```bash
find ~/notebooks/08_k6 -type f -name '*.md' | xargs -t ls > result.txt 2> command.txt
```

## p オプション

xargs で生成したコマンドを本当に実行するかどうかを確認させる。
`y` を押すことで確認したコマンドを実行する。

## n オプション

xargs で実行するコマンド一行にいくつまで引数を渡すのか指定する。

```bash
コマンド1 | xargs -n 引数の数 コマンド2
```

## i/I オプション

xargs はコマンド 2 の最後にコマンド 1 の出力を付与するが、
I オプションを使うことでコマンド 2 の任意の位置にコマンド 1 の出力を与えたり、コマンド 1 の出力を複数回コマンド 2 に与えたりできる。

```bash
コマンド1 | xargs -I {プレースホルダー} コマンド2
```

プレースホルダーには任意の文字列を指定する(例 :XXX)など。
小文字の i オプションの場合はプレースホルダーの指定がオプショナルとなる。
その際のプレースホルダーのデフォルトのストリングは `{}` となる。

## スペース区切りで複数の引数を xargs に渡すときの注意点

xargs ではプレースホルダーが現れるすべての箇所を標準入力の文字列で置き換える。
この際標準入力中にクォートされていない空白があっても入力項目の区切りにはならない。
区切りの指標は改行文字だけになる。
したがって配列/スペース区切りの文字列で xargs に複数の引数を与えたいときは空白ではなく改行文字で区切るように留意する。

```bash
$ echo -e "AAA BBB\nCCC\nDDD" |xargs -I{} echo {} is {}
AAA BBB is AAA BBB
CCC is CCC
DDD is DDD
```

詳細は以下のページを参照。

- <https://linuxjm.osdn.jp/html/GNU_findutils/man1/xargs.1.html>

**参考ページ**

- <https://orebibou.com/ja/home/201507/20150727_001/>
- <https://techblog.kyamanak.com/entry/2018/02/12/202256>
- <https://www.ibm.com/docs/ja/zos/2.2.0?topic=descriptions-xargs-construct-argument-list-run-command>
