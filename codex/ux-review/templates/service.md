# Service Profile — {{SERVICE_NAME}}

`/ux-review` コマンドが読み取るサービス情報。このファイルだけ書き換えれば
同じ仕組みがどのサービスでも動く。

## 基本情報

- **サービス名**:（例: crash-game, campaign-site, ...）
- **環境**:（例: stg, dev, ...）
- **base_url**: <https://example.com>
- **login_url**: <https://example.com/login>

## ログイン手順

ペルソナが一般ユーザーとしてログインできる手順を書く:

1. `login_url` を開く
2. どの要素を操作するか（例:「表示名」欄にユーザー名を入力して Enter）
3. SSO が必要な場合はその手順。不要な場合は「SSO は使わない」と明記

**ユーザー名テンプレート**: `ux-review-{persona}-{date}`

## 副作用ポリシー

- 環境（stg / 本番）に応じて副作用の許容範囲を明記
- 副作用を残す場合の命名規約を定める:
  - **プレフィックス**: `[ux-review/{persona}/{date}]`
- 他ユーザーのコンテンツは編集・削除しない

## レート制約

- 重い API（LLM 呼び出し、検索等）の呼び出し上限を明記
- 「1 セッション N 回以内」のような具体数値が望ましい

## 禁止事項

- URL 直打ち / DevTools の利用（ペルソナは一般ユーザー想定）
- 本番環境へのアクセス（stg 限定にしたい場合）
- 他ユーザーのコンテンツの編集・削除

## エンジン

- 初期は Playwright MCP（`mcp__playwright__*` ツール）
- Regression が必要になったら CDP attach / Playwright CLI を検討

## 参考ドキュメント

- 関連 Issue:
- 関連 MTG:
- システム構成図:
