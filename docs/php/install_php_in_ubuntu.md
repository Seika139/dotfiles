# Ubuntu に PHP をインストールする方法

VS Code で php の開発をしていて、いままでは docker 上の php に依存していたが、ローカル VS Code で phpcbf などを実行するにはローカルに php をインストールする必要があったので、そのときの対応内容をメモしておく。

## 手順

```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:ondrej/php
sudo apt install php8.4
```

それだけだと phpcs が以下のエラーで動かなかったので、必要な拡張モジュールをインストールする。

```bash
./vendor/bin/phpcs --version
ERROR: PHP_CodeSniffer requires the tokenizer, xmlwriter and SimpleXML extensions to be enabled. Please enable xmlwriter and SimpleXML.
```
