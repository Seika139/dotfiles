# AGENTS.md

このファイルは AI エージェント (Claude Code / Codex / Gemini CLI 等) 向けの指示書です。

## 基本方針

- コミュニケーションは日本語で。
- 不明点があれば作業前に質問する。
- 実装より先にテストで期待を固める（必要に応じて）。

## プロジェクト情報

- プロジェクト名: {{project_name}}
- GitHub: {{github_user}}/{{project_name}}

## 開発環境

依存関係は `mise.toml` に集約しています。

```bash
mise install         # ツール (python, uv, node, pnpm, ...) を一括で入れる
mise tasks           # 使えるタスク一覧
```

## コミットルール

- 1 つの論理的な変更単位ごとにコミットする
- テストの追加とプロダクションコードの変更は別コミットにする
- リファクタリングと機能追加を同じコミットに混ぜない
- コミットメッセージは日本語で書く (Conventional Commits プレフィックス・絵文字は使わない)

## コードスタイル

各言語は `mise run <lang>:lint` / `mise run <lang>:format` (または `<lang>:fix`) でチェック・自動修正できます。コミット前に実行してください。

## 制限事項

- 機密情報をソースコードにハードコードしない
- 最小権限の原則を守る
