# history コマンド

実行したコマンドの履歴を表示する

```bash
history !N      # N番目の履歴のコマンドを実行する
history !-N     # N個前の履歴のコマンドを実行する
history !!      # 前回のコマンドを実行する
history !STR    # STRから始まる最新コマンドを実行する
history !?STR?  # STRを含む最新コマンドを実行する
history !STR:p  # STRから始まる最新コマンドをecho表示する(実行はしない)
```

もっと詳しい使い方は以下のリンクを参照

- <https://orebibou.com/ja/home/201606/20160630_001/>
- <https://mseeeen.msen.jp/bash-history-expansion/>

**`ctrl + R` で history の検索をする**

- enter : 実行する
- esc : 検索を終了する
