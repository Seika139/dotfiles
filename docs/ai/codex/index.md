# Codex

Anthropic の Claude Code, Google の Gemini CLI のように、OpenAI でも Codex CLI というコード生成に特化したツールが提供されているので、CLI や VS Code の拡張機能で利用するための方法を記載する。

※ Windows で Codex を利用する場合は、[Windows で Codex を利用する場合](codex_on_windows.md)を参照。

- [Codex](#codex)
  - [導入](#導入)
    - [API KEY の取得](#api-key-の取得)
    - [CLI で Codex を利用する](#cli-で-codex-を利用する)
    - [VS Code で Codex を利用する](#vs-code-で-codex-を利用する)
  - [Codex の設定](#codex-の設定)
    - [AGENTS.md](#agentsmd)
    - [config.toml](#configtoml)

## 導入

### API KEY の取得

- <https://platform.openai.com/settings/organization/api-keys>

上記のリンクから API KEY を作成し、キーを控えておく。

### CLI で Codex を利用する

<https://developers.openai.com/codex/cli>

```bash
# npm または Homebrew でインストール
npm install -g @openai/codex
brew install codex

# codex コマンドが実行可能になる
codex --help
```

ターミナルで利用する場合は、環境変数 `OPENAI_API_KEY` に API KEY を設定する。
export コマンドで環境変数にセットしておくと、環境変数として永続化されるが、他のセッションからも利用される可能性があるので注意。
set コマンドでシェル変数として設定しておくと現在のセッションでしか有効にならないので、他のセッションから利用されないという意味では安全。

```bash
export OPENAI_API_KEY="sk-xxxxxx"
set OPENAI_API_KEY="sk-xxxxxx"
```

### VS Code で Codex を利用する

Open AI が提供する Codex 拡張機能をインストールする。
Codex のウィンドウを開いて「Continue with API Key」をクリックし、API Key を入力する。

## Codex の設定

### AGENTS.md

`~/.codex/AGENTS.md` に共通プロンプトを記載する。
`AGENTS.md` は Codex をはじめ、Cursor や GitHub Copilot,Gemini CLI, Roo Code など多くの AI ツールが共通して利用することができる Custom Instructions のファイル名だが、claude は未対応。 → <https://agents.md/>

### config.toml

Codex CLI の設定は、基本的に `~/.codex/config.toml` で行う。
設定方法は OpenAI の GitHub を見るのが確実。

- <https://github.com/openai/codex/blob/main/docs/config.md>
