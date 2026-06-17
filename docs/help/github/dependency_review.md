# GitHub Dependency Review

Dependency Review は、pull request で依存関係の変更差分を確認し、脆弱な依存関係が追加されるのを防ぐための機能。

## 今回の確認結果

以下は 2026-06-15 に共有された対象リポジトリの確認メモ。

| 項目                       | 状態                                           |
| -------------------------- | ---------------------------------------------- |
| Dependency Review workflow | 設定なし                                       |
| ruleset                    | Dependency Review を必須にする設定なし         |
| branch protection          | Dependency Review を必須チェックにする設定なし |

## 何を検出するか

Dependency Review は、PR の base commit と head commit の間で依存関係がどう変わったかを比較する。

確認できる内容:

- 追加・更新・削除された依存関係
- 追加された依存関係に既知の脆弱性があるか
- ライセンスや severity 条件に基づくブロック

Dependabot alerts は既存の依存関係に対する脆弱性通知で、Dependency Review は PR で新しく混入する依存関係リスクの確認に使う。

## Enforce する方法

Dependency Review を PR の防波堤として使う場合は、dependency-review-action を workflow として追加し、そのチェックを ruleset または branch protection で必須にする。

例:

```yaml
name: Dependency Review

on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: read

jobs:
  dependency-review:
    runs-on: ubuntu-latest
    steps:
      - name: Dependency Review
        uses: actions/dependency-review-action@v4
```

既定では、脆弱性のあるパッケージが検出されると dependency-review-action のチェックは失敗する。ruleset / branch protection でこのチェックを必須にすると、条件を満たさない PR のマージをブロックできる。

## 注意点

- 依存関係グラフが前提になる。
- private repository では、利用条件として Code Security または GitHub Advanced Security が関係する場合がある。
- workflow を追加しただけではマージブロックにはならない。必須チェックとして ruleset / branch protection に登録する必要がある。
- Dependabot security updates とは別機能なので、Dependabot が有効でも Dependency Review が有効とは限らない。

## 参考

- [依存関係の確認](https://docs.github.com/ja/code-security/concepts/supply-chain-security/dependency-review)
- [Enforcing dependency review across an organization](https://docs.github.com/ja/code-security/how-tos/secure-at-scale/configure-organization-security/configure-specific-tools/enforce-dependency-review)
- [Dependency Review Action](https://github.com/actions/dependency-review-action)
