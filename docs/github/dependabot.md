# Dependabot

GitHub が提供する機能で、リポジトリ内の依存関係を自動的に更新してくれる。

| Dependabot の機能                                                                                                                                | 説明                                                                                                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| [Dependabot alerts](https://docs.github.com/ja/code-security/dependabot/dependabot-alerts/about-dependabot-alerts)                               | パッケージバージョンの脆弱性が検知されたとき、メールなどでアラート通知をする                                           |
| [Dependabot security updates](https://docs.github.com/ja/code-security/dependabot/dependabot-security-updates/about-dependabot-security-updates) | パッケージバージョンの脆弱性が検知されたとき、その問題を解決するバージョンにアップデートするための PR を自動で生成する |
| [Dependabot version updates](https://docs.github.com/ja/code-security/dependabot/dependabot-version-updates/about-dependabot-version-updates)    | パッケージバージョンを最新にするための PR を自動で生成する                                                             |

## Dependabot alerts

導入したいリポジトリの `Settings > Advanced security > Dependabot alerts` から有効化できる。

## Dependabot security updates

導入したいリポジトリの `Settings > Advanced security > Dependabot security updates` から有効化できる。

## Dependabot version updates

導入したいリポジトリの `Settings > Advanced security > Dependabot version updates` から有効化したうえで、 `.github/dependabot.yml` をリポジトリに追加する。

### 明示的に version update を実行する方法

1. GitHub で対象のリポジトリを開く
2. 上部のタブから Insights をクリック
3. 左サイドメニューの Dependency graph を選択
4. 上部の Dependabot タブをクリック
5. 右側にある `Last checked ... ago` の横の `▼` または `Check for updates` ボタンをクリック

## 参考

- [Dependabot まとめ #GitHub - Qiita](https://qiita.com/WisteriaWave/items/b37be9c3ebf1de37da0f)
