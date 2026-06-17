# GitHub Security Features の親子関係

このメモでは、enterprise を GitHub.com 上の GitHub Enterprise Cloud organization 配下のリポジトリとして扱う。GHE.com と GitHub Enterprise Server は、機能境界や契約条件が少し異なるため別扱いにする。

## 位置づけ

GitHub の security / quality 系機能は、次の 4 つに分けて見ると混乱しにくい。

- 全プラン系の supply chain 機能
- GitHub Advanced Security paid products の GitHub Secret Protection
- GitHub Advanced Security paid products の GitHub Code Security
- GitHub Code Quality

CodeQL は SKU ではなく解析エンジン。CodeQL を code scanning として使うなら GitHub Code Security 側、Code Quality として走っているなら GitHub Code Quality 側の機能として扱う。

## ツリー

```text
GitHub security features
├─ 全プラン系
│  ├─ Dependency graph / SBOM
│  ├─ Dependabot alerts
│  ├─ Dependabot security updates
│  └─ Dependabot version updates
│
├─ GitHub Advanced Security paid products
│  ├─ GitHub Secret Protection
│  │  ├─ Secret scanning
│  │  ├─ Push protection
│  │  ├─ Copilot secret scanning / AI detection
│  │  ├─ Custom patterns
│  │  ├─ Validity / metadata checks
│  │  └─ Delegated bypass / dismissal
│  │
│  └─ GitHub Code Security
│     ├─ Code scanning
│     │  ├─ CodeQL
│     │  └─ Third-party SARIF uploads
│     ├─ CodeQL CLI
│     ├─ Copilot Autofix for code scanning
│     ├─ Dependency review
│     ├─ Custom auto-triage rules for Dependabot
│     ├─ Security campaigns
│     └─ Security overview
│
└─ GitHub Code Quality
   └─ CodeQL quality analysis
```

## 判断軸

| 判断したいこと                         | 見る場所                                  |
| -------------------------------------- | ----------------------------------------- |
| 依存関係の可視化や SBOM が必要         | 全プラン系の Dependency graph / SBOM      |
| 既知の脆弱性がある依存関係を検知したい | Dependabot alerts                         |
| 脆弱性修正 PR を自動作成したい         | Dependabot security updates               |
| 通常の依存関係更新 PR を自動作成したい | Dependabot version updates                |
| シークレット漏洩を検知・防止したい     | GitHub Secret Protection                  |
| code scanning alerts を出したい        | GitHub Code Security                      |
| CodeQL のセキュリティ分析を使いたい    | GitHub Code Security の code scanning     |
| PR で依存関係差分をブロックしたい      | GitHub Code Security の Dependency review |
| 品質問題を CodeQL で見たい             | GitHub Code Quality                       |

## CodeQL の扱い

CodeQL は解析エンジンであり、課金 SKU ではない。

同じ CodeQL でも、実行される場所で意味が変わる。

| 使い方                            | 所属                 | 備考                                                    |
| --------------------------------- | -------------------- | ------------------------------------------------------- |
| CodeQL code scanning              | GitHub Code Security | code scanning alerts として扱う                         |
| CodeQL CLI での security analysis | GitHub Code Security | 結果を GitHub にアップロードする場合は code scanning 側 |
| CodeQL quality analysis           | GitHub Code Quality  | Code Security とは別物                                  |

2026-06-15 時点で GitHub Code Quality は public preview。Code Quality 自体は課金されないが、Code Quality scan は GitHub Actions 分を消費する。また、Code Quality の利用に Copilot license や Code Security license は不要と説明されている。

## 既存メモとの対応

- [GitHub Security and Quality 設定の確認メモ](./security_and_quality_status.md)
- [GitHub Advanced Security の課金境界](./advanced_security_billing.md)
- [GitHub Code Security](./code_security.md)
- [GitHub Dependency Review](./dependency_review.md)
- [GitHub Code Quality](./code_quality.md)
- [GitHub Secret Protection](./secret_protection.md)
- [Dependabot](./dependabot.md)

## 参考

- [GitHub security features](https://docs.github.com/en/code-security/getting-started/github-security-features)
- [GitHub のコード品質について](https://docs.github.com/ja/code-security/concepts/about-code-quality)
- [About GitHub Code Quality](https://docs.github.com/en/code-security/concepts/about-code-quality)
- [GitHub Advanced Security license billing](https://docs.github.com/en/billing/concepts/product-billing/github-advanced-security)
