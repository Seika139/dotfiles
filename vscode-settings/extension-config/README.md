# このディレクトリについて

Markdown の整形に関する VS Code 拡張機能の設定ファイルを管理する。

## Markdownlint(davidanson.vscode-markdownlint)

元々は `settings.json` 内で `markdownlint.config` を設定していたが、それが deprecated となった。
代わりに `markdownlint.configFile` を `settings.json` 内で設定し、このディレクトリにある `.markdownlint-cli2.jsonc` ファイルを参照するようにした。

## Rumdl(dorzey.rumdl)

install.sh から ~/.config/rumdl/rumdl.toml への symlink を作る。拡張機能はこのファイルを見に行くので、設定が効く。 markdownlintの方は設定ファイルへのパスに `userHome` という変数を使うことで絶対パスを書かなくて済むが rumdl の方はその設定ができなかったのでこのように対応した。
