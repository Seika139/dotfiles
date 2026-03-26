# WAF (Web Application Firewall)

## 一言でいうと

Webアプリケーションへの悪意あるアクセスをブロックする「門番」。

## 何をするもの？

ALB や CloudFront の前段で、リクエストの内容を検査する。SQL インジェクションやクロスサイトスクリプティング（XSS）などの攻撃パターンに合致するリクエストをブロックする。

```text
ブラウザ → CloudFront → [WAF: 検査] → ALB → ECS
                          ↑
                     怪しいリクエストは
                     ここでブロック
```

## なぜ必要？

| 脅威 | WAF の対応 |
|---|---|
| SQL インジェクション | AWS マネージドルールでブロック |
| XSS（クロスサイトスクリプティング） | AWS マネージドルールでブロック |
| 大量リクエスト（DDoS / ブルートフォース） | レートリミットで制御 |
| 既知の悪意ある IP | IP ブラックリストでブロック |

## 主要な概念

### Web ACL（アクセスコントロールリスト）

ルールをまとめたセット。ALB や CloudFront に紐づける。

### ルールの種類

| 種類 | 説明 |
|---|---|
| AWS マネージドルール | AWS が用意した既製のルールセット。すぐ使える |
| カスタムルール | 自分で条件を定義（IP 制限、レートリミット等） |
| ルールグループ | 複数のルールをまとめたもの |

### よく使う AWS マネージドルール

| ルール名 | 内容 |
|---|---|
| `AWSManagedRulesCommonRuleSet` | OWASP Top 10 の主要な攻撃パターンをブロック |
| `AWSManagedRulesKnownBadInputsRuleSet` | Log4Shell 等の既知の脆弱性を突く入力をブロック |
| `AWSManagedRulesSQLiRuleSet` | SQL インジェクション特化 |

### レートリミットの例

```text
- 一般リクエスト: 2000 req / 5分 per IP
- SSE エンドポイント: 100 req / 5分 per IP
- ログイン: 30 req / 5分 per IP
```

## 社内向けサービスでは必要？

| 状況 | 判断 |
|---|---|
| ALB の SG で社内 IP に制限済み | WAF なしでも最低限のセキュリティは確保 |
| CloudFront を導入する場合 | WAF の追加を推奨（CloudFront は SG が使えないため） |
| 本番環境でインターネット公開する場合 | 必須 |

## リージョンに注意

| 紐づけ先 | WAF のリージョン |
|---|---|
| ALB | ALB と同じリージョン（例: `ap-northeast-1`） |
| CloudFront | **必ず `us-east-1`** |

## 料金

- Web ACL: $5/月
- ルール: $1/ルール/月
- リクエスト検査: 100万リクエストあたり $0.60
- 社内向け小規模なら月 $10〜20 程度

## 関連サービス

- **CloudFront**: WAF を紐づける一般的な対象 → [cloudfront.md](./cloudfront.md)
- **ALB**: CloudFront なしの場合、ALB に直接 WAF を紐づけることも可能 → [alb.md](./alb.md)
- **Shield Standard**: WAF とは別に、ネットワーク層の DDoS を自動防御 → [shield.md](./shield.md)
