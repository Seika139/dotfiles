# Dependabot

GitHub が提供する依存関係管理機能。脆弱性の検知、脆弱性修正 PR、通常のバージョン更新 PR を分けて扱う。

## 今回の確認結果

以下は 2026-06-15 に共有された対象リポジトリの確認メモ。

| 機能                        | 状態                                                    |
| --------------------------- | ------------------------------------------------------- |
| Dependabot alerts           | vulnerability alerts endpoint 204、alerts 27 件確認     |
| Dependabot security updates | `dependabot_security_updates=enabled`                   |
| Dependabot version updates  | `.github/dependabot.yml` で npm / uv / actions が daily |

## 機能の違い

| Dependabot の機能                                                                                                                  | 説明                                                                   |
| ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| [Dependabot alerts](https://docs.github.com/ja/code-security/concepts/supply-chain-security/dependabot-alerts)                     | 既知の脆弱性がある依存関係を検知して alert を作成する                  |
| [Dependabot security updates](https://docs.github.com/ja/code-security/concepts/supply-chain-security/dependabot-security-updates) | Dependabot alert に対して、修正バージョンへ更新する PR を自動生成する  |
| [Dependabot version updates](https://docs.github.com/ja/code-security/concepts/supply-chain-security/dependabot-version-updates)   | 脆弱性の有無に関係なく、依存関係を最新化する PR を定期的に自動生成する |

## Dependabot alerts

Dependabot alerts は、依存関係グラフと GitHub Advisory Database などの情報を使い、既知の脆弱性を持つ依存関係を検知する。

今回の確認では、vulnerability alerts endpoint が 204 を返し、alerts 27 件を確認できている。

確認箇所:

- `Security` / `Dependabot` の alerts 画面
- REST API の vulnerability alerts / Dependabot alerts endpoint
- `Security and quality` 配下の alert 一覧

## Dependabot security updates

Dependabot security updates は、Dependabot alert が作成されたときに、脆弱性を修正するための PR を自動で作成する機能。

今回の確認では `dependabot_security_updates=enabled`。

注意点:

- 依存関係グラフと Dependabot alerts が前提。
- PR が作られる対象は、マニフェストやロックファイルで指定された依存関係。
- security updates は、脆弱性修正を目的とした PR。通常の最新版追従とは別に扱う。
- `dependabot.yml` の一部設定は、security updates の PR にも影響する場合がある。

## Dependabot version updates

Dependabot version updates は、`.github/dependabot.yml` に基づき、依存関係を最新に保つための PR を定期作成する機能。

今回の確認では、npm / uv / GitHub Actions が daily 実行対象。

最小構成例:

```yaml
version: 2

updates:
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: daily

  - package-ecosystem: uv
    directory: /
    schedule:
      interval: daily

  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: daily
```

実運用では、PR の件数を抑えるために `groups`、実行時刻、timezone、対象ディレクトリ、ignore 条件を調整する。

### 明示的に version update を実行する方法

1. GitHub で対象のリポジトリを開く。
2. 上部のタブから `Insights` をクリックする。
3. 左サイドメニューの `Dependency graph` を選択する。
4. 上部の `Dependabot` タブをクリックする。
5. 右側にある `Last checked ... ago` の横の `▼` または `Check for updates` ボタンをクリックする。

## Dependency Review との違い

Dependabot は、主に既存依存関係の脆弱性検知と更新 PR の自動作成を扱う。

Dependency Review は、PR の差分に含まれる依存関係変更を確認し、脆弱な依存関係の追加をブロックするための仕組み。Dependabot が有効でも Dependency Review が workflow / ruleset / branch protection で強制されているとは限らない。

## 参考

- [Dependabot alerts](https://docs.github.com/ja/code-security/concepts/supply-chain-security/dependabot-alerts)
- [Dependabot セキュリティ アップデート](https://docs.github.com/ja/code-security/concepts/supply-chain-security/dependabot-security-updates)
- [Dependabot バージョン アップデート](https://docs.github.com/ja/code-security/concepts/supply-chain-security/dependabot-version-updates)
- [Dependabot オプション リファレンス](https://docs.github.com/ja/code-security/dependabot/working-with-dependabot/dependabot-options-reference)
- [Dependency Review](./dependency_review.md)
