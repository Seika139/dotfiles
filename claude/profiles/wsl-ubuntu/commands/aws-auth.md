# AWS 認証情報と環境変数の注意事項

## AWS SDK の認証情報の優先順位

AWS SDK / CLI は以下の順序で認証情報を解決する（上が優先）:

1. **環境変数**: `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN`
2. **プロファイル**: `--profile` オプション / `AWS_PROFILE` 環境変数
3. **共有認証情報ファイル**: `~/.aws/credentials`
4. **SSO キャッシュ**: `~/.aws/sso/cache/`
5. **インスタンスメタデータ**: EC2 / ECS のロール

**重要**: 環境変数 `AWS_PROFILE` が設定されていると、`--profile` オプションを指定しない `aws` コマンドはその環境変数のプロファイルで動作する。

## 使用者の環境での問題

この環境では `~/.aws/sso` を利用した SSO 認証で AWS 環境にアクセスする。
一方で Claude Code の Bedrock API 呼び出しのために、CCWB (claude-code-with-bedrock 認証ヘルパー) が次の構成を `~/.claude/settings.json` に注入している:

- `awsAuthRefresh`: `~/claude-code-with-bedrock/bin/credential-process` を呼び出して短命の AWS 認証情報を取得する
- `env.AWS_PROFILE`: `ccwb-prod-apne-1` (Bedrock 専用プロファイル)
- `env.AWS_REGION`: `us-east-1`
- `env.CREDENTIAL_PROCESS_PATH`: 認証ヘルパーへの絶対パス

このため、Claude Code から起動した子プロセス（mise タスクや bash コマンド）には常に `AWS_PROFILE=ccwb-prod-apne-1` が export された状態になる。`--profile` を指定せずに `aws` コマンドを実行すると、AWSのユーザーとして設定されている AWS アカウントではなく **Bedrock 用プロファイル**で動作してしまう。

なお、旧運用では Claude Code に静的な `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` を注入していたが、現在は CCWB の `credential_process` 経由で短命キーが都度発行される方式に切り替わっている。静的キーは基本的に env に乗らないが、`credential_process` の動作タイミングによっては短時間 export される可能性があるため、念のため後述の `unset` を併用する。

### 症状

- `aws` コマンドが意図しないアカウントで実行される
- `cdk deploy` が `AccessDenied` やリージョン不一致で失敗する
- `--profile` を付けても効果がないように見える（env が優先されるため）

### 対処法

AWS コマンドを直接実行する前に、Bedrock 用 env を退避する:

```bash
unset AWS_PROFILE AWS_REGION AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_SECURITY_TOKEN
# その上で SSO プロファイルを指定
aws --profile <SSO プロファイル名> ...
```

または `AWS_PROFILE` を直接書き換えて実行する:

```bash
AWS_PROFILE=<SSO プロファイル名> aws ...
```

### mise タスクは安全

開発プロジェクトの `mise.toml` で AWS タスクを定義する場合、各タスクの冒頭で上記 `unset` を実行するように定める。Claude Code 経由でも端末から直接でも再現性を保つため、AWS コマンドは可能な限り mise タスクに記述し、`mise run` 経由で実行することを推奨する。
