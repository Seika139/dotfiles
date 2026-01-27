# complete コマンド

completeコマンドは、bashの組み込みコマンドになります。
シェルでは入力途中の文字に対してTABを入力すると入力補完機能が働きます。
completeコマンドはこの入力補完機能をどのように表示するかを設定できます。

```bash
complete [オプション] [name]
```

nameは基本的にコマンドやファイル名を設定する。
シェルでnameを入力した後にTabを入力するとcompleteコマンドで設定した補完が表示される。

```bash
complete             # completeの一覧を表示
complete | grep git  # completeの一覧からgitを含むものを抽出
complete -r name     # nameのcompleteを削除する
```

- See: <https://linuxcommand.net/complete/>
