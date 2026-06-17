# GitHub Secret Protection

GitHub Secret Protection は、secret scanning / push protection / validity checks などを使い、漏洩した資格情報の検出と、将来の漏洩防止を行うための機能。

## 今回の確認結果

以下は 2026-06-15 に共有された対象リポジトリの確認メモ。

| 機能                      | 状態                                                 |
| ------------------------- | ---------------------------------------------------- |
| secret scanning           | alert 読み取り可                                     |
| Push protection           | `secret_scanning_push_protection=enabled`            |
| AI detection              | `secret_scanning_ai_detection=enabled`               |
| Non-provider patterns     | `secret_scanning_non_provider_patterns=enabled`      |
| Validity checks           | `secret_scanning_validity_checks=enabled`            |
| Delegated bypass          | `secret_scanning_delegated_bypass=disabled`          |
| Delegated alert dismissal | `secret_scanning_delegated_alert_dismissal=disabled` |

## Secret scanning

Secret scanning は、Git 履歴や GitHub 上の対象コンテンツをスキャンし、API キー・パスワード・トークンなどのハードコードされた資格情報を検出する。

alert が作成された場合は、原則として次の順で対応する。

1. 影響する資格情報を失効またはローテーションする。
2. 利用ログを確認し、不正利用の有無を確認する。
3. 必要に応じて履歴からシークレットを削除する。
4. alert を解決状態にする。

履歴削除は、資格情報の失効後であれば必ずしも最優先ではない。先にローテーションする。

## Push protection

Push protection は、シークレットを含む push がリポジトリに到達する前にブロックする secret scanning 機能。

対象になり得る操作:

- コマンドラインからの push
- GitHub UI での commit
- GitHub へのファイルアップロード
- REST API でのファイル作成・更新
- GitHub MCP server との連携操作

今回の確認では `secret_scanning_push_protection=enabled` なので、将来のシークレット混入防止が有効。

## Non-provider patterns

Non-provider patterns は、特定のサービスプロバイダーに紐づかないシークレットを検出するためのパターン。

例:

- 秘密鍵
- 接続文字列
- 汎用 API キー
- 認証ヘッダー

プロバイダー固有のトークンだけでは拾えない漏洩を補完する。

## AI detection

AI detection は、Copilot secret scanning の generic secret detection として、既知の provider pattern や custom pattern だけでは検出しにくい非構造化シークレットを検出する。

例:

- パスワードらしい文字列
- 構造化されていない資格情報

GitHub Copilot の通常サブスクリプションとは別に、GitHub Secret Protection が有効な organization / enterprise 所有リポジトリで使う機能として整理する。

## Validity checks

Validity checks は、検出されたシークレットが現在も有効かどうかを発行元サービスに確認し、修復優先度を判断しやすくする機能。

状態の見方:

- `active`: まだ有効な可能性が高く、最優先でローテーションする。
- `inactive`: 既に無効化済みの可能性がある。
- `unknown`: 有効性を判定できていない。

今回の確認では `secret_scanning_validity_checks=enabled` なので、検出後の優先順位付けに利用できる。

## 委任系の設定

今回の確認では次が無効。

- `secret_scanning_delegated_bypass=disabled`
- `secret_scanning_delegated_alert_dismissal=disabled`

つまり、push protection の bypass や secret scanning alert の dismissal に対して、レビュー担当者に承認を委任する運用はまだ入っていない。

監査やコンプライアンス上、例外や alert close にレビューを必須化したい場合は、delegated bypass / delegated alert dismissal の有効化を検討する。

## 参考

- [価格と有効化 GitHub Secret Protection](https://docs.github.com/ja/code-security/how-tos/secure-at-scale/configure-organization-security/configure-specific-tools/protect-your-secrets)
- [シークレット スキャン](https://docs.github.com/ja/code-security/concepts/secret-security/secret-scanning)
- [プッシュプロテクション](https://docs.github.com/ja/code-security/concepts/secret-security/push-protection)
- [有効性チェック](https://docs.github.com/ja/code-security/concepts/secret-security/validity-checks)
- [Enabling secret scanning for non-provider patterns](https://docs.github.com/code-security/how-tos/secure-your-secrets/detect-secret-leaks/enabling-secret-scanning-for-non-provider-patterns)
- [Enabling Copilot secret scanning's generic secret detection](https://docs.github.com/en/enterprise-cloud@latest/code-security/how-tos/secure-your-secrets/detect-secret-leaks/enabling-ai-powered-generic-secret-detection)
