# uv のインストール

公式情報: <https://docs.astral.sh/uv/getting-started/installation/>

各プラットフォームごとのインストール方法は以下の通りです。

## Standalone installer

```bash
# Mac
curl -LsSf https://astral.sh/uv/install.sh | sh
# その後 ~/.local/bin が PATH に入っていることを確認する

# Devcontainer
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

## Homebrew (Mac)

```bash
brew install uv
```

## Scoop (Windows)

```powershell
scoop install uv
```

## Docker

```Dockerfile
# ベースイメージに使う場合
FROM ghcr.io/astral-sh/uv:latest AS uv

# uv イメージから uv と uvx など必要なものだけをコピーする場合
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.4 /uv /uvx /bin/
```

## upgrade uv by self

uv 自身をアップグレードするには、以下のコマンドを実行します。

```bash
uv self upgrade
uv --version # バージョン確認
```
