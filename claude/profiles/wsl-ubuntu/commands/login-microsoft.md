# login-spark

Microsoft OAuth を使ったアプリケーションへのログインを Playwright で自動化する。

引数: ログイン後にアクセスしたい URL（省略時は `http://localhost:8410/`）

## 前提条件

以下の環境変数が設定されていること：

- `MICROSOFT_LOGIN_EMAIL`: Microsoft アカウントのメールアドレス
- `MICROSOFT_LOGIN_PASSWORD`: Microsoft アカウントのパスワード

## 手順

1. **環境変数の読み取り**: Bash ツールで `echo $MICROSOFT_LOGIN_EMAIL` と `echo $MICROSOFT_LOGIN_PASSWORD` を実行し、認証情報を取得する。環境変数が未設定（空文字）の場合はユーザーに設定方法を案内して中断する。

2. **ページへのナビゲート**: 引数で指定された URL（デフォルト: `http://localhost:8410/`）に `browser_navigate` でアクセスする。

3. **リダイレクト確認**: Microsoft のログインページ（`login.microsoftonline.com`）にリダイレクトされることを確認する。すでにログイン済みでチャットページが表示された場合は「ログイン済みです」と報告して完了。

4. **メールアドレス入力**:
   - `browser_snapshot` でページの状態を確認する。
   - メールアドレス入力欄（`textbox` で "email" や "Enter your email" を含むもの）を特定する。
   - `browser_type` でメールアドレスを入力する。
   - "Next" ボタンをクリックする。

5. **パスワード入力**:
   - ページ遷移を待ち（2秒程度）、`browser_snapshot` で状態を確認する。
   - パスワード入力欄（`textbox` で type="password" のもの）を特定する。
   - `browser_type` でパスワードを入力する。
   - "Sign in" または "サインイン" ボタンをクリックする。

6. **「サインインの状態を維持しますか？」への対応**:
   - ページ遷移を待ち（2秒程度）、`browser_snapshot` で状態を確認する。
   - "Stay signed in?" や "サインインの状態を維持しますか？" が表示された場合、"Yes" または "はい" をクリックする。

7. **ログイン完了確認**:
   - 最終的に目的の URL（チャットページなど）にリダイレクトされたことを確認する。
   - `browser_snapshot` でページ内容を確認し、ログインが成功したことをユーザーに報告する。

8. **エラーハンドリング**:
   - ログインに失敗した場合（パスワード間違いなど）は、エラー内容をユーザーに報告する。
   - MFA（多要素認証）が要求された場合は、ユーザーに手動対応を依頼し、完了後にスナップショットで状態を確認する。
