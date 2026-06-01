# awk コマンド

テキストを行ごとに読み、列を取り出したり集計したりするコマンド。
`grep` と `cut` と簡単な集計処理をまとめて書きたいときに便利。

## 基本

```bash
awk '条件 { 処理 }' ファイル
```

条件に一致した行に対して `{ 処理 }` を実行する。
条件を省略するとすべての行が対象になる。
処理を省略すると対象行をそのまま表示する。

```bash
awk '{ print $1 }' file       # 1列目を表示する
awk '/error/' file            # error を含む行を表示する
awk '/error/ { print $2 }' file # error を含む行の2列目を表示する
```

## オプション

```bash
-F 区切り文字        # 入力の区切り文字を指定する
-v 変数名=値         # awk に変数を渡す
-f ファイル          # awk スクリプトをファイルから読み込む
```

## よく使う変数

| 変数  | 意味                 |
| :---- | :------------------- |
| `$0`  | 行全体               |
| `$1`  | 1列目                |
| `$2`  | 2列目                |
| `NF`  | 現在行の列数         |
| `NR`  | 通算の行番号         |
| `FNR` | ファイルごとの行番号 |
| `FS`  | 入力の区切り文字     |
| `OFS` | 出力の区切り文字     |

## 区切り文字を指定する

入力の区切り文字は `FS` で決まる。
デフォルトは空白で、スペースやタブが連続していても1つの区切りとして扱われる。

```bash
echo 'foo   bar baz' | awk '{ print $1, $2, $3 }'
```

```bash
awk -F, '{ print $1, $3 }' users.csv
awk -F: '{ print $1 }' /etc/passwd
```

出力の区切り文字を変えたい場合は `OFS` を指定する。

```bash
awk -F, 'BEGIN { OFS="\t" } { print $1, $3 }' users.csv
```

## 条件で絞り込む

```bash
awk '$3 >= 80 { print $1, $3 }' score.txt
awk 'NR > 1 { print }' users.csv          # 1行目を飛ばす
awk 'NF >= 3 { print $0 }' file           # 3列以上ある行だけ表示する
awk '$1 == "ERROR" { print $0 }' app.log
```

正規表現は `/pattern/` で書く。
特定の列だけを正規表現で見る場合は `$列番号 ~ /pattern/` を使う。

```bash
awk '/timeout/' app.log
awk '$2 ~ /^user-/ { print $0 }' file
awk '$2 !~ /^user-/ { print $0 }' file
```

## BEGIN / END

`BEGIN` は入力を読む前、`END` は入力を読み終わった後に実行される。
ヘッダー表示や合計値の出力に使う。

```bash
awk 'BEGIN { print "name score" } { print $1, $3 }' score.txt
awk '{ sum += $3 } END { print sum }' score.txt
awk '{ sum += $3 } END { print sum / NR }' score.txt
```

## 集計する

```bash
awk '{ count++ } END { print count }' file
awk '{ sum += $1 } END { print sum }' file
awk '{ count[$1]++ } END { for (key in count) print key, count[key] }' file
```

列ごとに集計した結果は順序が保証されない。
順序が必要な場合は `sort` に渡す。

```bash
awk '{ count[$1]++ } END { for (key in count) print key, count[key] }' file | sort
```

## 変数を渡す

シェル変数を awk の中で使うときは `-v` を使う。
シングルクォートの中ではシェル変数は展開されないため。

```bash
threshold=80
awk -v min="$threshold" '$3 >= min { print $1, $3 }' score.txt
```

## 複数ファイルを処理する

`NR` はすべてのファイルを通した行番号、`FNR` はファイルごとの行番号。

```bash
awk '{ print NR, FNR, FILENAME, $0 }' *.log
awk 'FNR == 1 { print FILENAME }' *.log
```

## 注意点

- awk の式は基本的にシングルクォート `'...'` で囲む。`$1` などをシェルに展開させないため。
- CSV の引用符や改行を厳密に扱う用途には向かない。複雑な CSV は Python などの CSV パーサーを使う。
- `for (key in array)` の順序は保証されない。必要なら `sort` と組み合わせる。

**参考**

- <https://www.gnu.org/software/gawk/manual/gawk.html>
- <https://pubs.opengroup.org/onlinepubs/9699919799/utilities/awk.html>
