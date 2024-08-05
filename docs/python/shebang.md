# Shebang

スクリプトファイルの先頭に記載される特別なコメント行で、スクリプトをどのインタプリタで実行するかを指定します。

```python
#!/path/to/interpreter
```

Python スクリプトの場合、一般的なシェバン行は以下のようになります：

```python
#!/usr/bin/env python3
```

## シェバン行の詳細

### `#!`（シェバン）

この 2 文字はシェバン行の始まりを示します。

### インタプリタのパス

`#!/usr/bin/env python3` のように、インタプリタのパスを指定します。
`/usr/bin/env` を使用することで、環境変数 `PATH` に基づいて適切な Python インタプリタを検索します。これにより、システムにインストールされている Python のバージョンに依存せずにスクリプトを実行できるようになります。

## シェバン行の利点

### 可搬性の向上

`#!/usr/bin/env python3` を使用することで、異なるシステム間でスクリプトの可搬性が向上します。システムによって Python のインストール場所が異なる場合でも、適切なインタプリタが使用されます。

### 実行の簡便さ

- シェバン行を含むスクリプトは、実行権限を付与することで直接実行可能になります。例えば、以下のように実行できます：

```sh
chmod +x script.py
./script.py
```

### 情報源

コードの作成者以外に実行する Python バージョンが伝わりやすい。

### 注意点

- シェバン行はスクリプトの最初の行に記載する必要があります。コメントや空行が先にあると無効になります。
- Windows 環境ではシェバン行は無視されますが、クロスプラットフォームでスクリプトを共有する場合には記載しておくと便利です。

## シェバンはどう読まれるか

### Unix 系

python3.9 が起動する

```python
#!python3.9
```

python3 系で最も新しいバージョンで起動する

```python
#!python3
```

### Windows

windows の Python ランチャーで実行する場合は Python ランチャーが仮想的に解釈してくれる。

## Mac Windows Linux どの環境でも動くようにする

Windows で解釈できるのは下記の 3 パターン。一番上の書き方が最も柔軟にどこでも使えるらしい。

```python
#!/usr/bin/env python
#!/usr/bin/python
#!/usr/local/bin/python
```

## 参考

- [Python スクリプトから Shebang の意味を考えてみる #script - Qiita](https://qiita.com/Nick_paper/items/b9655e02721a583f29b5)
- [Python プログラムの先頭行の #! シバン（Shebang）について - ガンマソフト](https://gammasoft.jp/python/python-shebang/)
