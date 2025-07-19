# Claude Code

現状 Claude Code を無料で使う方法はないので、一旦 Dev Container の Dockerfile で導入する方法だけ記載しておく。

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
