# du と dust で容量の大きい項目を探す

容量を整理するときは、最初に軽い検索で候補を探し、心当たりのある小さなディレクトリだけを `du` や `dust` で調べます。

## 走査する前に候補を探す

Linux と macOS では、まずホーム直下にある大きなファイルを調べられます。

```bash
find "$HOME" -maxdepth 1 -type f -exec du -k {} + | sort -nr | head -n 10
```

`-maxdepth 1` はホーム直下のファイルだけを調べ、子ディレクトリには入りません。直下のファイルが多い場合は、その数だけ名前やサイズなどのメタデータを確認します。

Windows では PowerShell でユーザーフォルダ直下にある大きなファイルを調べられます。

```powershell
Get-ChildItem -LiteralPath $env:USERPROFILE -File -Force | Sort-Object Length -Descending | Select-Object -First 10 Length, FullName
```

この検索も直下のファイルだけを対象にします。`Length` はファイルサイズをバイト単位で示します。

深い階層にある大きなファイルは、既に有効な検索インデックスを使って候補を探せます。macOS では Spotlight のインデックスを `mdfind` で検索します。

```bash
mdfind -onlyin "$HOME" 'kMDItemFSSize > 1073741824'
```

Windows ではインデックスが作成済みの場所をエクスプローラーで開き、検索欄に `System.Size:>1073741824` と入力します。未索引の場所ではファイル走査が発生することがあるため、索引済みの場所だけを検索します。

インデックス検索はサイズが 1 GiB を超えるファイルを見つけます。未索引のファイルや、多数の小さなファイルで容量を使うディレクトリは候補に出ないことがあります。ディレクトリの合計は事前の集計情報がなければ配下を測る必要があるため、キャッシュやビルド出力など心当たりのある場所を選びます。

`Downloads` 直下の名前を確認するだけなら、`ls -A` は下の階層へ入りません。容量を調べるパスを見つけたら、実在する小さなサブディレクトリを `scan_dir` に指定します。

```bash
ls -A "$HOME/Downloads"

# 実在する小さなディレクトリに置き換える
scan_dir="$HOME/Downloads/old-builds"
```

候補が見つからない場合は、対象を `Downloads` などに絞り、先ほどの `find` の `-maxdepth 1` を `-maxdepth 2` に替えて浅い層を確認できます。階層を深くすると調べる項目が増えます。

## ディレクトリの容量を調べる

選んだディレクトリ直下を容量順に表示します。

```bash
# GNU/Linux、macOS、WSL、Git Bash
du -k -d 1 "$scan_dir" | sort -nr | head -n 10
dust -D -d 1 -n 10 "$scan_dir"
```

`du` の `-d 1` は直下までを表示し、各ディレクトリの合計にはその下の階層も含みます。起点の `scan_dir` 自体の合計も表示されます。

`du -k` のサイズは 1024 バイト単位です。`du` は隠しディレクトリも集計し、`dust` も既定で隠し項目を表示します。

読み取り権限のないディレクトリは集計できず、警告が表示されることがあります。

`du` の各行は左にサイズ、右にパスが表示され、`sort -nr` はサイズの大きい順に並べます。

`dust` の割合バーを見ると、各ディレクトリが起点全体のどの程度を占めるか分かります。

`-d 1`、`sort` と `head`、`dust -n` は表示内容を絞る指定です。容量を集計するため、選んだディレクトリ以下の項目は深い階層まで走査します。

これらのコマンドは配下の名前を列挙してサイズなどのメタデータを確認します。通常はファイルの内容全体を読み込みませんが、対象に大量の項目があれば時間がかかります。

`-x` は選んだディレクトリの下にある別ファイルシステムへ入らない指定です。選んだファイルシステム内の走査範囲や項目数は減りません。

`dust -D` はディレクトリに絞り、`-n 10` は大きな項目を10件表示します。ツリーの親項目や合計行が加わることがあります。

## 大きいディレクトリを掘り下げる

容量の大きい子ディレクトリがあれば、その実在するパスを新しい起点にします。

```bash
# 例の cache を選んだディレクトリ内にある既存の子ディレクトリへ置き換える
scan_dir="$scan_dir/cache"
du -k -d 1 "$scan_dir" | sort -nr | head -n 10
dust -D -d 1 -n 10 "$scan_dir"
```

`dust` のツリーで容量の多い項目をたどるか、`du` の一覧から次に調べるパスを選び、起点をそのパスへ更新します。

## 大きいファイルを見つける

`dust -F` はファイルに絞って表示します。`-p` を付けるとファイルのパス全体が分かります。

```bash
dust -F -n 10 -p "$scan_dir"
```

`find` と `du` を組み合わせると、ファイルの容量を数値順に並べられます。

```bash
find "$scan_dir" -type f -exec du -k {} + | sort -nr | head -n 10
```

この一覧の容量も KiB 単位です。選んだディレクトリ以下にあるファイルを検索します。

`find` は対象ディレクトリ以下を再帰的に調べるため、ファイル数が多いと時間がかかることがあります。

## Windows で使う

Windows 版 `dust` は PowerShell から実行できます。実在する小さなディレクトリに合わせて `old-builds` を置き換えます。

```powershell
$scanDir = Join-Path $env:USERPROFILE 'Downloads\old-builds'
dust -D -d 1 -n 10 "$scanDir"
dust -F -n 10 -p "$scanDir"
```

GNU `du` の例は WSL または Git Bash の Bash で実行します。WSL で Windows 側のファイルを調べる場合は、`scan_dir` に `/mnt/c/Users/<ユーザー名>/Downloads/old-builds` のような実在する小さなサブディレクトリを指定します。WSL の `$HOME` は Linux 側のホームディレクトリです。

PowerShell の `$env:USERPROFILE` は Windows 側のユーザーフォルダを指します。

Spotlight の `kMDItemFSSize` は [Apple のドキュメント](https://developer.apple.com/documentation/coreservices/kmditemfssize)、エクスプローラーの検索構文は [Microsoft の Advanced Query Syntax](https://learn.microsoft.com/en-us/windows/win32/search/-search-3x-advancedquerysyntax) を参照してください。`du` の OS ごとのオプションや単位は [`du.md`](./du.md)、`dust` の集計方法は [`dust.md`](./dust.md)、ほかの検索方法は [`find_large_directory.md`](./find_large_directory.md) にあります。

## 空き容量を確認する

選んだディレクトリがあるファイルシステムの空き容量は `df` で確認できます。

```bash
df -h "$scan_dir"
```

この結果はファイルシステム全体の使用量と空き容量を示し、個別のディレクトリ容量は表示しません。
