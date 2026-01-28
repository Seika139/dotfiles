# set コマンド
​
`set` コマンドは、シェルの動作を制御するためのオプションを設定または解除するために使用されます。
これにより、スクリプトやシェルセッションの挙動をカスタマイズできます。
​
## シェル変数の一覧を表示する
​
```bash
$ set
BASH=/bin/bash
BASH_ARGC=()
BASH_ARGV=()
シェル変数の一覧が続く ...
```
​
引数を指定せずに `set` コマンドを実行すると、現在のシェル変数の一覧が表示されます。
​
## オプションフラグの設定
​
```bash
set -E          # errtrace: トラップが有効な場合に、関数やサブシェル内で発生したエラーもキャッチする
set -e          # errexit: スクリプト内でエラーが発生した場合に即座に終了する
set -u          # nounset: 未定義の変数を参照した場合にエラーを発生させる
set -o pipefail # パイプライン内のいずれかのコマンドが失敗した場合にエラーを返す
set -x          # 実行されるコマンドを表示する
```
​
複数のオプションを同時に設定することも可能です。
​
```bash
set -euoE pipefail
```
​
また、オプションを解除するには、対応するフラグの前に `+` を付けます。
​
```bash
set +e          # -e オプションを解除
```
​
## オプションフラグの確認
​
### 1. 現在有効なオプションを一覧表示する
​
現在有効になっているオプションだけをシンプルに確認したい場合は、以下のコマンドを叩きます。
​
```bash
$ echo $-
himBHs
```
​
各文字が有効なフラグを表します（例: e があれば `set -e` が有効）。
​
### すべてのオプションのオン/オフを詳細表示する
​
どの項目が on でどれが off かを一覧で見るには、-o を使います。
​
```bash
# 他の項目も出力されるので、必要に応じて grep などで絞り込むと見やすい
$ set -o | rg 'errexit|errtrace|nounset|pipefail'
errexit         off
errtrace        off
nounset         off
pipefail        off
```
​
- errexit が on なら set -e
- nounset が on なら set -u
​
が効いている状態です。
​
### スクリプト内でデバッグ用に表示する
​
スクリプトの中で、「今どの設定で動いているか」をログに出したい場合は、以下のように書くと確実です。
​
```bash
# 現在のフラグを表示
echo "Current flags: $-"
​
# 特定のオプション（例: nounset）の状態を確認
if [[ -o nounset ]]; then
  echo "set -u (nounset) is ENABLED"
else
  echo "set -u (nounset) is DISABLED"
fi
```
