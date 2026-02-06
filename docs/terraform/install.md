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
