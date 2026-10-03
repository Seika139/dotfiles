# mise による Node.js と CLI の管理

この dotfiles は従来 Volta が管理していた Node.js と CLI を、PC ごとの mise profile で管理します。既存の Brew や pnpm が所有するツールは従来の管理を維持します。

## プロファイル

`bash/daily/.env` の `DAILY_PROFILE` が選択元です。未設定なら `default` を使います。`.active-profile` はテーマ等に使う別設定です。

| DAILY_PROFILE | 管理するツール |
| --- | --- |
| `default` | mise 管理ツールなし |
| `cg-m2-mac` | Node.js、dotenvx、GitHub Copilot、AWS CDK、pnpm |
| `hm-m1-mac` | Node.js、Codex CLI |
| `win-15034` | Node.js、Codex CLI、AWS CDK、dotenvx、clasp、GitHub Copilot、ccusage、TypeScript、webpack |
| `wsl-ubuntu` | Node.js、npm、dotenvx、GitHub Copilot、Codex CLI、AWS CDK、ccusage、difit、markdownlint-cli2、pnpm |
| `xsv-linux-1` | mise 管理ツールなし（ccusage は従来どおり pnpm 管理） |

設定は `mise/profiles/<DAILY_PROFILE>.toml` にあります。`.env` では `DAILY_PROFILE=値` の形式だけが有効です。値は英数字、`_`、`-` で構成し、引用符、`export`、inline comment、重複行は拒否します。`install.sh` は `.env` を実行せずに値を読み取ります。対応する通常ファイルが存在するときだけ `${MISE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/mise}/conf.d/dotfiles-profile.toml` にリンクし、ホームディレクトリで `mise install` を実行します。未知のprofile、無効値、既存ユーザー設定ファイル、dotfiles以外のsymlinkは上書きせず、profile toolsも導入しません。

Daily更新はMac/Windowsでは従来の Volta 更新対象に限って `mise upgrade` を実行します。WSL Ubuntuでは従来どおりmiseの全ツールをホームディレクトリで更新します。WSLのprofileはNode.js/npmと登録CLIを `latest` で追跡します。

## プロファイルの切り替え

`bash/daily/.env` の `DAILY_PROFILE` を変更して `install.sh` を再実行してください。管理リンクが選択済みprofileへ切り替わり、そのprofileのツールがインストールされます。`unlink.sh` はdotfiles配下のprofile manifestを指す所有symlinkだけを解除します。

```bash
cd "$HOME/dotfiles"
bash install.sh
cd "$HOME"
mise ls
node --version
codex --version
```

## Codex CLI

mise の [npm backend](https://mise.jdx.dev/dev-tools/backends/npm.html) は `npm:<package>` 形式のツール指定を扱います。Codex CLI は `mise/profiles/<DAILY_PROFILE>.toml` で `npm:@openai/codex` として管理します。これはOpenAIの[公式インストール案内](https://github.com/openai/codex#installation)にある npm パッケージ `@openai/codex` に対応します。

## 既存のVolta環境

このリポジトリはVoltaを自動削除しません。対象PCでprofile表の各コマンドを `command -v <command>` または `mise which <tool>` で確認し、選択profileのツールがmiseから解決されることを確かめてから、そのOS側のVoltaを手動で削除してください。Windows、WSL、macOSはPATHが別なので、それぞれのシェルで確認してから削除します。`brew uninstall volta` はHomebrewで入れたVoltaを削除します。Windows PowerShellなど、このBash設定を読まないシェルのPATHも別途確認してください。
