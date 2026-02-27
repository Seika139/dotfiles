# AWS 認証情報と環境変数の注意事項

## AWS SDK の認証情報の優先順位

AWS SDK / CLI は以下の順序で認証情報を解決する（上が優先）:

1. **環境変数**: `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN`
2. **プロファイル**: `--profile` オプション / `AWS_PROFILE` 環境変数
3. **共有認証情報ファイル**: `~/.aws/credentials`
4. **SSO キャッシュ**: `~/.aws/sso/cache/`
5. **インスタンスメタデータ**: EC2 / ECS のロール

**重要**: 静的認証情報（環境変数）は常に `--profile`（SSO）より優先される。

## 使用者の環境での問題

この環境では ~/.aws/sso を利用して SSO 認証を行う方法で AWS 環境にアクセスする。
一方で Claude Code の Bedrock API 呼び出し用にデフォルトで `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` を注入している。そのため、各種AWSコマンドを実行するさいに --profile で SSO を指定しても、環境変数の静的認証情報が優先されてしまい、意図しないアカウントでコマンドが実行される問題が発生する。

### 症状

- `aws` コマンドが意図しないアカウントで実行される
- `cdk deploy` が `AccessDenied` やリージョン不一致で失敗する
- `--profile` を付けても効果がない

### 対処法

AWS コマンドを直接実行する前に、必ず静的認証情報を unset する:

```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_SECURITY_TOKEN
```

### mise タスクは安全

開発プロジェクトのリポジトリで `mise.toml` をつかって AWS のタスクを定義する場合、これらのタスクの冒頭で上記 `unset` を実行するように定める。
Claude Code の実行以外でも再現性を保つため、AWS コマンドは可能な限り mise タスクに記述し、記述したタスクを `mise run` 経由で実行することを推奨する。
