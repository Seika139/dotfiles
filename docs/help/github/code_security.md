# GitHub Code Security

GitHub Code Security は、code scanning / CodeQL alerts など、コード上の脆弱性やエラーを検出して alert として扱うための機能。

## 設定場所

1. リポジトリの `Settings` を開く。
2. `Security` セクションの `Advanced Security` を開く。
3. `Code Security` の状態を確認する。
4. `Enable` できる場合は有効化する。
5. organization / enterprise のポリシーでブロックされている場合は、ポリシー管理者にアクセスを依頼する。

## Code Scanning

Code scanning は、GitHub リポジトリ内のコードを分析して、セキュリティ脆弱性やコーディングエラーを見つける機能。結果はリポジトリの alert として表示される。

### 設定場所

Code Security を Enabled にすると `Security and quality` タブに `Code scanning` が表示され、リポジトリ全体の alert を確認できる。

## CodeQL

CodeQL は GitHub が開発しているコード分析エンジンで、CodeQL データベースを作成し、クエリを実行して以下のような脆弱性やエラーを検出する。

- SQL Injection
- XSS
- SSRF
- Command Injection
- Path Traversal
- 認証・認可不備

CodeQL による分析結果は code scanning alert として GitHub に表示される。

CodeQL の code scanning 分析には主に次の方法がある。

- default setup: GitHub 側で言語・クエリ・トリガーを自動選択する。
- advanced setup: `.github/workflows/` に CodeQL workflow を追加してカスタマイズする。
- external CI: CodeQL CLI を外部 CI で実行し、結果を GitHub にアップロードする。

## 403 になる理由

非公開または内部リポジトリで Code Security が無効な状態だと、code scanning を使う操作は `GitHub Code Security or GitHub Advanced Security must be enabled` 系の 403 になる。

この状態では、次の操作は期待通りに使えない。

- code scanning alerts の取得
- CodeQL alert の確認
- SARIF アップロードによる code scanning result の登録
- Code scanning alert に対する Copilot Autofix

## Code Quality との違い

Code Quality も CodeQL を使うが、Code Security の code scanning alerts とは別の機能。

- Code Security: セキュリティ脆弱性やエラーを code scanning alert として扱う。
- Code Quality: 品質問題、保守性、信頼性、PR コメント、品質スコアを扱う。

そのため、Code Quality の dynamic CodeQL quality scan が成功していても、Code Security の code scanning alerts が有効とは限らない。

## 有効化が必要なとき

Code scanning alerts や Copilot Autofix for code scanning を使いたい場合は、対象リポジトリで Code Security を有効化する必要がある。

## 参考

- [Code scanning](https://docs.github.com/ja/code-security/concepts/code-scanning/code-scanning)
- [CodeQL を使用したコード スキャン](https://docs.github.com/ja/code-security/concepts/code-scanning/codeql/codeql-code-scanning)
- [Code Security を有効にする必要があるエラー](https://docs.github.com/ja/code-security/reference/code-scanning/troubleshoot-analysis-errors/advanced-security-must-be-enabled)
- [コード スキャン用の REST API エンドポイント](https://docs.github.com/ja/rest/code-scanning/code-scanning)
