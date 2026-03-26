# CloudFormation

## 一言でいうと

AWS のリソースをコードで定義して自動作成する「インフラの設計図」サービス。

## 何をするもの？

「VPC を作って、ALB を置いて、ECS を動かして...」という手作業をコード（テンプレート）に書き起こし、そのコードから AWS リソースを自動的に作成・更新・削除する。Infrastructure as Code (IaC) の AWS 標準実装。

```text
テンプレート（YAML/JSON）
  ↓ デプロイ
CloudFormation
  ↓ リソース作成
VPC, ALB, ECS, RDS, ...
```

## 主要な概念

| 概念 | 説明 |
|---|---|
| テンプレート | リソースの定義を書いたファイル（YAML or JSON） |
| スタック | テンプレートからデプロイされたリソースの集合。スタック単位で作成・更新・削除される |
| チェンジセット | 更新前に「何が変わるか」をプレビューする機能 |
| ドリフト検出 | 手動変更されたリソースを検出する機能 |

## AWS CDK との関係

AWS CDK は CloudFormation の「上位レイヤー」。CDK で TypeScript や Python のコードを書くと、最終的に CloudFormation テンプレートが生成されてデプロイされる。

```text
CDK（TypeScript / Python）
  ↓ cdk synth
CloudFormation テンプレート（YAML）
  ↓ cdk deploy
CloudFormation API
  ↓
AWS リソース
```

CDK を使っている場合でも、裏側では CloudFormation が動いている。AWS コンソールで「CloudFormation」を開くと、CDK がデプロイしたスタックが見える。

### CDK の構造

CDK のコードは3つの階層で構成される:

| 階層 | 役割 | 対応するファイル |
|---|---|---|
| App | 最上位。複数のスタックを束ねる | `bin/spark-infra.ts` |
| Stack | CloudFormation スタックと 1:1 対応。デプロイ単位 | `lib/stacks/*.ts` |
| Construct | AWS リソースの部品。L1（低レベル）〜 L3（パターン）まである | `lib/constructs/*.ts` |

### Construct のレベル

| レベル | 説明 | 例 |
|---|---|---|
| L1 | CloudFormation リソースと 1:1 対応。全パラメータを明示的に指定 | `CfnBucket` |
| L2 | L1 を抽象化。デフォルト値や便利メソッド付き。**通常はこれを使う** | `Bucket` |
| L3 | 複数リソースを組み合わせたパターン | `BucketDeployment` |

## スタックの状態

| 状態 | 意味 |
|---|---|
| CREATE_COMPLETE | 正常に作成された |
| UPDATE_COMPLETE | 正常に更新された |
| ROLLBACK_COMPLETE | 作成に失敗し、ロールバック済み。削除が必要 |
| UPDATE_ROLLBACK_COMPLETE | 更新に失敗し、前の状態にロールバック済み |

## 料金

- **無料**（CloudFormation 自体に料金はかからない。作成されたリソースの料金のみ）

## 関連サービス

- **CDK**: CloudFormation テンプレートをプログラミング言語で書くためのフレームワーク
- 全ての AWS リソースが CloudFormation 経由で管理可能
