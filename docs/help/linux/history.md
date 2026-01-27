# history コマンド

実行したコマンドの履歴を表示する。
保存されるコマンド履歴の数は環境変数 `$HISTSIZE` で定められる。

```bash
history              # 保存されたコマンド履歴を表示する
history N            # 直近 N 個までのコマンド履歴を表示する
history -c           # コマンド履歴をクリアする
history -w file_name # コマンド履歴をファイルに保存する
history -r file_name # ファイルにあるコマンド履歴を現在の履歴に取り込む
```

## 履歴を利用してコマンドを実行する

```bash
!N      # N番目の履歴のコマンドを実行する
!-N     # N個前の履歴のコマンドを実行する
!!      # 前回のコマンドを実行する
!STR    # STRから始まる最新コマンドを実行する
!?STR?  # STRを含む最新コマンドを実行する
!STR:p  # STRから始まる最新コマンドをecho表示する(実行はしない)
```

もっと詳しい使い方は以下のリンクを参照

- <https://orebibou.com/ja/home/201606/20160630_001/>
- <https://mseeeen.msen.jp/bash-history-expansion/>

## `ctrl + R` で history の検索をする

コマンド入力行に `ctrl + R` を入力すると画面に

```bash
(reverse-i-search) '':
```

と表示される。ここに文字列を入力すると以下のように入力した文字列に合致するコマンドが表示される

```bash
# so と入力したとき
(reverse-i-search)`so': source ~/.bash_profile
```

その後、以下の操作ができる

- `enter` : 表示されているコマンドを実行する
- `esc` : 検索を終了し、画面にそのコマンドが残る（次の enter で実行可能）
- `ctrl + R`: 次の候補
- `↑ / ↓`: 今表示されているコマンドの前後の履歴を表示する
