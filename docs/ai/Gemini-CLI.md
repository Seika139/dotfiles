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

**参考**:

- [Gemini-CLI を Docker コンテナ内で限定して動作させてみる](https://deep.tacoskingdom.com/blog/276)

## VPS での導入方法

VPS 上にまず pnpm と Node.js をインストールします。

```bash
# pnpm のインストール
# pnpm 公式 (https://pnpm.io/ja/installation) の手順に従ってインストール
curl -fsSL https://get.pnpm.io/install.sh | sh -
# Node.js のバージョンを指定してインストール
pnpm env use --global 24
```

この状態で Gemini CLI をインストールします。

```bash
pnpm add -g @google/gemini-cli
```

または `package.json` に以下の内容を追加して、`pnpm install` を実行します。

```json
{
  "dependencies": {
    "@google/gemini-cli": "^0.1.0"
  }
}
```

### Gemini CLI の認証

ブラウザを開かずにコマンドラインで操作を完結させる必要があります。

```bash
export NO_BROWSER=true
pnpm exec gemini
```

初回のみ認証が必要ですが、次回以降は認証は不要です。

**参考**:

- [Gemini CLI を解説 - G-gen Tech Blog](https://blog.g-gen.co.jp/entry/gemini-cli-explained)
