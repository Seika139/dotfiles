# dotenvx

**公式サイトのドキュメント**: <https://dotenvx.com/docs>

**目次**

- [dotenvx](#dotenvx)
  - [概要](#概要)
  - [Install](#install)
  - [encrypt / decrypt コマンド](#encrypt--decrypt-コマンド)
  - [自前で用意した秘密鍵を利用して encrypt する](#自前で用意した秘密鍵を利用して-encrypt-する)
  - [run](#run)

## 概要

dotenvx を使うと、環境変数ファイル（例: `.env`）を暗号化してバージョン管理システムに安全に保存できます。
dotenvx は OpenSSL を利用してファイルを暗号化・復号化するため、Git リポジトリにコミットしても秘匿性の高い情報が漏洩するリスクを軽減できます。
また、dotenvx は既存の dotenv 互換の環境変数ファイルをそのまま利用できるため、Next.js プロジェクトへの導入も容易です。

代わりに .env を暗号化・復号化する鍵が `.env.keys` に保存されるため、このファイルは必ず `.gitignore` に追加してバージョン管理から除外してください。

**`.env.keys` の例**

```plain
#/------------------!DOTENV_PRIVATE_KEYS!-------------------/
#/ private decryption keys. DO NOT commit to source control /
#/     [how it works](https://dotenvx.com/encryption)       /
#/           backup with: `dotenvx ops backup`              /
#/----------------------------------------------------------/

# .env
DOTENV_PRIVATE_KEY=********************************
```

## Install

```bash
brew install dotenvx/brew/dotenvx   # macOS (Homebrew)
npm install @dotenvx/dotenvx --save # Node.js (npm)
curl -sfS https://dotenvx.sh | sh   # Universal (Shell Script)
```

## encrypt / decrypt コマンド

```bash
dotenvx encrypt   # 環境変数ファイルを暗号化
dotenvx decrypt   # 環境変数ファイルを復号化
```

オプションに `-f <file>` を指定することで、デフォルトの `.env` 以外のファイルを暗号化・復号化できます。
この際ファイルを複数指定することも可能です。

```bash
dotenvx encrypt -f .env.production
dotenvx decrypt -f .env.production
```

## 自前で用意した秘密鍵を利用して encrypt する

```bash
DOTENV_PRIVATE_KEY="private_key_your_custom_secret_here" dotenvx encrypt
```

## run

`.env` を暗号化すると、これまで環境変数を利用していたアプリケーションはそのまま動作しなくなります。
なぜなら、アプリケーションが起動する際に `.env` を復号化して環境変数を設定する必要があるためです。
そこで dotenvx では `dotenvx run` コマンドを提供しており、これを使うことでアプリケーション起動時に自動的に環境変数ファイルを復号化して環境変数を設定できます。

```bash
dotenvx run -- <これまで実行していたコマンド>
```
