# VPC (Virtual Private Cloud)

## 一言でいうと

AWS 上に構築する自分専用の仮想ネットワーク。すべての AWS リソース（ECS, RDS, ALB 等）はこの中に配置される。

## なぜ必要？

| メリット | 説明 |
|---|---|
| セキュリティ | 通信経路を絞ってアクセスを制御 |
| スケーラビリティ | ALB 等で負荷分散が可能 |
| 可用性 | マルチ AZ 構成で障害に強い |
| 管理性 | IaC（CDK）で構成をコード管理 |

## VPC の構造

```text
AWS リージョン（ap-northeast-1 = 東京）
  └── VPC (10.1.0.0/22)
        ├── AZ-a
        │   ├── Public サブネット (10.1.0.0/26)   ← ALB, NAT Gateway
        │   ├── Private App サブネット (10.1.0.128/25)  ← ECS コンテナ
        │   └── Private Data サブネット (10.1.1.0/26)   ← RDS, ElastiCache
        └── AZ-c
            ├── Public サブネット (10.1.1.64/26)
            ├── Private App サブネット (10.1.2.0/25)
            └── Private Data サブネット (10.1.1.128/26)
```

## 3層サブネット構成

| 層 | サブネットタイプ | 配置するもの | インターネットアクセス |
|---|---|---|---|
| Public | `PUBLIC` | ALB, NAT Gateway | 直接可能（IGW 経由） |
| Private App | `PRIVATE_WITH_EGRESS` | ECS コンテナ | 外向きのみ（NAT 経由） |
| Private Data | `PRIVATE_ISOLATED` | RDS, ElastiCache | 不可 |

## 主要コンポーネント

### インターネットゲートウェイ (IGW)

VPC とインターネットを繋ぐ出入口。パブリックサブネットに必須。

```text
インターネット ←→ IGW ←→ パブリックサブネット
```

### NAT Gateway

プライベートサブネットから**外向きのみ**インターネットにアクセスするための中継。パブリックサブネット上に配置する。

```text
Private App サブネット → NAT Gateway（Public サブネット内）→ IGW → インターネット
                         ↑ 外向きのみ。外部からの直接アクセスは不可
```

### VPC エンドポイント

インターネットを経由せずに AWS サービス（S3, ECR, Secrets Manager 等）にアクセスする仕組み。

| 種類 | 料金 | 例 |
|---|---|---|
| Gateway | **無料** | S3, DynamoDB |
| Interface | 有料（$0.014/時間） | ECR, Secrets Manager, KMS |

Private Data サブネットの RDS がインターネットに出られなくても、VPC エンドポイント経由で Secrets Manager 等にアクセスできる。

## マルチ AZ

複数の AZ（データセンター）にリソースを分散配置することで、1つの AZ が障害を起こしてもサービスが継続する。

```text
AZ-a が障害 → AZ-c の ALB, ECS, RDS スタンバイが引き継ぐ
```

AWS のベストプラクティスで推奨されている構成。

## AWS 予約 IP アドレス

各サブネットの先頭 4 つと末尾 1 つは AWS が予約しており使用不可。

| アドレス | 用途 |
|---|---|
| `.0` | ネットワークアドレス |
| `.1` | VPC ルーター |
| `.2` | DNS サーバー |
| `.3` | 将来の利用のため |
| `.255` | ブロードキャスト |

`/26`（64 アドレス）のサブネットなら、実際に使えるのは **59 アドレス**。

## 社内ルール

- VPC は他アカウントのネットワークと重複しないよう設計が必要
- 新規 VPC 作成はインフラセクションに相談

## 関連サービス

- **ネットワーク基礎**: IP アドレス、CIDR、NAT 等の基礎知識 → [network.md](./network.md)
- **ALB**: パブリックサブネットに配置してトラフィックを受ける → [alb.md](./alb.md)
- **ECS**: Private App サブネットでコンテナを実行 → [ecs.md](./ecs.md)
- **RDS**: Private Data サブネットに配置 → [rds.md](./rds.md)
