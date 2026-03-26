# Route 53

## 一言でいうと

ドメイン名（`spark.cygames.jp` など）を IP アドレスに変換する「電話帳」。AWS が提供する DNS サービス。

## 何をするもの？

ブラウザに `https://spark.cygames.jp` と入力すると、まず「このドメインの IP アドレスは？」という問い合わせが走る。Route 53 がその問い合わせに答えて、ALB や CloudFront の IP アドレスを返す。

```text
ブラウザ: 「spark.cygames.jp はどこ？」
  ↓
Route 53: 「ALB の IP アドレスはこれだよ」
  ↓
ブラウザ → ALB → ECS
```

## 主要な概念

### ホストゾーン

あるドメイン（例: `spark.cygames.jp`）の DNS レコードをまとめて管理する入れ物。

```text
ホストゾーン: spark.cygames.jp
  ├── A レコード:   spark.cygames.jp     → ALB の IP
  ├── A レコード:   stg.spark.cygames.jp → stg 用 ALB の IP
  └── CNAME レコード: _acme-challenge... → ACM の DNS 検証用
```

### サブドメイン委譲

親ゾーン（`cygames.jp`）に「`spark.cygames.jp` の問い合わせはこっちに聞いて」と NS レコードを登録すること。これにより別の AWS アカウントでサブドメインを自由に管理できる。

```text
cygames.jp のゾーン（cygames-infra アカウント）
  └── NS レコード: spark.cygames.jp → 別アカウントの Route 53

spark.cygames.jp のゾーン（自チームのアカウント）
  ├── A レコード: spark.cygames.jp → ALB
  └── CNAME: _xxx.spark.cygames.jp → ACM 検証用
      ↑ 自由に追加・変更できる
```

## よく使う DNS レコードの種類

| レコード | 用途 | 例 |
|---|---|---|
| A | ドメイン → IP アドレス | `spark.cygames.jp → 203.0.113.10` |
| AAAA | ドメイン → IPv6 アドレス | A の IPv6 版 |
| CNAME | ドメイン → 別のドメイン名 | `www.spark.cygames.jp → spark.cygames.jp` |
| NS | サブドメインの委譲先 | `spark.cygames.jp → ns-xxx.awsdns-xx.com` |
| Alias | AWS リソースへの直接参照 | `spark.cygames.jp → ALB の DNS 名`（A レコードの AWS 拡張版。Zone Apex でも使える） |

## 社内ルール

- Route 53 のゾーンファイルは親アカウント `cygames-infra` に集約されている
- 新しいゾーンが必要な場合はインフラセクションへ依頼
- 自チームのアカウントでホストゾーンを作成し、親ゾーンに NS 委譲してもらう運用が可能

## 料金

- ホストゾーン: $0.50/月
- DNS クエリ: 100万クエリあたり $0.40（社内向けなら微小）

## 関連サービス

- **ACM**: DNS 検証で証明書を発行する際に Route 53 のレコードを使う → [acm.md](./acm.md)
- **ALB**: A/Alias レコードで ALB にトラフィックを向ける → [alb.md](./alb.md)
- **CloudFront**: Alias レコードで CloudFront にトラフィックを向ける → [cloudfront.md](./cloudfront.md)
