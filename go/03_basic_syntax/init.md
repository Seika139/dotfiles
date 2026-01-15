# Go の基本構文

以下のコマンドを実行すれば現在のディレクトリ名を使って `go.mod` ファイルを初期化できます。

```bash
go mod init "github.com/username/$(basename $(pwd))"
```
