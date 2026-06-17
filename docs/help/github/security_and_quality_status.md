# GitHub Security and Quality 設定の確認メモ

GitHub の Security and quality 周辺機能を確認したときの状態を、機能区分ごとに整理する。

確認日: 2026-06-15

以下の確認結果は、共有された対象リポジトリの確認メモに基づく。

## 全体像

| 区分              | 機能                              | 確認結果                                                |
| ----------------- | --------------------------------- | ------------------------------------------------------- |
| Code Security     | `code_security`                   | `security_and_analysis.code_security.status=disabled`   |
| Code Security     | Code scanning / CodeQL alerts     | API が `Code Security must be enabled` で 403           |
| Code Security     | Dependency Review                 | workflow / ruleset / branch protection に設定なし       |
| Code Security     | Copilot Autofix for code scanning | code scanning alerts が使えないため利用不可             |
| Code Quality      | dynamic CodeQL quality scan       | Python / JS / TS を PR と `main` で成功実行中           |
| Secret Protection | secret scanning                   | alert 読み取り可                                        |
| Secret Protection | Push protection                   | `secret_scanning_push_protection=enabled`               |
| Secret Protection | AI detection                      | `secret_scanning_ai_detection=enabled`                  |
| Secret Protection | Non-provider patterns             | `secret_scanning_non_provider_patterns=enabled`         |
| Secret Protection | Validity checks                   | `secret_scanning_validity_checks=enabled`               |
| Secret Protection | Delegated bypass                  | `secret_scanning_delegated_bypass=disabled`             |
| Secret Protection | Delegated alert dismissal         | `secret_scanning_delegated_alert_dismissal=disabled`    |
| Dependabot        | alerts                            | vulnerability alerts endpoint 204、alerts 27 件確認     |
| Dependabot        | security updates                  | `dependabot_security_updates=enabled`                   |
| Dependabot        | version updates                   | `.github/dependabot.yml` で npm / uv / actions が daily |

## 判断メモ

- Code Security と Code Quality は別機能として扱う。どちらも CodeQL に関係するが、Code Security は code scanning alerts、Code Quality は品質指摘・品質スコア・PR コメントを扱う。
- Code Security が無効な状態では、CodeQL による code scanning alert の取得や SARIF アップロード系の API が 403 になる。
- Code Quality の dynamic CodeQL quality scan が成功していても、Code Security の code scanning alerts が使えることは意味しない。
- Dependency Review は、Dependabot alerts とは別に、PR で依存関係差分を確認・ブロックするための仕組み。現状は workflow / ruleset / branch protection に設定がないため、PR の必須チェックとしては効いていない。
- Secret Protection は主要な検出・防止系の設定が有効。委任系の bypass / alert dismissal は無効なので、レビュー付きの例外運用はまだ入っていない。
- Dependabot は alerts / security updates / version updates を分けて見る。alerts は検知、security updates は脆弱性修正 PR、version updates は通常更新 PR。

## 関連メモ

- [GitHub Security Features の親子関係](./security_features_tree.md)
- [GitHub Advanced Security の課金境界](./advanced_security_billing.md)
- [Code Security](./code_security.md)
- [Dependency Review](./dependency_review.md)
- [Code Quality](./code_quality.md)
- [Secret Protection](./secret_protection.md)
- [Dependabot](./dependabot.md)

## 参考

- [Code scanning](https://docs.github.com/ja/code-security/concepts/code-scanning/code-scanning)
- [CodeQL を使用したコード スキャン](https://docs.github.com/ja/code-security/concepts/code-scanning/codeql/codeql-code-scanning)
- [GitHub のコード品質について](https://docs.github.com/ja/code-security/concepts/about-code-quality)
- [価格と有効化 GitHub Secret Protection](https://docs.github.com/ja/code-security/how-tos/secure-at-scale/configure-organization-security/configure-specific-tools/protect-your-secrets)
- [Dependabot alerts](https://docs.github.com/ja/code-security/concepts/supply-chain-security/dependabot-alerts)
