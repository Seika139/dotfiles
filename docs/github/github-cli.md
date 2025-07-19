# GitHub CLI

`gh` コマンドは、GitHub の公式コマンドラインツールです。
これを使うと、ターミナルから GitHub のリポジトリ作成、プルリクエストの管理、イシューの操作など、様々な GitHub 操作を効率的に行うことができます。

## Install

**macOS**

```bash
brew install gh
```

**Ubuntu**

```bash
sudo apt update
sudo apt install gh -y
```

## GitHub の認証

```bash
gh auth login
```

このコマンドを実行すると、GitHub アカウントへの認証が開始されます。以下の手順に従ってください。

1. **認証方法の選択**:
   - `GitHub.com` または `GitHub Enterprise Server` を選択します。
   - 認証方法として `HTTPS` または `SSH` を選択します。
2. **ブラウザでの認証**:
   - ブラウザが開き、GitHub アカウントへのログインを求められます。
   - ログイン後、GitHub CLI が必要な権限を要求します。これを許可してください。
   - VPS 上で実行している場合は、ブラウザが開かないため、表示される URL をコピーして、ローカルのブラウザで開いてください。
3. **認証の完了**:
   - 認証が成功すると、ターミナルに戻り、GitHub CLI が認証情報を保存します。
   - これで、`gh` コマンドを使用して GitHub の操作が可能になります。

## 認証状態の確認

```bash
gh auth status
```

このコマンドを実行すると、現在の認証状態が表示されます。以下の情報が確認できます。

- 認証されているユーザー名
- 認証方法（HTTPS または SSH）
- 認証トークンの有効期限（もしあれば）

## リポジトリの操作

### リポジトリのクローン

```bash
gh repo clone <owner>/<repo>
```

このコマンドを使用して、GitHub 上のリポジトリをローカルにクローンできます。`<owner>` はリポジトリの所有者のユーザー名または組織名、`<repo>` はリポジトリ名です。

### プルリクエストの一覧表示

```bash
gh pr list
```

このコマンドを実行すると、現在のリポジトリに関連するプルリクエストの一覧が表示されます。各プルリクエストのタイトル、状態（オープン、クローズドなど）、作成者などの情報が含まれます。

### プルリクエストの詳細表示

```bash
gh pr view <pr-number>
```

このコマンドを使用して、特定のプルリクエストの詳細情報を表示できます。`<pr-number>` はプルリクエストの番号です。

### プルリクエストの作成

```bash
gh pr create --base <base-branch> --head <head-branch> --title "<PR Title>" --body "<PR Description>"
```

### プルリクエストのマージ

```bash
gh pr merge <pr-number>
```

このコマンドを使用して、特定のプルリクエストをマージできます。`<pr-number>` はマージしたいプルリクエストの番号です。マージ方法（Squash、Rebase、Merge Commit）を選択することもできます。

### Issue の一覧表示

```bash
gh issue list
```

このコマンドを実行すると、現在のリポジトリに関連するイシューの一覧が表示されます。各イシューのタイトル、状態（オープン、クローズドなど）、作成者などの情報が含まれます。

### Issue の詳細表示

```bash
gh issue view <issue-number>
```

このコマンドを使用して、特定のイシューの詳細情報を表示できます。`<issue-number>` はイシューの番号です。

### Issue の作成

```bash
gh issue create --title "<Issue Title>" --body "<Issue Description>"
```

### Issue の編集

```bash
gh issue edit <issue-number> --title "<New Title>" --body "<New Description>"
```

### Issue のクローズ

```bash
gh issue close <issue-number>
```

### リポジトリの作成

```bash
gh repo create <repo-name> --public # または --private
```
