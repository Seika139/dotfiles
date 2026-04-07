# mise を Ubuntu on Windows 上で利用する

参考: <https://mise.jdx.dev/getting-started.html>

## CPU が AMD/Intel 系か ARM 系かを調べる

```bash
# wsl 上で
$ lscpu | grep Architecture
Architecture:                    x86_64
```

この出力が x86_64 なら AMD/Intel 系、aarch64 なら ARM 系。

## mise のインストール

ref: <https://mise.jdx.dev/installing-mise.html>

```bash
sudo apt update -y && sudo apt install -y curl
sudo install -dm 755 /etc/apt/keyrings
curl -fSs https://mise.jdx.dev/gpg-key.pub | sudo tee /etc/apt/keyrings/mise-archive-keyring.asc 1> /dev/null
echo "deb [signed-by=/etc/apt/keyrings/mise-archive-keyring.asc] https://mise.jdx.dev/deb stable main" | sudo tee /etc/apt/sources.list.d/mise.list
sudo apt update -y
sudo apt install -y mise
```

> **Note:** 以前は AMD/Intel 系と ARM 系で `arch=amd64` / `arch=arm64` の指定が必要だったが、現在は不要。
