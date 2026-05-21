# GitHub で扱うトークンについて

GiHub のアクセストークンには、いくつかの種類があり、それぞれに特定のプレフィックスが付いています。
以下の表は、GitHub のトークンの種類とそのプレフィックス、および関連する情報へのリンクを示しています。

| Token type                                 | Prefix        | More information                                                                                                                                                                                 |
| :----------------------------------------- | :------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Personal access token (classic)            | `ghp_`        | [Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#creating-a-personal-access-token-classic) |
| Fine-grained personal access token         | `github_pat_` | [Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#creating-a-personal-access-token-classic) |
| OAuth access token                         | `gho_`        | [Authorizing OAuth apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)                                                                                  |
| User access token for a GitHub App         | `ghu_`        | [Authenticating with a GitHub App on behalf of a user](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/identifying-and-authorizing-users-for-github-apps)  |
| Installation access token for a GitHub App | `ghs_`        | [Authenticating as a GitHub App installation](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation)                 |
| Refresh token for a GitHub App             | `ghr_`        | [Refreshing user access tokens](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/refreshing-user-access-tokens)                                             |
| GITHUB_TOKEN                               |               | [About GitHub Actions secrets](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)                                                                                |

## Personal access token

現在 GitHub が提供している Personal access token (PAT) には、classic と fine-grained の 2 種類があります。

自分の代わりに GitHub リソースにアクセスすることを目的としています。

### Personal access token (classic)

- prefix: `ghp_`

classic とあるように、昔からあるタイプの Personal access token (PAT) です。
GitHub の API を利用する際に、ユーザーが自分のアカウントに対して発行するトークンで、ユーザー本人としてのアクセス権を持ちます。

**特徴:**

- 広範なスコープを持つことができる
- 特定のリポジトリに制限することは不可

**有効期限**

- デフォルトは30日間だが、無制限に設定することも可能

### Fine-grained personal access token

- prefix: `github_pat_`

classic よりも細かいアクセス制御が可能でセキュリティが向上していますが、classic でしか利用できない機能もあるため、用途に応じて使い分ける必要があります。例えば `package:read` などClassicでは付与できる権限が付与できない場合があります。 → <https://docs.github.com/ja/packages/working-with-a-github-packages-registry/working-with-the-container-registry#container-registry%E3%81%A7%E3%81%AE%E8%AA%8D%E8%A8%BC>

**有効期限:**

- 最大で1年間
- トークン生成時に「Expiration」フィールドで設定必須

## OAuth Access Token

- prefix: `gho_`

OAuthアプリケーションによって生成されるトークンで、ユーザーの代わりにAPIアクセスを行うために使用されます。
ユーザー本人としてのアクセス権を持ちますが、OAuthアプリケーションのスコープに基づいてアクセスが制限されます。
GiTHub CLI で `gh auth login` を実行して GitHub アカウントにログインした場合は、このタイプのトークンが生成されます。

**有効期限:**

- 有効期限なし（ユーザーが無効化しない限り）

## User access token for a GitHub App

- prefix: `ghu_`

GitHub App が、「ユーザーの代理」として動く token。
特定のユーザーアクションを実行するために利用
ユーザーアカウントに紐づいており、ユーザーとして操作を行うために使用

**有効期限:**

- デフォルトで8時間後に期限切れ
- 更新トークンで再作成が可能

## Installation access token for a GitHub App

ユーザーではなく GitHub App Installation つまりアプリとして振る舞います。
個のトークンでコミットやコメントをすると、ユーザーではなくアプリの名前・アイコンが表示されます。

**有効期限:**

- 1時間

## Refresh token for a GitHub App

- prefix: `ghr_`

ユーザーアクセストークンを更新するために使用

**有効期限**

- 6か月

## GITHUB_TOKEN

GitHub Actionsワークフロー内で自動的に生成されるトークン

workflow 内で

```yml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

として定義されます。

デフォルトではリポジトリの内容に対する読み取りおよび書き込み権限を持ちますが、ワークフローファイル内で明示的に権限を設定することも可能です。以下のように `permissions` を指定することが推奨されています。

```yml
permissions:
  contents: read
  pull-requests: write
```

- 外部リソースへのアクセスには使用不可
- リポジトリに限定されたスコープを持つ

### GITHUB_TOKEN で利用できないアクセス許可を要求するトークンが必要な場合

- GitHub App を作成し、ワークフロー内でインストール アクセス トークンを生成します。
  - 詳しくは、[GitHub Actions ワークフローでGitHub アプリを使用して認証済み API 要求を作成する](https://docs.github.com/ja/apps/creating-github-apps/guides/making-authenticated-api-requests-with-a-github-app-in-a-github-actions-workflow) をご覧ください。
- または、personal access tokenを作成して、シークレットとしてリポジトリに格納し、ワークフロー内のトークンを `${{ secrets.SECRET_NAME }}` 構文で使用できます。
  - [個人用アクセス トークンを管理する](https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) および [GitHub Actions でのシークレットの使用](https://docs.github.com/ja/actions/security-guides/encrypted-secrets) を参照してください。

## 参考ページ

- <https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/about-authentication-to-github#githubs-token-formats>
- <https://qiita.com/suin/items/1ce9e11bd1c203fb1167>
