# Gemini CLI

## Dev Container での導入方法

.devcontainer ディレクトリに以下の内容で `Dockerfile` を作成します。
これで開発環境で Gemini CLI を使用できるようになります。

```Dockerfile
# 開発環境用Dockerfile
FROM node:24-slim

# 必要なパッケージのインストール
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install git bash-completion make \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# pnpmのインストール
RUN npm install -g pnpm

# 作業ディレクトリの設定
WORKDIR /workspaces/app

# ユーザー設定
USER root
RUN apt-get update && \
    npm install -g @anthropic-ai/claude-code @google/gemini-cli \
    apt-get clean -y && rm -rf /var/lib/apt/lists/*
USER node
```
