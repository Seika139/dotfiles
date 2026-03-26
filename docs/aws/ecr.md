# ECR (Elastic Container Registry)

## 一言でいうと

Docker イメージを保管する AWS 版の「コンテナ倉庫」。Docker Hub の AWS 版。

## 何をするもの？

ローカルや CI でビルドした Docker イメージを push し、ECS / Fargate がそこから pull してコンテナを起動する。

```text
開発者の PC / GitHub Actions
  ↓ docker push
ECR（イメージを保管）
  ↓ docker pull
ECS / Fargate（コンテナを起動）
```

## 主要な概念

| 概念 | 説明 |
|---|---|
| リポジトリ | 1つのサービスに対応するイメージの保管場所（例: `spark-prd-auth`） |
| イメージタグ | イメージのバージョン（例: `latest`, `v1.2.3`, `abc123`） |
| ライフサイクルポリシー | 古いイメージを自動削除するルール |

## Docker Hub との違い

| | Docker Hub | ECR |
|---|---|---|
| 場所 | インターネット上 | 自分の AWS アカウント内 |
| 認証 | Docker Hub アカウント | IAM（AWS の認証） |
| ネットワーク | インターネット経由 | VPC エンドポイント経由で閉域通信も可能 |
| 料金 | 無料枠あり（制限付き） | 保存量 + 転送量の従量課金 |

## 料金の目安

- ストレージ: $0.10/GB/月
- データ転送: 同一リージョン内は無料

## 関連サービス

- **ECS**: ECR からイメージを取得してコンテナを起動 → [ecs.md](./ecs.md)
- **Fargate**: 同上 → [fargate.md](./fargate.md)
