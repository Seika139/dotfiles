# GitHub Code Quality

GitHub Code Quality は、PR とリポジトリスキャンでコード品質の問題を検出し、品質指摘・Copilot 自動修正・ルールセットによる標準適用を行う機能。

2026-06-15 時点では public preview。preview 中は Code Quality 自体は課金されないが、Code Quality scan は GitHub Actions 分を消費する。

## 何を見る機能か

Code Quality は、コードベースが信頼性・保守性・効率性の観点で健全かを確認するための機能。

- 不要なコード
- 重複コード
- 複雑すぎる関数
- 可読性の低い実装
- ベストプラクティス違反

などを検出し、PR 上で品質指摘や品質スコアを提供する。

主に次の用途で使われる。

- PR に品質問題をコメントする。
- リポジトリの品質スコアや注意すべき領域を確認する。
- Code Quality のルールセットで品質基準を満たさない PR をブロックする。
- コードカバレッジをアップロードし、PR 上でテストされていない変更を把握する。

## Code Quality の検出結果を見る方法

GitHub 上で `Security and quality` タブを開き、`Code Quality` を選択すると、品質スキャンの結果を確認できる。
2026-06-15 時点では `Standard findings` と `AI findings` の2項目が表示される。

## CodeQL quality scan

Code Quality は CodeQL を使ってルールベースの品質分析を実行する。

サポートされる代表的な言語:

- C#
- Go
- Java
- JavaScript
- Python
- Ruby
- TypeScript

リポジトリで Code Quality を有効にすると、既定ブランチ向けの PR や既定ブランチ自体に対する CodeQL 品質スキャンが表示される。GitHub 公式ドキュメントでは、この分析は GitHub Actions 分を消費し、リポジトリの Code Quality タブに dynamic workflow として表示されると説明されている。

## Code Security との違い

Code Quality と Code Security は混同しやすい。

| 観点            | Code Quality                   | Code Security                   |
| --------------- | ------------------------------ | ------------------------------- |
| 主目的          | 品質・保守性・信頼性           | 脆弱性・エラーの検出            |
| 主な表示先      | Code Quality タブ、PR コメント | code scanning alerts            |
| CodeQL との関係 | 品質分析で利用                 | code scanning 分析で利用        |
| 今回の状態      | dynamic scan 成功              | `code_security.status=disabled` |

Code Quality が成功していても、Code Security の CodeQL alerts API が使えることは意味しない。

## 運用メモ

- PR を品質基準でブロックしたい場合は、Code Quality の ruleset / threshold を確認する。
- セキュリティ alert として扱いたい場合は、Code Security 側の code scanning を有効化する。
- dynamic scan が落ちた場合は、通常の GitHub Actions workflow と同じく workflow run のログを確認する。

## 参考

- [GitHub のコード品質について](https://docs.github.com/ja/code-security/concepts/about-code-quality)
- [Enabling GitHub Code Quality](https://docs.github.com/en/code-security/how-tos/maintain-quality-code/enable-code-quality)
- [Interpreting the code quality results for your repository](https://docs.github.com/en/code-security/how-tos/maintain-quality-code/interpret-results)
- [Setting code quality thresholds for pull requests](https://docs.github.com/en/code-security/how-tos/maintain-quality-code/set-pr-thresholds)
