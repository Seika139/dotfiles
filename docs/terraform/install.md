# Terraform をインストールする

## mac

HashiCorp公式のタップ（リポジトリ）を追加してからインストールします。

```bash
# Tapを追加
brew tap hashicorp/tap

# Terraformをインストール
brew install hashicorp/tap/terraform
```

インストールが終わったら、バージョンが表示されるか確認しましょう。

```bash
terraform -v
```

## Linux

公式ページの手順に従ってインストールしてください。

<https://developer.hashicorp.com/terraform/install>

2026年2月時点では Ubuntu/Debian 系の場合、以下のコマンドでインストールできます。

```bash
wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```
