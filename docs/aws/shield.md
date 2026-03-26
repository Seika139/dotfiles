# Shield Standard

## 一言でいうと

ネットワーク層の DDoS 攻撃を **自動で** 防いでくれる無料の防御サービス。

## 何をするもの？

大量のパケットを送りつけてサービスをダウンさせる DDoS（Distributed Denial of Service）攻撃から、AWS リソースを自動的に保護する。

```text
攻撃者 ──(大量トラフィック)──→ [Shield Standard: 自動検知・緩和]
                                  ↓ 正常なトラフィックのみ通過
                               CloudFront / ALB → ECS
```

## Shield Standard vs Shield Advanced

| | Shield Standard | Shield Advanced |
|---|---|---|
| 料金 | **無料** | $3,000/月〜 |
| 有効化 | **自動（何もしなくてよい）** | 手動で有効化 |
| 保護対象 | CloudFront, Route 53, ALB 等 | 左記 + EC2, EIP, Global Accelerator |
| 防御する攻撃 | L3/L4（ネットワーク/トランスポート層） | L3/L4 + L7（アプリケーション層） |
| DDoS レスポンスチーム | なし | 24/365 で AWS のチームが対応 |
| コスト保護 | なし | DDoS によるスケールアウト費用を AWS が補填 |

## 社内向けサービスでの判断

**Shield Standard（無料）で十分**。理由：

1. ALB の SG で社内 IP のみに制限しているため、外部からの DDoS リスクは低い
2. CloudFront を導入すれば自動で Shield Standard が適用される
3. Shield Advanced は月 $3,000〜なので、社内ツールには過剰

## 何もしなくてよい理由

Shield Standard は AWS アカウントを作成した時点で自動的に有効化されている。設定画面もない。CloudFront や ALB を使っている時点で、ネットワーク層の DDoS 対策は既に動いている。

## WAF との違い

| | Shield Standard | WAF |
|---|---|---|
| 防御する層 | L3/L4（SYN flood, UDP flood 等） | L7（SQL インジェクション, XSS, レートリミット等） |
| 設定 | 不要（自動） | ルールの設定が必要 |
| 料金 | 無料 | 有料（$5/Web ACL〜） |
| 役割 | ネットワークレベルの洪水を止める | アプリケーションレベルの悪意あるリクエストを止める |

両者は補完関係にある。Shield がネットワークの洪水を止め、WAF がアプリケーションへの攻撃を止める。

## 関連サービス

- **CloudFront**: Shield Standard が自動適用される → [cloudfront.md](./cloudfront.md)
- **WAF**: アプリケーション層の防御を担当 → [waf.md](./waf.md)
- **ALB**: Shield Standard の保護対象 → [alb.md](./alb.md)
