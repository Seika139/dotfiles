# Git のタグ機能

タグを使うことで、特定のコミットに名前を付けて管理することができる。
リリースバージョンや重要なマイルストーンを示すために使用されることが一般的。

## タグを付与する

```bash
git tag -a v0.1.0 5afdbea
```

コミットを省略した場合は HEAD が指定される。
`-m` オプションでタグにメッセージを付けることができる。

```bash
git tag -a v0.1.0 -m "Initial release with basic FileScribe functionality"
```

## タグの一覧を表示する

```bash
git tag
```

## 特定のパターンのタグを表示する

```bash
git tag -l "v0.1.*"
```

## タグの詳細を表示する

```bash
git show v0.1.0
```

## タグを削除する

```bash
git tag -d v0.1.0
```

ただし一度リモートにプッシュしたタグは削除できない。（と考えて良い）
